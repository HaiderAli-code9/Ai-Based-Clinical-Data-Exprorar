"""
MIMIC-IV Demo table catalog — purposes derived from actual schema and MIMIC-IV documentation.
Used for Table Inventory descriptions and SQL source-table extraction.
"""

TABLE_PURPOSES: dict[str, str] = {
    "patients": "Core patient demographics: subject identifiers, gender, anchor age/year, and date of death when recorded.",
    "admissions": "Hospital admission episodes with admission/discharge times, locations, insurance, and mortality flags.",
    "icustays": "ICU stay records linked to admissions, including care unit, intime/outtime, and length of stay.",
    "chartevents": "ICU bedside charted measurements and vitals (values, units, chart/store timestamps).",
    "labevents": "Laboratory measurement results with numeric values, units, reference ranges, and flags.",
    "d_labitems": "Dictionary of laboratory item identifiers with labels, fluid type, and category.",
    "diagnoses_icd": "ICD diagnosis codes assigned per hospital admission with sequence numbers.",
    "d_icd_diagnoses": "Dictionary mapping ICD codes and versions to long diagnosis titles.",
    "prescriptions": "Medication prescriptions with drug name, dose, route, and start/stop times.",
    "transfers": "Intra-hospital transfer events between care units with timestamps.",
}

KNOWN_TABLES: list[str] = list(TABLE_PURPOSES.keys())
