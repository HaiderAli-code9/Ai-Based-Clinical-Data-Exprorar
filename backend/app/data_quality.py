# backend/app/data_quality.py
"""
Data Quality Analyzer for ClinData Explorer — Track 2.

STRICT RULES:
  - NEVER modifies or deletes source data.
  - Only flags issues for researcher review.
  - Every finding is backed by a named rule from quality_rules.py.
  - Every finding has provenance via provenance.py.

Two levels of analysis:
  A. query_level  — runs on the DataFrame returned by a user query
  B. dataset_level — runs on the full database (used by /api/insights)
"""

import sqlite3
import pandas as pd
from typing import Optional, List, Dict, Any

from quality_rules import rules_registry
from provenance import ProvenanceTracer
from table_catalog import TABLE_PURPOSES


class DataQualityAnalyzer:
    """
    Query-level Data Quality Analyzer.
    Analyzes a retrieved DataFrame for DQ issues relevant to the query context.
    """

    def __init__(self, df: pd.DataFrame, source_table: str = "Retrieved Cohort"):
        # STRICT: Work on a copy. Never touch original data.
        self.df_original = df.copy()
        self.source_table = source_table
        self.findings: List[Dict[str, Any]] = []
        self.tracer = ProvenanceTracer(source_table=source_table)

    def _add_finding(
        self,
        issue_type: str,
        column: str,
        subject_id: Any,
        original_value: Any,
        rule_id: str,
        action: str,
    ):
        rule = rules_registry.get_rule(rule_id)
        self.findings.append({
            "Source Table": self.source_table,
            "Issue Type": issue_type,
            "Column Affected": column,
            "Subject ID (Provenance)": str(subject_id),
            "Original Value": str(original_value),
            "Rule ID": rule_id,
            "Rule Applied": rule.name if rule else rule_id,
            "Severity": rule.severity if rule else "WARNING",
            "Action Taken": action,
            "Is Clinical Finding?": "No (Data Quality Flag)",
        })

    # ── Check 1: Missing Values ───────────────────────────────────────────────
    def check_missing_values(self):
        """Flags NULL/NaN values in each column of the retrieved cohort."""
        if self.df_original.empty:
            return

        rule = rules_registry.get_rule("DQ-001")
        for col in self.df_original.columns:
            missing_rows = self.df_original[self.df_original[col].isna()]
            for _, row in missing_rows.iterrows():
                subject_id = row.get("subject_id", "Unknown")
                self._add_finding(
                    issue_type="Missing Value",
                    column=col,
                    subject_id=subject_id,
                    original_value="NULL",
                    rule_id="DQ-001",
                    action=rule.action,
                )
                self.tracer.trace_missing_value(row, col)

    # ── Check 2: Duplicates ───────────────────────────────────────────────────
    def check_duplicates(self):
        """Flags exact duplicate rows in the retrieved cohort."""
        if self.df_original.empty:
            return

        rule = rules_registry.get_rule("DQ-002")
        duplicates = self.df_original[self.df_original.duplicated(keep=False)]
        for _, row in duplicates.iterrows():
            subject_id = row.get("subject_id", "Unknown")
            self._add_finding(
                issue_type="Duplicate Record",
                column="Entire Row",
                subject_id=subject_id,
                original_value=str(row.to_dict()),
                rule_id="DQ-002",
                action=rule.action,
            )
            self.tracer.trace_duplicate(row)

    # ── Check 3: Temporal Misalignment ───────────────────────────────────────
    def check_temporal_misalignment(self):
        """Checks all known temporal column pairs for impossible timelines."""
        if self.df_original.empty:
            return

        temporal_pairs = [
            ("admittime", "dischtime", "DQ-003", "Admission/Discharge Temporal Misalignment"),
            ("intime", "outtime", "DQ-004", "ICU Intime/Outtime Temporal Misalignment"),
            ("starttime", "stoptime", "DQ-005", "Prescription Start/Stop Temporal Misalignment"),
            ("charttime", "storetime", "DQ-006", "Chart Event Storetime Before Charttime"),
        ]

        df = self.df_original.copy()
        for start_col, end_col, rule_id, rule_name in temporal_pairs:
            if start_col in df.columns and end_col in df.columns:
                df[start_col] = pd.to_datetime(df[start_col], errors="coerce")
                df[end_col] = pd.to_datetime(df[end_col], errors="coerce")

                # For charttime/storetime use a threshold (>1hr discrepancy is notable)
                if rule_id == "DQ-006":
                    misaligned = df[
                        df[end_col].notna() &
                        df[start_col].notna() &
                        ((df[start_col] - df[end_col]).dt.total_seconds() > 3600)
                    ]
                else:
                    misaligned = df[df[end_col] < df[start_col]]

                rule = rules_registry.get_rule(rule_id)
                for _, row in misaligned.iterrows():
                    self._add_finding(
                        issue_type="Temporal Misalignment",
                        column=f"{start_col} / {end_col}",
                        subject_id=row.get("subject_id", "Unknown"),
                        original_value=f"{start_col}={row[start_col]}, {end_col}={row[end_col]}",
                        rule_id=rule_id,
                        action=rule.action,
                    )
                    self.tracer.trace_temporal_misalignment(row, start_col, end_col, rule_id, rule_name)

    # ── Check 4: Implausible Values ───────────────────────────────────────────
    def check_implausible_values(self):
        """Checks for biologically/physiologically impossible values."""
        if self.df_original.empty:
            return

        # Negative age
        if "anchor_age" in self.df_original.columns:
            rule = rules_registry.get_rule("DQ-007")
            neg_ages = self.df_original[self.df_original["anchor_age"] < 0]
            for _, row in neg_ages.iterrows():
                self._add_finding(
                    issue_type="Implausible Value (Negative Age)",
                    column="anchor_age",
                    subject_id=row.get("subject_id", "Unknown"),
                    original_value=row["anchor_age"],
                    rule_id="DQ-007",
                    action=rule.action,
                )
                self.tracer.trace_implausible_value(row, "anchor_age", row["anchor_age"], "DQ-007", rule.name)

        # Physiologically implausible chartevents values (when valuenum present)
        if "valuenum" in self.df_original.columns and "valueuom" in self.df_original.columns:
            rule = rules_registry.get_rule("DQ-009")
            df = self.df_original.dropna(subset=["valuenum", "valueuom"])

            implausible_checks = [
                (df["valueuom"].str.contains("%", na=False) & (df["valuenum"] > 100), "SpO2/% > 100"),
                (df["valueuom"].str.contains("bpm", na=False) & (df["valuenum"] < 0), "Heart Rate < 0"),
                (df["valueuom"].str.contains("mmHg", na=False) & (df["valuenum"] < 0), "Blood Pressure < 0"),
                (df["valueuom"].str.contains("mmHg", na=False) & (df["valuenum"] > 300), "Blood Pressure > 300"),
            ]

            for mask, description in implausible_checks:
                for _, row in df[mask].iterrows():
                    self._add_finding(
                        issue_type=f"Implausible Value ({description})",
                        column="valuenum",
                        subject_id=row.get("subject_id", "Unknown"),
                        original_value=f"{row['valuenum']} {row['valueuom']}",
                        rule_id="DQ-009",
                        action=rule.action,
                    )
                    self.tracer.trace_implausible_value(row, "valuenum", f"{row['valuenum']} {row['valueuom']}", "DQ-009", rule.name)

    # ── Check 5: Reference Range Outliers ─────────────────────────────────────
    def check_reference_range_outliers(self):
        """Flags lab values outside their documented reference range."""
        needed = {"valuenum", "ref_range_lower", "ref_range_upper"}
        if not needed.issubset(self.df_original.columns):
            return
        if self.df_original.empty:
            return

        rule = rules_registry.get_rule("DQ-008")
        df = self.df_original.dropna(subset=["valuenum", "ref_range_lower", "ref_range_upper"])

        outliers = df[
            (df["valuenum"] < df["ref_range_lower"]) |
            (df["valuenum"] > df["ref_range_upper"])
        ]

        for _, row in outliers.iterrows():
            self._add_finding(
                issue_type="Reference Range Outlier",
                column="valuenum",
                subject_id=row.get("subject_id", "Unknown"),
                original_value=f"value={row['valuenum']}, ref=[{row['ref_range_lower']}, {row['ref_range_upper']}]",
                rule_id="DQ-008",
                action=rule.action,
            )
            self.tracer.trace_ref_range_outlier(row)

    # ── Check 6: Unit Variation ───────────────────────────────────────────────
    def check_unit_variation(self) -> List[Dict[str, Any]]:
        """
        Detects multiple measurement units for the same itemid.
        Returns a list of unit variation findings (separate from row-level findings).
        """
        unit_variations = []
        if "itemid" not in self.df_original.columns or "valueuom" not in self.df_original.columns:
            return unit_variations
        if self.df_original.empty:
            return unit_variations

        rule_id = "DQ-010" if self.source_table in ("labevents", "Retrieved Cohort") else "DQ-011"
        rule = rules_registry.get_rule(rule_id)

        df = self.df_original.dropna(subset=["itemid", "valueuom"])
        df = df[df["valueuom"].str.strip() != ""]

        grouped = df.groupby("itemid")["valueuom"].nunique()
        multi_unit_items = grouped[grouped > 1].index.tolist()

        for itemid in multi_unit_items:
            item_df = df[df["itemid"] == itemid]
            unit_counts = item_df["valueuom"].value_counts().to_dict()
            units_list = list(unit_counts.keys())

            unit_variations.append({
                "Source Table": self.source_table,
                "Issue Type": "Unit Variation",
                "itemid": int(itemid),
                "Distinct Units": len(units_list),
                "Units Found": unit_counts,
                "Rule ID": rule_id,
                "Rule Applied": rule.name,
                "Severity": rule.severity,
                "Action Taken": rule.action,
                "Is Clinical Finding?": "No (Data Quality Flag)",
            })
            self.tracer.trace_unit_variation(itemid, units_list, len(units_list), rule_id, rule.name)

        return unit_variations

    # ── Check 7: ICD Version Mix ──────────────────────────────────────────────
    def check_icd_version_mix(self) -> List[Dict[str, Any]]:
        """Flags hospital admissions with both ICD-9 and ICD-10 codes."""
        icd_findings = []
        if "icd_version" not in self.df_original.columns or "hadm_id" not in self.df_original.columns:
            return icd_findings
        if self.df_original.empty:
            return icd_findings

        rule = rules_registry.get_rule("DQ-012")
        grouped = self.df_original.groupby("hadm_id")["icd_version"].unique()

        for hadm_id, versions in grouped.items():
            if len(versions) > 1:
                icd_findings.append({
                    "Source Table": self.source_table,
                    "Issue Type": "Mixed ICD Version Coding",
                    "hadm_id": int(hadm_id),
                    "ICD Versions Found": [int(v) for v in versions],
                    "Rule ID": "DQ-012",
                    "Rule Applied": rule.name,
                    "Severity": rule.severity,
                    "Action Taken": rule.action,
                    "Is Clinical Finding?": "No (Data Quality Flag)",
                })
                self.tracer.trace_icd_version_mix(hadm_id, [int(v) for v in versions])

        return icd_findings

    # ── Master Run ────────────────────────────────────────────────────────────
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Runs all applicable DQ checks and returns a structured report dict.
        Returns:
            {
              "row_level_findings": [...],   # per-record DQ flags
              "unit_variations": [...],       # aggregate unit variation findings
              "icd_findings": [...],          # ICD version mix findings
              "provenance": [...],            # full provenance chain
              "summary": {...}
            }
        """
        self.findings = []
        self.tracer = ProvenanceTracer(source_table=self.source_table)

        if self.df_original.empty:
            return {
                "row_level_findings": [],
                "unit_variations": [],
                "icd_findings": [],
                "provenance": [],
                "summary": {"total_findings": 0, "note": "No data returned for quality analysis."},
            }

        self.check_missing_values()
        self.check_duplicates()
        self.check_temporal_misalignment()
        self.check_implausible_values()
        self.check_reference_range_outliers()
        unit_variations = self.check_unit_variation()
        icd_findings = self.check_icd_version_mix()

        return {
            "row_level_findings": self.findings,
            "unit_variations": unit_variations,
            "icd_findings": icd_findings,
            "provenance": self.tracer.get_all_provenance(),
            "summary": {
                "total_row_findings": len(self.findings),
                "total_unit_variation_findings": len(unit_variations),
                "total_icd_findings": len(icd_findings),
                "total_findings": len(self.findings) + len(unit_variations) + len(icd_findings),
                "provenance_summary": self.tracer.summary(),
            },
        }


# ── Dataset-Level Analyzer ────────────────────────────────────────────────────

class DatasetLevelAnalyzer:
    """
    Runs DQ analysis on the full database — used by /api/insights.
    Operates directly via SQL for efficiency (avoids loading full tables into RAM).
    chartevents (668K rows) and labevents (107K rows) are queried via aggregation only.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _get_table_data_summary(self, cursor, tname: str) -> Dict[str, Any]:
        """Build a small, real-data summary suitable for the Table Inventory UI."""
        summary: Dict[str, Any] = {"summary_type": "stats", "items": []}

        try:
            if tname == "patients":
                cursor.execute(
                    "SELECT gender, COUNT(*) AS cnt FROM patients GROUP BY gender ORDER BY cnt DESC"
                )
                summary["items"] = [
                    {"label": row[0] or "Unknown", "value": row[1]} for row in cursor.fetchall()
                ]
                summary["chart_label"] = "Gender distribution"
            elif tname == "admissions":
                cursor.execute(
                    "SELECT admission_type, COUNT(*) AS cnt FROM admissions "
                    "GROUP BY admission_type ORDER BY cnt DESC LIMIT 6"
                )
                summary["items"] = [
                    {"label": row[0] or "Unknown", "value": row[1]} for row in cursor.fetchall()
                ]
                summary["chart_label"] = "Admission types"
            elif tname == "icustays":
                cursor.execute(
                    "SELECT first_careunit, COUNT(*) AS cnt FROM icustays "
                    "GROUP BY first_careunit ORDER BY cnt DESC LIMIT 6"
                )
                summary["items"] = [
                    {"label": row[0] or "Unknown", "value": row[1]} for row in cursor.fetchall()
                ]
                summary["chart_label"] = "First care unit distribution"
            elif tname == "labevents":
                cursor.execute(
                    """
                    SELECT COALESCE(d.label, 'Unknown item'), COUNT(*) AS cnt
                    FROM labevents l
                    LEFT JOIN d_labitems d ON l.itemid = d.itemid
                    GROUP BY COALESCE(d.label, 'Unknown item')
                    ORDER BY cnt DESC
                    LIMIT 5
                    """
                )
                summary["items"] = [{"label": row[0], "value": row[1]} for row in cursor.fetchall()]
                summary["chart_label"] = "Top laboratory measurements"
            elif tname == "chartevents":
                cursor.execute(
                    """
                    SELECT COALESCE(valueuom, 'No unit'), COUNT(*) AS cnt
                    FROM chartevents
                    WHERE valueuom IS NOT NULL AND valueuom != ''
                    GROUP BY valueuom
                    ORDER BY cnt DESC
                    LIMIT 5
                    """
                )
                summary["items"] = [{"label": row[0], "value": row[1]} for row in cursor.fetchall()]
                summary["chart_label"] = "Chart measurement units"
            elif tname == "diagnoses_icd":
                cursor.execute(
                    "SELECT icd_version, COUNT(*) AS cnt FROM diagnoses_icd GROUP BY icd_version"
                )
                summary["items"] = [
                    {"label": f"ICD-{row[0]}", "value": row[1]} for row in cursor.fetchall()
                ]
                summary["chart_label"] = "ICD version distribution"
            elif tname == "prescriptions":
                cursor.execute(
                    "SELECT drug, COUNT(*) AS cnt FROM prescriptions "
                    "GROUP BY drug ORDER BY cnt DESC LIMIT 5"
                )
                summary["items"] = [{"label": row[0], "value": row[1]} for row in cursor.fetchall()]
                summary["chart_label"] = "Most prescribed medications"
            elif tname == "transfers":
                cursor.execute(
                    "SELECT eventtype, COUNT(*) AS cnt FROM transfers "
                    "GROUP BY eventtype ORDER BY cnt DESC LIMIT 5"
                )
                summary["items"] = [
                    {"label": row[0] or "Unknown", "value": row[1]} for row in cursor.fetchall()
                ]
                summary["chart_label"] = "Transfer event types"
            elif tname == "d_labitems":
                cursor.execute(
                    "SELECT category, COUNT(*) AS cnt FROM d_labitems "
                    "GROUP BY category ORDER BY cnt DESC LIMIT 5"
                )
                summary["items"] = [
                    {"label": row[0] or "Unknown", "value": row[1]} for row in cursor.fetchall()
                ]
                summary["chart_label"] = "Lab item categories"
            elif tname == "d_icd_diagnoses":
                cursor.execute(
                    "SELECT icd_version, COUNT(*) AS cnt FROM d_icd_diagnoses GROUP BY icd_version"
                )
                summary["items"] = [
                    {"label": f"ICD-{row[0]}", "value": row[1]} for row in cursor.fetchall()
                ]
                summary["chart_label"] = "Dictionary ICD versions"
        except Exception:
            summary["items"] = []

        return summary

    def get_table_inventory(self) -> List[Dict[str, Any]]:
        """Returns table names, row counts, column counts, purpose, and data summaries."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [t[0] for t in cursor.fetchall()]

        inventory = []
        for tname in tables:
            cursor.execute(f"SELECT COUNT(*) FROM [{tname}]")
            row_count = cursor.fetchone()[0]
            cursor.execute(f"PRAGMA table_info({tname})")
            cols = cursor.fetchall()
            col_info = [{"name": c[1], "type": c[2] or "TEXT"} for c in cols]
            inventory.append({
                "table_name": tname,
                "purpose": TABLE_PURPOSES.get(
                    tname,
                    f"Clinical data table `{tname}` in the MIMIC-IV demo database.",
                ),
                "row_count": row_count,
                "column_count": len(cols),
                "columns": col_info,
                "data_summary": self._get_table_data_summary(cursor, tname),
            })

        conn.close()
        return inventory

    def get_quality_flags_summary(self) -> Dict[str, Any]:
        """Aggregate dataset-level quality flag counts for summary cards."""
        missingness = self.get_missingness_report()
        duplicates = self.get_duplicate_report()
        unit_variation = self.get_unit_variation_report()
        coding = self.get_coding_patterns()

        duplicate_flags = 0
        for entry in duplicates:
            dup_val = entry.get("duplicate_rows")
            if isinstance(dup_val, int) and dup_val > 0:
                duplicate_flags += dup_val

        unit_flags = (
            unit_variation.get("labevents_unit_variation", {}).get("items_with_multiple_units", 0)
            + unit_variation.get("chartevents_unit_variation", {}).get("items_with_multiple_units", 0)
        )

        mixed_icd = coding.get("admissions_with_mixed_icd_versions", 0)
        missing_flags = len(missingness)
        total_flags = missing_flags + duplicate_flags + unit_flags + mixed_icd

        return {
            "total_flags": total_flags,
            "missingness_flags": missing_flags,
            "duplicate_flags": duplicate_flags,
            "unit_variation_flags": unit_flags,
            "coding_flags": mixed_icd,
            "severity_breakdown": {
                "HIGH": sum(1 for m in missingness if m.get("severity") == "HIGH"),
                "MEDIUM": sum(1 for m in missingness if m.get("severity") == "MEDIUM"),
                "LOW": sum(1 for m in missingness if m.get("severity") == "LOW"),
            },
        }

    def get_missingness_report(self) -> List[Dict[str, Any]]:
        """Returns NULL percentage per column for each table."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [t[0] for t in cursor.fetchall()]

        report = []
        for tname in tables:
            cursor.execute(f"SELECT COUNT(*) FROM [{tname}]")
            total = cursor.fetchone()[0]
            if total == 0:
                continue

            cursor.execute(f"PRAGMA table_info({tname})")
            cols = [c[1] for c in cursor.fetchall()]

            for col in cols:
                cursor.execute(f"SELECT COUNT(*) FROM [{tname}] WHERE [{col}] IS NULL")
                null_count = cursor.fetchone()[0]
                pct = round((null_count / total) * 100, 2)
                if null_count > 0:
                    report.append({
                        "table": tname,
                        "table_name": tname,
                        "column": col,
                        "column_name": col,
                        "total_rows": total,
                        "null_count": null_count,
                        "missing_rows": null_count,
                        "null_pct": pct,
                        "missing_pct": pct,
                        "severity": "HIGH" if pct > 50 else "MEDIUM" if pct > 10 else "LOW",
                    })

        conn.close()
        return report

    def get_duplicate_report(self) -> List[Dict[str, Any]]:
        """Returns duplicate row count per table (estimated via group-by on all columns)."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [t[0] for t in cursor.fetchall()]

        report = []
        for tname in tables:
            # For large tables (chartevents), limit this to avoid timeout
            cursor.execute(f"SELECT COUNT(*) FROM [{tname}]")
            total = cursor.fetchone()[0]

            cursor.execute(f"PRAGMA table_info({tname})")
            cols = [f"[{c[1]}]" for c in cursor.fetchall()]

            if total > 200000:
                report.append({
                    "table": tname,
                    "total_rows": total,
                    "duplicate_rows": "SKIPPED (large table >200K rows)",
                    "note": "Use query-level analysis for targeted duplicate detection.",
                })
                continue

            col_list = ", ".join(cols)
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) as dup_count FROM (
                        SELECT {col_list}, COUNT(*) as cnt
                        FROM [{tname}]
                        GROUP BY {col_list}
                        HAVING cnt > 1
                    )
                """)
                dup_count = cursor.fetchone()[0]
                report.append({
                    "table": tname,
                    "total_rows": total,
                    "duplicate_rows": dup_count,
                    "duplicate_pct": round((dup_count / total) * 100, 2) if total > 0 else 0,
                })
            except Exception as e:
                report.append({"table": tname, "total_rows": total, "duplicate_rows": f"ERROR: {e}"})

        conn.close()
        return report

    def get_unit_variation_report(self) -> Dict[str, Any]:
        """Returns unit variation for labevents and chartevents."""
        conn = self._connect()
        cursor = conn.cursor()

        result = {}

        # labevents unit variation
        cursor.execute("""
            SELECT l.itemid, d.label, l.valueuom, COUNT(*) as cnt
            FROM labevents l
            LEFT JOIN d_labitems d ON l.itemid = d.itemid
            WHERE l.valueuom IS NOT NULL AND l.valueuom != ''
            GROUP BY l.itemid, l.valueuom
            ORDER BY l.itemid, cnt DESC
        """)
        lab_rows = cursor.fetchall()

        lab_items: Dict[int, Dict] = {}
        for itemid, label, uom, cnt in lab_rows:
            if itemid not in lab_items:
                lab_items[itemid] = {"itemid": itemid, "label": label or "Unknown", "units": {}}
            lab_items[itemid]["units"][uom] = cnt

        lab_variation = [
            {
                "itemid": v["itemid"],
                "item_id": v["itemid"],
                "label": v["label"],
                "distinct_units": len(v["units"]),
                "unit_distribution": v["units"],
                "unit_counts": v["units"],
            }
            for v in lab_items.values()
            if len(v["units"]) > 1
        ]

        # chartevents unit variation (top 20 items with multiple units)
        cursor.execute("""
            SELECT itemid, valueuom, COUNT(*) as cnt
            FROM chartevents
            WHERE valueuom IS NOT NULL AND valueuom != ''
            GROUP BY itemid, valueuom
            ORDER BY itemid, cnt DESC
        """)
        chart_rows = cursor.fetchall()

        chart_items: Dict[int, Dict] = {}
        for itemid, uom, cnt in chart_rows:
            if itemid not in chart_items:
                chart_items[itemid] = {"itemid": itemid, "units": {}}
            chart_items[itemid]["units"][uom] = cnt

        chart_variation = [
            {
                "itemid": v["itemid"],
                "item_id": v["itemid"],
                "label": f"Chart Item {v['itemid']}",
                "distinct_units": len(v["units"]),
                "unit_distribution": v["units"],
                "unit_counts": v["units"],
            }
            for v in chart_items.values()
            if len(v["units"]) > 1
        ][:20]  # top 20 only

        result["labevents_unit_variation"] = {
            "items_with_multiple_units": len(lab_variation),
            "details": lab_variation,
        }
        result["chartevents_unit_variation"] = {
            "items_with_multiple_units": len(chart_variation),
            "details": chart_variation,
        }

        conn.close()
        return result

    def get_measurement_coverage(self) -> Dict[str, Any]:
        """Returns measurement coverage: which patients have lab/chart data."""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM patients")
        total_patients = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT subject_id) FROM labevents")
        lab_patients = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT subject_id) FROM chartevents")
        chart_patients = cursor.fetchone()[0]

        # Top lab measurements
        cursor.execute("""
            SELECT d.label, COUNT(DISTINCT l.subject_id) as patient_count, COUNT(*) as measurement_count
            FROM labevents l
            LEFT JOIN d_labitems d ON l.itemid = d.itemid
            WHERE d.label IS NOT NULL
            GROUP BY d.label
            ORDER BY patient_count DESC
            LIMIT 15
        """)
        top_labs = [{"label": r[0], "patient_count": r[1], "measurement_count": r[2]} for r in cursor.fetchall()]

        # ICU vital coverage (chartevents top items by patient count)
        cursor.execute("""
            SELECT itemid, valueuom, COUNT(DISTINCT subject_id) as patient_count, COUNT(*) as measurement_count
            FROM chartevents
            WHERE valueuom IS NOT NULL AND valueuom != ''
            GROUP BY itemid, valueuom
            ORDER BY patient_count DESC
            LIMIT 10
        """)
        top_vitals = [{"itemid": r[0], "unit": r[1], "patient_count": r[2], "measurement_count": r[3]} for r in cursor.fetchall()]

        conn.close()
        return {
            "total_patients": total_patients,
            "patients_with_lab_data": lab_patients,
            "patients_with_chart_data": chart_patients,
            "lab_coverage_pct": round((lab_patients / total_patients) * 100, 1) if total_patients > 0 else 0,
            "chart_coverage_pct": round((chart_patients / total_patients) * 100, 1) if total_patients > 0 else 0,
            "top_lab_measurements": top_labs,
            "top_icu_vitals": top_vitals,
        }

    def get_coding_patterns(self) -> Dict[str, Any]:
        """Returns ICD coding patterns and admission statistics."""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT icd_version, COUNT(*) FROM diagnoses_icd GROUP BY icd_version")
        icd_versions = {str(r[0]): r[1] for r in cursor.fetchall()}

        cursor.execute("""
            SELECT d.long_title, COUNT(*) as freq
            FROM diagnoses_icd di
            JOIN d_icd_diagnoses d ON di.icd_code = d.icd_code AND di.icd_version = d.icd_version
            GROUP BY d.long_title
            ORDER BY freq DESC
            LIMIT 10
        """)
        top_diagnoses = [{"diagnosis": r[0], "frequency": r[1]} for r in cursor.fetchall()]

        cursor.execute("SELECT admission_type, COUNT(*) as cnt FROM admissions GROUP BY admission_type ORDER BY cnt DESC")
        admission_types = [{"type": r[0], "count": r[1]} for r in cursor.fetchall()]

        cursor.execute("""
            SELECT hadm_id, COUNT(DISTINCT icd_version) as version_count
            FROM diagnoses_icd
            GROUP BY hadm_id
            HAVING version_count > 1
        """)
        mixed_icd_admissions = cursor.fetchall()

        conn.close()
        return {
            "icd_version_distribution": icd_versions,
            "admissions_with_mixed_icd_versions": len(mixed_icd_admissions),
            "top_10_diagnoses": top_diagnoses,
            "admission_type_distribution": admission_types,
        }

    def run_full_analysis(self) -> Dict[str, Any]:
        """
        Runs all dataset-level analyses. Used by /api/insights.
        Returns a comprehensive dataset quality and coverage report.
        """
        quality_summary = self.get_quality_flags_summary()
        return {
            "table_inventory": self.get_table_inventory(),
            "missingness_report": self.get_missingness_report(),
            "duplicate_report": self.get_duplicate_report(),
            "unit_variation": self.get_unit_variation_report(),
            "measurement_coverage": self.get_measurement_coverage(),
            "coding_patterns": self.get_coding_patterns(),
            "quality_summary": quality_summary,
            "meta": {
                "source": "MIMIC-IV Demo Dataset",
                "analysis_type": "dataset_level",
                "note": "This analysis covers the entire available database independently of any user query.",
                "disclaimer": "For research and educational purposes only. Not for clinical use.",
            },
        }