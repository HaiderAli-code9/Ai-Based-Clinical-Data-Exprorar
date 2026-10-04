# backend/app/summarizer.py
import json
import re
from typing import Any, Dict, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

AI_UNAVAILABLE_MESSAGE = (
    "AI explanation is currently unavailable. The computed results and "
    "data-quality analysis are still available."
)


class Summarizer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.llm = None
        if api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.3,
                google_api_key=api_key,
            )
            self.prompt = ChatPromptTemplate.from_messages([
                (
                    "system",
                    """You are a medical data researcher. Return ONLY valid JSON with:
{
  "key_findings": ["finding 1", "finding 2"],
  "limitations": ["limitation 1"],
  "uncertainty": ["uncertainty 1"]
}
Rules: no diagnosis, no treatment advice. Keep arrays concise (0-5 items).
Do NOT include a summary – we will generate it separately."""
                ),
                (
                    "human",
                    """User Question: {question}
Generated SQL: {sql}
Query Logic: {logic}
Cohort Stats: {stats}
Data Quality Issues: {quality_flags}"""
                ),
            ])
            self.chain = self.prompt | self.llm | StrOutputParser()

    @staticmethod
    def _empty_response(message: str = AI_UNAVAILABLE_MESSAGE) -> Dict[str, Any]:
        return {
            "summary": message,
            "key_findings": [],
            "limitations": [],
            "uncertainty": [],
            "available": False,
        }

    @staticmethod
    def _parse_json_response(raw: str) -> Dict[str, Any]:
        cleaned = raw.strip()
        cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON from Gemini")
        if not isinstance(data, dict):
            raise ValueError("AI response was not a JSON object")
        return {
            "key_findings": [str(x) for x in (data.get("key_findings") or []) if str(x).strip()],
            "limitations": [str(x) for x in (data.get("limitations") or []) if str(x).strip()],
            "uncertainty": [str(x) for x in (data.get("uncertainty") or []) if str(x).strip()],
        }

    def generate_summary(
        self,
        question: str,
        sql: str,
        logic: str,
        stats: dict,
        quality_flags: list,
    ) -> Dict[str, Any]:
        # Always build the summary from actual stats
        row_count = stats.get('row_count', 0)
        col_count = len(stats.get('columns', []))
        flag_count = len(quality_flags)

        summary_text = (
            f"Your query returned {row_count} records with {col_count} columns. "
            f"There are {flag_count} data quality flags detected."
        )

        # Try to get additional insights from Gemini (optional)
        key_findings = [f"Retrieved {row_count} records", f"{flag_count} quality flags found"]
        limitations = [
            "Results are from the MIMIC-IV Demo dataset (100 patients).",
            "This tool is for research and educational purposes only."
        ]
        uncertainty = []

        if self.llm and self.api_key:
            try:
                print("[Summarizer] Calling Gemini for additional insights...")
                raw = self.chain.invoke({
                    "question": question,
                    "sql": sql,
                    "logic": logic,
                    "stats": stats,
                    "quality_flags": quality_flags,
                })
                parsed = self._parse_json_response(raw)
                key_findings = parsed.get("key_findings", key_findings)
                limitations = parsed.get("limitations", limitations)
                uncertainty = parsed.get("uncertainty", uncertainty)
            except Exception as e:
                print(f"[Summarizer] Gemini error (ignored): {e}")

        return {
            "summary": summary_text,
            "key_findings": key_findings,
            "limitations": limitations,
            "uncertainty": uncertainty,
            "available": True,
        }