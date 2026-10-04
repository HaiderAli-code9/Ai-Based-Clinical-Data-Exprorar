# backend/app/quality_rules.py
"""
Quality Rules Registry for ClinData Explorer.
Each rule is a named, versioned definition used by the DataQualityAnalyzer
and ProvenanceTracer. Rules are NEVER applied automatically to clinical data —
they only flag issues for researcher review.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class QualityRule:
    rule_id: str
    name: str
    version: str
    description: str
    applies_to_tables: List[str]
    applies_to_columns: List[str]
    check_type: str          # "missing" | "duplicate" | "temporal" | "implausible" | "unit_variation" | "ref_range" | "coding"
    severity: str            # "WARNING" | "ERROR" | "INFO"
    action: str              # What analyst should do
    reversible: bool = True  # Whether any suggested correction is reversible


# ── Registry Definition ─────────────────────────────────────────────────────

QUALITY_RULES: List[QualityRule] = [

    # ── Missing Value Rules ──────────────────────────────────────────────────
    QualityRule(
        rule_id="DQ-001",
        name="Missing Value Check",
        version="1.0",
        description="Detects NULL or NaN values in any retrieved column. Missing clinical data can bias cohort analysis.",
        applies_to_tables=["patients", "admissions", "labevents", "chartevents", "diagnoses_icd", "prescriptions"],
        applies_to_columns=["*"],
        check_type="missing",
        severity="WARNING",
        action="Flagged for researcher review. No imputation applied. Consider excluding records with critical missing fields.",
        reversible=True,
    ),

    # ── Duplicate Rules ──────────────────────────────────────────────────────
    QualityRule(
        rule_id="DQ-002",
        name="Exact Duplicate Row Check",
        version="1.0",
        description="Detects exact row-level duplicates in retrieved cohort data. Duplicates can inflate statistics.",
        applies_to_tables=["*"],
        applies_to_columns=["*"],
        check_type="duplicate",
        severity="ERROR",
        action="Flagged as duplicate. Original records preserved. Researcher should verify if duplication is intentional.",
        reversible=True,
    ),

    # ── Temporal Rules ───────────────────────────────────────────────────────
    QualityRule(
        rule_id="DQ-003",
        name="Admission/Discharge Temporal Misalignment",
        version="1.0",
        description="Discharge time must be strictly after admission time. Reversed timestamps indicate data entry errors.",
        applies_to_tables=["admissions"],
        applies_to_columns=["admittime", "dischtime"],
        check_type="temporal",
        severity="ERROR",
        action="Flagged as impossible timeline. No automatic correction. Records should be reviewed against source EHR.",
        reversible=True,
    ),
    QualityRule(
        rule_id="DQ-004",
        name="ICU Intime/Outtime Temporal Misalignment",
        version="1.0",
        description="ICU outtime must be strictly after intime. Reversed timestamps indicate a data quality issue.",
        applies_to_tables=["icustays"],
        applies_to_columns=["intime", "outtime"],
        check_type="temporal",
        severity="ERROR",
        action="Flagged as impossible ICU timeline. Original data preserved.",
        reversible=True,
    ),
    QualityRule(
        rule_id="DQ-005",
        name="Prescription Start/Stop Temporal Misalignment",
        version="1.0",
        description="Prescription stoptime must be after starttime. Reversed timestamps indicate data entry or ETL errors.",
        applies_to_tables=["prescriptions"],
        applies_to_columns=["starttime", "stoptime"],
        check_type="temporal",
        severity="WARNING",
        action="Flagged for review. Prescriptions with reversed timelines may affect medication exposure analysis.",
        reversible=True,
    ),
    QualityRule(
        rule_id="DQ-006",
        name="Chart Event Storetime Before Charttime",
        version="1.0",
        description="Storetime (when data was stored) should not be significantly before charttime (when data was recorded).",
        applies_to_tables=["chartevents"],
        applies_to_columns=["charttime", "storetime"],
        check_type="temporal",
        severity="INFO",
        action="Flagged for awareness. Minor discrepancies may be expected but large gaps indicate data pipeline issues.",
        reversible=True,
    ),

    # ── Implausible Value Rules ──────────────────────────────────────────────
    QualityRule(
        rule_id="DQ-007",
        name="Negative Age Check",
        version="1.0",
        description="Patient anchor_age cannot be negative. Negative values indicate data entry or ETL errors.",
        applies_to_tables=["patients"],
        applies_to_columns=["anchor_age"],
        check_type="implausible",
        severity="ERROR",
        action="Flagged as biologically impossible. No automatic correction applied.",
        reversible=True,
    ),
    QualityRule(
        rule_id="DQ-008",
        name="Reference Range Outlier — Lab Events",
        version="1.0",
        description="Detects lab values outside the documented reference range (ref_range_lower, ref_range_upper). May indicate abnormal physiology or data entry error.",
        applies_to_tables=["labevents"],
        applies_to_columns=["valuenum", "ref_range_lower", "ref_range_upper"],
        check_type="ref_range",
        severity="INFO",
        action="Flagged as outside reference range. This may be a clinical finding (not necessarily a data error). Researcher should distinguish between clinical vs data-quality interpretation.",
        reversible=True,
    ),
    QualityRule(
        rule_id="DQ-009",
        name="Reference Range Outlier — Chart Events",
        version="1.0",
        description="Detects ICU vital/measurement values that are physiologically implausible (e.g., SpO2 > 100%, HR < 0, temperature > 45°C).",
        applies_to_tables=["chartevents"],
        applies_to_columns=["valuenum", "valueuom"],
        check_type="implausible",
        severity="WARNING",
        action="Flagged as physiologically implausible. Original data preserved. Confirm against clinical context.",
        reversible=True,
    ),

    # ── Unit Variation Rules ─────────────────────────────────────────────────
    QualityRule(
        rule_id="DQ-010",
        name="Unit Variation — Lab Events",
        version="1.0",
        description="Multiple measurement units for the same lab item (itemid) indicate inconsistent data entry or system migration issues.",
        applies_to_tables=["labevents"],
        applies_to_columns=["itemid", "valueuom"],
        check_type="unit_variation",
        severity="WARNING",
        action="Flagged for review. Unit conversion may be required before statistical analysis. Original units preserved.",
        reversible=True,
    ),
    QualityRule(
        rule_id="DQ-011",
        name="Unit Variation — Chart Events",
        version="1.0",
        description="Multiple measurement units for the same chart item (itemid) in chartevents indicate inconsistent documentation.",
        applies_to_tables=["chartevents"],
        applies_to_columns=["itemid", "valueuom"],
        check_type="unit_variation",
        severity="WARNING",
        action="Flagged for review. Researchers should standardize units before trend analysis.",
        reversible=True,
    ),

    # ── Coding Pattern Rules ─────────────────────────────────────────────────
    QualityRule(
        rule_id="DQ-012",
        name="Mixed ICD Version Coding",
        version="1.0",
        description="A single hospital admission contains both ICD-9 and ICD-10 diagnosis codes. This may indicate incomplete ICD migration.",
        applies_to_tables=["diagnoses_icd"],
        applies_to_columns=["icd_version", "hadm_id"],
        check_type="coding",
        severity="WARNING",
        action="Flagged for researcher awareness. Mixed ICD versions can complicate phenotyping and cohort definition.",
        reversible=True,
    ),
]


class QualityRulesRegistry:
    """
    Central registry for all data quality rules.
    Provides lookup by rule_id, check_type, table, or severity.
    """

    def __init__(self):
        self._rules = {rule.rule_id: rule for rule in QUALITY_RULES}

    def get_rule(self, rule_id: str) -> QualityRule:
        return self._rules.get(rule_id)

    def get_by_check_type(self, check_type: str) -> List[QualityRule]:
        return [r for r in QUALITY_RULES if r.check_type == check_type]

    def get_by_table(self, table_name: str) -> List[QualityRule]:
        return [r for r in QUALITY_RULES if table_name in r.applies_to_tables or "*" in r.applies_to_tables]

    def get_by_severity(self, severity: str) -> List[QualityRule]:
        return [r for r in QUALITY_RULES if r.severity == severity]

    def all_rules(self) -> List[QualityRule]:
        return list(QUALITY_RULES)

    def to_dict_list(self) -> list:
        """Return all rules as a list of dicts for API serialization."""
        return [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "version": r.version,
                "description": r.description,
                "applies_to_tables": r.applies_to_tables,
                "applies_to_columns": r.applies_to_columns,
                "check_type": r.check_type,
                "category": r.check_type.capitalize(),
                "severity": r.severity,
                "action": r.action,
                "reversible": r.reversible,
            }
            for r in QUALITY_RULES
        ]



# Singleton instance
rules_registry = QualityRulesRegistry()
