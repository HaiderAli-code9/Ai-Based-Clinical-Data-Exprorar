# backend/app/dataset_insights.py
"""
Dataset Insights Service for ClinData Explorer.
Provides a comprehensive overview of the entire MIMIC-IV Demo database.
This is INDEPENDENT of any user query — it analyzes the full dataset.
Used by the /api/insights endpoint.
"""

from data_quality import DatasetLevelAnalyzer
from quality_rules import rules_registry


class DatasetInsightsService:
    """
    Orchestrates full dataset-level analysis and returns a structured
    insights report for the Dataset Insights frontend page.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.analyzer = DatasetLevelAnalyzer(db_path=db_path)

    def get_full_insights(self) -> dict:
        """
        Returns a complete dataset insights report.
        This is the data source for the Dataset Insights frontend page.
        """
        analysis = self.analyzer.run_full_analysis()

        return {
            "database_overview": self._build_overview(analysis["table_inventory"]),
            "table_inventory": analysis["table_inventory"],
            "table_details": analysis["table_inventory"],
            "missingness_report": analysis["missingness_report"],
            "duplicate_report": analysis["duplicate_report"],
            "unit_variation": analysis["unit_variation"],
            "measurement_coverage": analysis["measurement_coverage"],
            "coding_patterns": analysis["coding_patterns"],
            "quality_summary": analysis["quality_summary"],
            "quality_rules": rules_registry.to_dict_list(),
            "meta": analysis["meta"],
        }

    def _build_overview(self, inventory: list) -> dict:
        total_tables = len(inventory)
        total_rows = sum(t["row_count"] for t in inventory)
        total_columns = sum(t["column_count"] for t in inventory)
        return {
            "total_tables": total_tables,
            "total_rows": total_rows,
            "total_columns": total_columns,
            "table_names": [t["table_name"] for t in inventory],
            "largest_table": max(inventory, key=lambda x: x["row_count"])["table_name"] if inventory else None,
        }
