# backend/app/app.py
"""
ClinData Explorer — FastAPI Backend
Track 2: Cohort & Data Quality Explorer | AI for Smarter Patient Care

Endpoints:
  POST /api/chat       — NL → SQL → DB → DQ → Provenance → AI Summary
  GET  /api/insights   — Full dataset-level analysis (independent of user query)
  GET  /api/schema     — Database schema for frontend reference
  GET  /api/rules      — All quality rule definitions
  GET  /api/health     — Health check
"""

import os
import time
from typing import Any, List, Optional, Dict
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from config import DB_PATH, DB_URI, GOOGLE_API_KEY
from text_to_Sql import TextToSQLAgent
from database_search import DatabaseManager
from data_quality import DataQualityAnalyzer
from summarizer import Summarizer, AI_UNAVAILABLE_MESSAGE
from dataset_insights import DatasetInsightsService
from quality_rules import rules_registry
from criteria_formatter import format_criteria_human_readable
from sql_utils import extract_source_tables

load_dotenv()

app = FastAPI(
    title="ClinData Explorer API",
    description="AI-Powered Clinical Cohort and Data Quality Explorer — MIMIC-IV Demo",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Component Initialization ──────────────────────────────────────────────────
sql_agent = TextToSQLAgent(db_uri=DB_URI, api_key=GOOGLE_API_KEY)
db_manager = DatabaseManager(db_path=DB_PATH)
summarizer = Summarizer(api_key=GOOGLE_API_KEY)
insights_service = DatasetInsightsService(db_path=DB_PATH)

# ── Pydantic Models ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: Optional[str] = None
    query: Optional[str] = None

class ProvenanceChain(BaseModel):
    source_table: str
    source_field: str
    record_id: str
    subject_id: str
    timestamp: str

class ProvenanceItem(BaseModel):
    finding_type: str
    provenance_chain: ProvenanceChain
    rule: dict
    original_value: str
    transformation_applied: str
    provenance_available: bool
    provenance_note: str

class DQSummary(BaseModel):
    total_row_findings: int
    total_unit_variation_findings: int
    total_icd_findings: int
    total_findings: int

class DataQualityReport(BaseModel):
    row_level_findings: List[dict]
    unit_variations: List[dict]
    icd_findings: List[dict]
    provenance: List[dict]
    summary: DQSummary

class CohortStats(BaseModel):
    row_count: int
    distinct_patients: Optional[int] = None  # NEW: added for clarity
    columns: List[str]
    sample: List[dict]

class AIExplanation(BaseModel):
    summary: str
    key_findings: List[str] = []
    limitations: List[str] = []
    uncertainty: List[str] = []
    available: bool = True

class ChatResponse(BaseModel):
    # Query interpretation
    query: str
    user_question: str
    sql_query: str
    logic: str
    explanation: str
    summary: str
    ai_explanation: AIExplanation
    inclusion_criteria: List[Any]
    exclusion_criteria: List[Any]
    limitations: List[str]

    # Results
    results: List[dict]
    total_rows: int
    execution_time_ms: int
    cohort_stats: CohortStats

    # Data quality
    data_quality: DataQualityReport
    data_quality_report: dict
    provenance: List[dict]
    source_tables: List[str]

    # Meta
    error: Optional[str] = None
    source_label: str = "SOURCE DATA"
    result_label: str = "COMPUTED RESULTS"
    ai_label: str = "AI-GENERATED EXPLANATION"

# ── POST /api/chat ─────────────────────────────────────────────────────────────
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main analysis pipeline:
    NL Query → SQL Generation → DB Execution → DQ Analysis → AI Summary
    """
    start_time = time.time()
    user_prompt = (request.question or request.query or "").strip()
    if not user_prompt:
        raise HTTPException(status_code=400, detail="Query string ('question' or 'query') is required.")

    try:
        # Step 1: Natural Language → SQL + structured criteria
        sql_result = sql_agent.generate_sql(user_prompt)

        if sql_result.get("error"):
            raise HTTPException(status_code=400, detail=sql_result["error"])

        sql_query = sql_result["sql_query"]
        logic = sql_result["logic"]
        raw_inclusion = sql_result.get("inclusion_criteria", [])
        raw_exclusion = sql_result.get("exclusion_criteria", [])
        limitations = sql_result.get("limitations", [])

        inclusion_criteria = format_criteria_human_readable(raw_inclusion, kind="INCLUDE")
        exclusion_criteria = format_criteria_human_readable(raw_exclusion, kind="EXCLUDE")
        source_tables = extract_source_tables(sql_query)

        # Handle refused queries (clinical advice refusals)
        if sql_query.startswith("--"):
            exec_ms = int((time.time() - start_time) * 1000)
            empty_dq = DataQualityReport(
                row_level_findings=[], unit_variations=[], icd_findings=[],
                provenance=[], summary=DQSummary(
                    total_row_findings=0, total_unit_variation_findings=0,
                    total_icd_findings=0, total_findings=0,
                )
            )
            empty_ai = AIExplanation(
                summary=logic or AI_UNAVAILABLE_MESSAGE,
                key_findings=[],
                limitations=limitations,
                uncertainty=[],
                available=False,
            )
            return ChatResponse(
                query=user_prompt,
                user_question=user_prompt,
                sql_query=sql_query,
                logic=logic,
                explanation=logic,
                summary=logic,
                ai_explanation=empty_ai,
                inclusion_criteria=[],
                exclusion_criteria=[],
                limitations=limitations,
                results=[],
                total_rows=0,
                execution_time_ms=exec_ms,
                cohort_stats=CohortStats(row_count=0, distinct_patients=0, columns=[], sample=[]),
                data_quality=empty_dq,
                data_quality_report={
                    "summary": {
                        "total_findings": 0, "errors": 0, "warnings": 0, "info": 0,
                        "total_row_findings": 0, "total_dataset_findings": 0
                    },
                    "row_findings": [],
                    "dataset_findings": [],
                    "provenance": []
                },
                provenance=[],
                source_tables=source_tables,
                error="Query refused: outside research scope.",
            )

        # Step 2: Execute SQL against database
        db_result = db_manager.execute_query(sql_query)
        if db_result["error"]:
            raise HTTPException(status_code=400, detail=db_result["error"])

        df = db_result["data"]
        row_count = db_result["row_count"]

        # Step 3: Query-level Data Quality Analysis
        dq_analyzer = DataQualityAnalyzer(df=df, source_table="Retrieved Cohort")
        dq_report = dq_analyzer.run_all_checks()

        # Step 4: Build cohort stats & sample results
        sample_records = df.head(100).to_dict(orient="records") if not df.empty else []
        # Compute distinct patients
        distinct_patients = df['subject_id'].nunique() if 'subject_id' in df.columns else row_count
        stats = CohortStats(
            row_count=row_count,
            distinct_patients=distinct_patients,
            columns=list(df.columns) if not df.empty else [],
            sample=sample_records,
        )

        # Step 5: Build structured DQ report & frontend data quality report
        dq_summary_data = dq_report.get("summary", {})
        data_quality = DataQualityReport(
            row_level_findings=dq_report.get("row_level_findings", []),
            unit_variations=dq_report.get("unit_variations", []),
            icd_findings=dq_report.get("icd_findings", []),
            provenance=dq_report.get("provenance", []),
            summary=DQSummary(
                total_row_findings=dq_summary_data.get("total_row_findings", 0),
                total_unit_variation_findings=dq_summary_data.get("total_unit_variation_findings", 0),
                total_icd_findings=dq_summary_data.get("total_icd_findings", 0),
                total_findings=dq_summary_data.get("total_findings", 0),
            ),
        )

        # Aggregate findings for frontend components
        row_findings = []
        findings_map = {}
        for item in dq_report.get("row_level_findings", []):
            rid = item.get("Rule ID", "DQ-001")
            if rid not in findings_map:
                findings_map[rid] = {
                    "rule_id": rid,
                    "rule_name": item.get("Rule Applied", rid),
                    "severity": item.get("Severity", "WARNING"),
                    "description": f"Flagged {item.get('Issue Type', 'Quality Issue')} on column '{item.get('Column Affected', 'Unknown')}'.",
                    "count": 0,
                    "impact_summary": item.get("Action Taken", "Review flagged records."),
                }
            findings_map[rid]["count"] += 1
        row_findings = list(findings_map.values())

        dataset_findings = []
        for uv in dq_report.get("unit_variations", []):
            dataset_findings.append({
                "rule_id": uv.get("Rule ID", "DQ-010"),
                "rule_name": uv.get("Rule Applied", "Unit Variation Check"),
                "severity": uv.get("Severity", "WARNING"),
                "description": f"Item ID {uv.get('itemid')} has {uv.get('Distinct Units')} distinct measurement units.",
                "count": 1,
                "impact_summary": uv.get("Action Taken", "Standardize units before statistical analysis."),
            })
        for icd in dq_report.get("icd_findings", []):
            dataset_findings.append({
                "rule_id": icd.get("Rule ID", "DQ-012"),
                "rule_name": icd.get("Rule Applied", "Mixed ICD Version Coding"),
                "severity": icd.get("Severity", "WARNING"),
                "description": f"Admission {icd.get('hadm_id')} contains mixed ICD versions: {icd.get('ICD Versions Found')}.",
                "count": 1,
                "impact_summary": icd.get("Action Taken", "Review coding history."),
            })

        all_findings = row_findings + dataset_findings
        err_cnt = sum(f["count"] for f in all_findings if f["severity"] == "ERROR")
        warn_cnt = sum(f["count"] for f in all_findings if f["severity"] == "WARNING")
        info_cnt = sum(f["count"] for f in all_findings if f["severity"] == "INFO")

        frontend_dq_report = {
            "summary": {
                "total_findings": sum(f["count"] for f in all_findings),
                "errors": err_cnt,
                "warnings": warn_cnt,
                "info": info_cnt,
                "total_row_findings": len(dq_report.get("row_level_findings", [])),
                "total_dataset_findings": len(dataset_findings),
            },
            "row_findings": row_findings,
            "dataset_findings": dataset_findings,
            "provenance": dq_report.get("provenance", []),
        }

        # Step 6: AI Summary – pass ALL quality flags (no slicing)
        all_quality_flags = dq_report.get("row_level_findings", [])
        ai_result = summarizer.generate_summary(
            question=user_prompt,
            sql=sql_query,
            logic=logic,
            stats=stats.model_dump(),  # includes row_count and distinct_patients
            quality_flags=all_quality_flags,
        )
        ai_explanation = AIExplanation(
            summary=ai_result.get("summary", AI_UNAVAILABLE_MESSAGE),
            key_findings=ai_result.get("key_findings", []),
            limitations=ai_result.get("limitations", []),
            uncertainty=ai_result.get("uncertainty", []),
            available=ai_result.get("available", False),
        )
        explanation_text = ai_explanation.summary

        exec_ms = int((time.time() - start_time) * 1000)

        return ChatResponse(
            query=user_prompt,
            user_question=user_prompt,
            sql_query=sql_query,
            logic=logic,
            explanation=explanation_text,
            summary=explanation_text,
            ai_explanation=ai_explanation,
            inclusion_criteria=inclusion_criteria,
            exclusion_criteria=exclusion_criteria,
            limitations=limitations,
            results=sample_records,
            total_rows=row_count,
            execution_time_ms=exec_ms,
            cohort_stats=stats,
            data_quality=data_quality,
            data_quality_report=frontend_dq_report,
            provenance=[],
            source_tables=source_tables,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the query.")

# ── GET /api/insights ──────────────────────────────────────────────────────────
@app.get("/api/insights")
async def get_insights():
    try:
        insights = insights_service.get_full_insights()
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insights analysis failed: {str(e)}")

# ── GET /api/schema ────────────────────────────────────────────────────────────
@app.get("/api/schema")
async def get_schema():
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [t[0] for t in cursor.fetchall()]

        schema = {}
        for tname in tables:
            cursor.execute(f"PRAGMA table_info({tname})")
            cols = cursor.fetchall()
            cursor.execute(f"SELECT COUNT(*) FROM [{tname}]")
            row_count = cursor.fetchone()[0]
            schema[tname] = {
                "row_count": row_count,
                "columns": [{"name": c[1], "type": c[2] or "TEXT"} for c in cols],
            }

        conn.close()
        return {"schema": schema, "total_tables": len(tables)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── GET /api/rules ─────────────────────────────────────────────────────────────
@app.get("/api/rules")
async def get_rules():
    return {
        "total_rules": len(rules_registry.all_rules()),
        "rules": rules_registry.to_dict_list(),
    }

# ── GET /api/health ────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "ClinData Explorer API", "version": "2.0"}

# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)