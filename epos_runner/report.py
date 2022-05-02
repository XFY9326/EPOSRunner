import csv
import os
from typing import List, Dict, Any

from epos_runner.analyzer import AbstractAnalyzer
from epos_runner.log import logger


class Report:

    @staticmethod
    def print_params(params: Dict[str, List[Any]]):
        if len(params) > 0:
            logger.info("Params:")
            for key, value in params.items():
                logger.info(f"\t{key} = {value}")
        else:
            logger.info("Empty Params!")

    @staticmethod
    def print_report(output_name: str, modified_values: dict, report: dict):
        logger.info(f"Output path: {output_name}")
        if len(report) > 0:
            logger.info(f"Report values:")
            for key, value in report.items():
                logger.info(f"\t{key}: {value}")
        logger.info("Modified values:")
        for key, value in sorted(modified_values.items()):
            logger.info(f"\t{key} = {value}")

    @staticmethod
    def print_best_report(bundled_reports: List[dict], analyzer: AbstractAnalyzer):
        logger.info("Best result:")
        best_report_index = analyzer.best_result([i["report"] for i in bundled_reports])
        best_output_name = bundled_reports[best_report_index]["output"]
        best_modified_values = bundled_reports[best_report_index]["modified"]
        best_report = bundled_reports[best_report_index]["report"]
        Report.print_report(best_output_name, best_modified_values, best_report)

    @staticmethod
    def generate_bundled_report(output_dir: str, modified_values: dict, analyzer: AbstractAnalyzer) -> dict:
        return {
            "output": os.path.basename(output_dir),
            "modified": modified_values,
            "report": analyzer.generate_report(output_dir)
        }

    @staticmethod
    def append_bundled_report(csv_file_path: str, bundled_report: dict):
        new_file = not os.path.isfile(csv_file_path)
        report_keys = list(bundled_report["report"].keys())
        with open(csv_file_path, "a") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(["output", "modified"] + report_keys)
            modified_content = ", ".join([f"{k} = {v}" for k, v in sorted(bundled_report["modified"].items())])
            row = [bundled_report["output"], modified_content]
            for key in report_keys:
                row.append(bundled_report["report"][key])
            writer.writerow(row)
            os.fsync(f)
