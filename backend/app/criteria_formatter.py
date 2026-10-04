"""
Convert structured cohort criteria into human-readable inclusion/exclusion rules.
Raw SQL expressions must not be shown as criteria — SQL stays under Generated SQL only.
"""

from typing import Any, List

OPERATOR_PHRASES = {
    "=": "equals",
    "==": "equals",
    "!=": "does not equal",
    "<>": "does not equal",
    ">": "greater than",
    ">=": "greater than or equal to",
    "<": "less than",
    "<=": "less than or equal to",
    "LIKE": "matches pattern",
    "IN": "is one of",
    "NOT IN": "is not one of",
    "IS NULL": "is missing",
    "IS NOT NULL": "is present",
}

FIELD_LABELS = {
    "anchor_age": "Age",
    "gender": "Gender",
    "admission_type": "Admission type",
    "admission_location": "Admission location",
    "discharge_location": "Discharge location",
    "insurance": "Insurance",
    "race": "Race",
    "marital_status": "Marital status",
    "hospital_expire_flag": "In-hospital mortality flag",
    "first_careunit": "First ICU care unit",
    "last_careunit": "Last ICU care unit",
    "los": "Length of ICU stay",
    "icd_code": "Diagnosis code",
    "icd_version": "ICD version",
    "long_title": "Diagnosis",
    "drug": "Medication",
    "drug_type": "Medication type",
    "itemid": "Measurement item",
    "label": "Measurement label",
    "valueuom": "Measurement unit",
    "subject_id": "Patient",
    "hadm_id": "Hospital admission",
    "stay_id": "ICU stay",
}

TABLE_CONTEXT = {
    "patients": "Patient",
    "admissions": "Admission",
    "icustays": "ICU stay",
    "chartevents": "Chart event",
    "labevents": "Lab result",
    "diagnoses_icd": "Diagnosis",
    "d_icd_diagnoses": "Diagnosis dictionary",
    "prescriptions": "Prescription",
    "transfers": "Transfer",
    "d_labitems": "Lab item",
}


def _looks_like_sql(text: str) -> bool:
    upper = text.upper()
    sql_tokens = ("SELECT ", " FROM ", " WHERE ", " JOIN ", " GROUP BY ", " HAVING ", " ORDER BY ")
    return any(tok in upper for tok in sql_tokens)


def _label_for_field(field: str) -> str:
    if not field:
        return "Criterion"
    return FIELD_LABELS.get(field, field.replace("_", " ").strip().title())


def _strip_prefix(text: str) -> str:
    """Remove any leading bracketed prefix like [ INCLUDE ] or [ EXCLUDE ]."""
    if text.startswith("[") and "]" in text:
        return text.split("]", 1)[-1].strip()
    return text


def _format_value(value: Any) -> str:
    """Format a value for display in a SQL condition."""
    if value is None:
        return "NULL"
    if isinstance(value, str):
        # If already quoted, keep as is; otherwise add single quotes
        if not (value.startswith("'") and value.endswith("'")):
            return f"'{value}'"
        return value
    return str(value)


def humanize_criterion(item: Any, *, kind: str = "INCLUDE") -> str:
    """
    Convert one inclusion/exclusion criterion to a SQL‑like condition.
    Example: { "field": "anchor_age", "operator": ">", "value": 20, "table": "patients" }
    -> "patients.anchor_age > 20"
    """
    if isinstance(item, str):
        # If it's a string, try to convert known phrases to SQL
        cleaned = item.strip()
        if not cleaned:
            return ""
        # If it already looks like SQL, return as is
        if any(tok in cleaned.upper() for tok in ("SELECT", "FROM", "WHERE", "JOIN")):
            return cleaned
        # Otherwise, keep it as descriptive text (fallback)
        return cleaned

    if not isinstance(item, dict):
        return str(item)

    field = str(item.get("field", "") or item.get("column", "")).strip()
    operator = str(item.get("operator", "=")).strip().upper()
    value = item.get("value", "")
    table = str(item.get("table", "") or item.get("source_table", "")).strip().lower()

    if not field:
        return ""

    if table:
        condition = f"{table}.{field}"
    else:
        condition = field

    if operator in ("IS NULL", "IS NOT NULL"):
        condition = f"{condition} {operator}"
    else:
        formatted_value = _format_value(value)
        condition = f"{condition} {operator} {formatted_value}"

    return condition


def format_criteria_human_readable(criteria_list: List[Any], *, kind: str = "INCLUDE") -> List[str]:
    """
    Format a list of criteria into SQL‑like conditions (without INCLUDE/EXCLUDE prefixes).
    Duplicates are removed.
    """
    formatted: List[str] = []
    seen: set[str] = set()
    for item in criteria_list or []:
        text = humanize_criterion(item, kind=kind).strip()
        if text and text not in seen:
            seen.add(text)
            formatted.append(text)
    return formatted