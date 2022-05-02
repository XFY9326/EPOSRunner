import os
from typing import List, Dict

# noinspection PyUnresolvedReferences
from epos_runner.analyzer import AbstractAnalyzer
# noinspection PyUnresolvedReferences
from epos_runner.utils import generate_weights, report_minium_global_cost

# Executor parallel size
PARALLEL_SIZE = 4
# Show params before all tasks start
PRINT_PARAMS = True
# Show best result after all task finished
PRINT_BEST_RESULT = True

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
# epos.py
# config.py
# epos_runner/
# workspace/ - conf/log4j.properties, measurement.conf, protopeer.conf
#            - datasets/<dataset>
#            - epos.template.properties
#            - IEPOS-Tutorial.jar
WORKSPACE_PATH = os.path.join(CURRENT_DIR, "workspace")
EPOS_PROPERTIES_TEMPLATE_PATH = os.path.join(WORKSPACE_PATH, "epos.template.properties")
REPORT_PATH = os.path.join(CURRENT_DIR, "result.csv")

# Dict[str, List[str]]
PARAMS = {
    "numChildren": [2, 4],
    "weightsString": generate_weights(0.3, (0.20, 0.25, 0.01), 2)
}


class MiniumGlobalCostAnalyzer(AbstractAnalyzer):
    def required_propreties(self, properties: Dict[str, str]) -> Dict[str, str]:
        # Force enable GlobalCostLogger
        properties["logger.GlobalCostLogger"] = "true"
        return properties

    def generate_report(self, output_dir: str) -> dict:
        return report_minium_global_cost(output_dir)

    def best_result(self, reports: List[dict]) -> int:
        return reports.index(min(reports, key=lambda x: x["var"]))


ANALYZER: AbstractAnalyzer = MiniumGlobalCostAnalyzer()
