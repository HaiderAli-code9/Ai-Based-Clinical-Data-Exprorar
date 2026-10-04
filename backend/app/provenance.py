# backend/app/provenance.py
"""
Provenance Tracer for ClinData Explorer.

Every important finding must be traceable to:
  - source_table
  - source_field
  - record_identifier
  - subject_identifier
  - timestamp (if available)
  - rule_id that produced the finding
  - transformation applied (None for raw source data)

This module NEVER invents provenance. If unavailable, it explicitly states so.
"""

from typing import Optional, Dict, Any, List
import pandas as pd


class ProvenanceRecord:
    """Represents a single provenance trace for a data finding."""

    def __init__(
        self,
        finding_type: str,
        source_table: str,
        source_field: str,
        record_id: Optional[Any],
        subject_id: Optional[Any],
        timestamp: Optional[str],
        rule_id: str,
        rule_name: str,
        original_value: Any,
        transformation_applied: str = "None (raw source data)",
        provenance_available: bool = True,
    ):
        self.finding_type = finding_type
        self.source_table = source_table
        self.source_field = source_field
        self.record_id = record_id if record_id is not None else "UNAVAILABLE"
        self.subject_id = subject_id if subject_id is not None else "UNAVAILABLE"
        self.timestamp = timestamp if timestamp else "UNAVAILABLE"
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.original_value = original_value
        self.transformation_applied = transformation_applied
        self.provenance_available = provenance_available

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_type": self.finding_type,
            "provenance_chain": {
                "source_table": self.source_table,
                "source_field": self.source_field,
                "record_id": str(self.record_id),
                "subject_id": str(self.subject_id),
                "timestamp": self.timestamp,
            },
            "rule": {
                "rule_id": self.rule_id,
                "rule_name": self.rule_name,
            },
            "original_value": str(self.original_value),
            "transformation_applied": self.transformation_applied,
            "provenance_available": self.provenance_available,
            "provenance_note": (
                "Full provenance trace available."
                if self.provenance_available
                else "Provenance is partially unavailable. Source field or record identifier could not be determined from returned data."
            ),
        }


class ProvenanceTracer:
    """
    Builds provenance records for DQ findings and cohort results.
    Always traces findings to source table, field, record, and subject.
    Never invents provenance — explicitly states when unavailable.
    """

    def __init__(self, source_table: str):
        self.source_table = source_table
        self.records: List[ProvenanceRecord] = []

    def _get_timestamp_col(self, row: pd.Series) -> Optional[str]:
        """Try known timestamp column names in order of preference."""
        for col in ["charttime", "admittime", "starttime", "intime", "storetime"]:
            if col in row.index and pd.notna(row[col]):
                return str(row[col])
        return None

    def _get_record_id(self, row: pd.Series) -> Optional[Any]:
        """Try known record identifier columns."""
        for col in ["labevent_id", "transfer_id", "hadm_id", "stay_id", "pharmacy_id"]:
            if col in row.index and pd.notna(row[col]):
                return row[col]
        return None

    def trace_missing_value(self, row: pd.Series, column: str) -> ProvenanceRecord:
        record = ProvenanceRecord(
            finding_type="Missing Value",
            source_table=self.source_table,
            source_field=column,
            record_id=self._get_record_id(row),
            subject_id=row.get("subject_id", None),
            timestamp=self._get_timestamp_col(row),
            rule_id="DQ-001",
            rule_name="Missing Value Check",
            original_value="NULL / NaN",
            provenance_available=True,
        )
        self.records.append(record)
        return record

    def trace_duplicate(self, row: pd.Series) -> ProvenanceRecord:
        record = ProvenanceRecord(
            finding_type="Duplicate Record",
            source_table=self.source_table,
            source_field="Entire Row",
            record_id=self._get_record_id(row),
            subject_id=row.get("subject_id", None),
            timestamp=self._get_timestamp_col(row),
            rule_id="DQ-002",
            rule_name="Exact Duplicate Row Check",
            original_value=str(row.to_dict()),
            provenance_available=True,
        )
        self.records.append(record)
        return record

    def trace_temporal_misalignment(
        self,
        row: pd.Series,
        start_col: str,
        end_col: str,
        rule_id: str,
        rule_name: str,
    ) -> ProvenanceRecord:
        record = ProvenanceRecord(
            finding_type="Temporal Misalignment",
            source_table=self.source_table,
            source_field=f"{start_col} / {end_col}",
            record_id=self._get_record_id(row),
            subject_id=row.get("subject_id", None),
            timestamp=str(row.get(start_col, "UNAVAILABLE")),
            rule_id=rule_id,
            rule_name=rule_name,
            original_value=f"{start_col}={row.get(start_col)}, {end_col}={row.get(end_col)}",
            provenance_available=True,
        )
        self.records.append(record)
        return record

    def trace_implausible_value(
        self,
        row: pd.Series,
        column: str,
        value: Any,
        rule_id: str,
        rule_name: str,
    ) -> ProvenanceRecord:
        record = ProvenanceRecord(
            finding_type="Implausible Value",
            source_table=self.source_table,
            source_field=column,
            record_id=self._get_record_id(row),
            subject_id=row.get("subject_id", None),
            timestamp=self._get_timestamp_col(row),
            rule_id=rule_id,
            rule_name=rule_name,
            original_value=value,
            provenance_available=True,
        )
        self.records.append(record)
        return record

    def trace_ref_range_outlier(self, row: pd.Series) -> ProvenanceRecord:
        record = ProvenanceRecord(
            finding_type="Reference Range Outlier",
            source_table=self.source_table,
            source_field="valuenum",
            record_id=self._get_record_id(row),
            subject_id=row.get("subject_id", None),
            timestamp=self._get_timestamp_col(row),
            rule_id="DQ-008",
            rule_name="Reference Range Outlier — Lab Events",
            original_value=f"value={row.get('valuenum')}, ref=[{row.get('ref_range_lower')}, {row.get('ref_range_upper')}]",
            provenance_available=True,
        )
        self.records.append(record)
        return record

    def trace_unit_variation(
        self,
        itemid: Any,
        units: List[str],
        count: int,
        rule_id: str,
        rule_name: str,
    ) -> ProvenanceRecord:
        record = ProvenanceRecord(
            finding_type="Unit Variation",
            source_table=self.source_table,
            source_field="valueuom",
            record_id=f"itemid={itemid}",
            subject_id="Multiple (cohort-level)",
            timestamp="UNAVAILABLE (aggregate finding)",
            rule_id=rule_id,
            rule_name=rule_name,
            original_value=f"itemid={itemid} has {count} distinct units: {units}",
            transformation_applied="None — aggregate unit count per itemid",
            provenance_available=True,
        )
        self.records.append(record)
        return record

    def trace_icd_version_mix(self, hadm_id: Any, versions: List[int]) -> ProvenanceRecord:
        record = ProvenanceRecord(
            finding_type="Mixed ICD Coding Version",
            source_table=self.source_table,
            source_field="icd_version",
            record_id=f"hadm_id={hadm_id}",
            subject_id="UNAVAILABLE (need JOIN with admissions)",
            timestamp="UNAVAILABLE",
            rule_id="DQ-012",
            rule_name="Mixed ICD Version Coding",
            original_value=f"Admission {hadm_id} contains ICD versions: {versions}",
            provenance_available=True,
        )
        self.records.append(record)
        return record

    def get_all_provenance(self) -> List[Dict[str, Any]]:
        """Return all traced provenance records as a list of dicts."""
        return [r.to_dict() for r in self.records]

    def summary(self) -> Dict[str, Any]:
        """Return a high-level summary of provenance coverage."""
        if not self.records:
            return {"total_findings": 0, "provenance_available": 0, "provenance_unavailable": 0}
        avail = sum(1 for r in self.records if r.provenance_available)
        return {
            "total_findings": len(self.records),
            "provenance_available": avail,
            "provenance_unavailable": len(self.records) - avail,
            "source_table": self.source_table,
        }
