# backend/app/text_to_Sql.py
"""
Text-to-SQL Agent for ClinData Explorer.
Uses Google Gemini to convert natural language to SQL.
"""

import re
import json
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ── Table catalog (keep the full list you already have) ──
TABLE_CATALOG = """
Available Tables (MIMIC-IV Demo):
... (your full catalog) ...
"""

class TextToSQLAgent:
    def __init__(self, db_uri: str, api_key: str):
        if not api_key:
            raise ValueError("Google API Key is missing. Check your .env file.")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            google_api_key=api_key
        )

        try:
            self.db = SQLDatabase.from_uri(db_uri)
            self.schema_info = self.db.get_table_info()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to database or fetch schema: {e}")

        system_prompt = f"""
You are an expert SQLite data engineer for a clinical research tool called ClinData Explorer.
This tool is for RESEARCH AND EDUCATION ONLY. It must never provide clinical advice, diagnosis,
treatment recommendations, triage guidance, or patient-specific medical decisions.

{TABLE_CATALOG}

Full Schema:
{{schema}}

YOUR TASK:
Convert the user's natural-language research question into a valid SQLite SELECT query.

OUTPUT FORMAT — You MUST follow this EXACT format. Do not deviate:

SQL_QUERY:
<your SQL SELECT query here>

INCLUSION_CRITERIA:
<JSON array of inclusion conditions, e.g. [{{{{"field": "admission_type", "operator": "=", "value": "URGENT", "table": "admissions"}}}}] >

EXCLUSION_CRITERIA:
<JSON array of exclusion conditions, e.g. [{{{{"field": "hospital_expire_flag", "operator": "=", "value": 1, "table": "admissions"}}}}] >

LOGIC:
<1-3 sentence plain English explanation of what this query does and why>

LIMITATIONS:
<JSON array of limitations/caveats, e.g. ["chartevents has no item dictionary (d_items not loaded)", "Results limited to MIMIC-IV Demo subset of 100 patients"]>

RULES:
1. ONLY use SELECT statements. NEVER use DROP, DELETE, UPDATE, INSERT, or DDL.
2. ONLY use tables and columns listed above. Do NOT hallucinate columns.
3. Always use square brackets for table/column names with spaces.
4. Add LIMIT 500 to any query that could return very large results (chartevents, labevents).
5. If the user asks for clinical advice, diagnosis, or patient identification, respond:
   SQL_QUERY: -- REFUSED
   LOGIC: This question asks for clinical advice/diagnosis which is outside the scope of this research tool.
   INCLUSION_CRITERIA: []
   EXCLUSION_CRITERIA: []
   LIMITATIONS: ["Clinical advice, diagnosis, and treatment recommendations are not supported."]
6. chartevents has NO item name dictionary loaded (d_items not in DB). Use itemid numbers or
   filter by valueuom to identify measurement types.
7. For lab item names, always JOIN labevents with d_labitems on itemid.
"""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}")
        ])

        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate_sql(self, user_question: str) -> dict:
        try:
            raw_response = self.chain.invoke({
                "schema": self.schema_info,
                "question": user_question
            })
            return self._parse_response(raw_response, user_question)
        except Exception as e:
            return {"error": f"Failed to generate SQL: {str(e)}"}

    def _parse_response(self, raw: str, question: str) -> dict:
        # ... (keep the same parsing logic you already have) ...
        # I'll include it below for completeness:

        def extract_block(text: str, start_tag: str, end_tags: list) -> str:
            if start_tag not in text:
                return ""
            after = text.split(start_tag, 1)[1]
            for tag in end_tags:
                if tag in after:
                    after = after.split(tag, 1)[0]
            return after.strip()

        sql_raw = extract_block(raw, "SQL_QUERY:", ["INCLUSION_CRITERIA:", "EXCLUSION_CRITERIA:", "LOGIC:", "LIMITATIONS:"])
        logic = extract_block(raw, "LOGIC:", ["LIMITATIONS:", "SQL_QUERY:", "INCLUSION_CRITERIA:"])
        limitations_raw = extract_block(raw, "LIMITATIONS:", ["SQL_QUERY:", "LOGIC:", "INCLUSION_CRITERIA:"])
        inclusion_raw = extract_block(raw, "INCLUSION_CRITERIA:", ["EXCLUSION_CRITERIA:", "LOGIC:", "LIMITATIONS:"])
        exclusion_raw = extract_block(raw, "EXCLUSION_CRITERIA:", ["LOGIC:", "LIMITATIONS:", "SQL_QUERY:"])

        sql_query = re.sub(r"^```sql\s*", "", sql_raw, flags=re.IGNORECASE)
        sql_query = re.sub(r"\s*```$", "", sql_query)
        sql_query = sql_query.strip()

        if sql_query and not sql_query.upper().startswith("SELECT") and not sql_query.startswith("--"):
            return {
                "error": "AI generated a non-SELECT query. Blocked for safety.",
                "raw_response": raw,
            }

        def safe_json(s: str) -> list:
            try:
                s = s.strip()
                if not s or s == "[]":
                    return []
                s = re.sub(r"^```json\s*", "", s, flags=re.IGNORECASE)
                s = re.sub(r"\s*```$", "", s)
                return json.loads(s)
            except Exception:
                return [s] if s else []

        inclusion = safe_json(inclusion_raw)
        exclusion = safe_json(exclusion_raw)
        limitations = safe_json(limitations_raw)

        base_limitations = [
            "Results are from the MIMIC-IV Demo dataset (100 patients). Not representative of the full MIMIC-IV.",
            "This tool is for research and educational purposes only.",
        ]
        for lim in base_limitations:
            if lim not in limitations:
                limitations.append(lim)

        return {
            "user_question": question,
            "sql_query": sql_query,
            "inclusion_criteria": inclusion if isinstance(inclusion, list) else [],
            "exclusion_criteria": exclusion if isinstance(exclusion, list) else [],
            "logic": logic,
            "limitations": limitations,
            "raw_response": raw,
            "error": None,
        }

# ── Local Testing ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from config import GOOGLE_API_KEY, DB_URI
    print("[INFO] Initializing Text-to-SQL Agent with Gemini...")
    agent = TextToSQLAgent(db_uri=DB_URI, api_key=GOOGLE_API_KEY)
    print("[INFO] Agent Ready. Type 'exit' to quit.\n")

    while True:
        question = input("Enter your research question: ")
        if question.lower() == "exit":
            break
        result = agent.generate_sql(question)
        if result.get("error"):
            print(f"\n❌ ERROR: {result['error']}")
        else:
            print("\n" + "=" * 60)
            print("✅ SQL QUERY:\n", result["sql_query"])
            print("\n📋 INCLUSION CRITERIA:\n", result["inclusion_criteria"])
            print("\n🚫 EXCLUSION CRITERIA:\n", result["exclusion_criteria"])
            print("\n💡 LOGIC:\n", result["logic"])
            print("\n⚠️ LIMITATIONS:")
            for lim in result["limitations"]:
                print(f"  - {lim}")
            print("=" * 60)