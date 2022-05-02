from abc import abstractmethod
from typing import Dict, List


class AbstractAnalyzer:
    # Force set properties before run EPOS
    @abstractmethod
    def required_propreties(self, properties: Dict[str, str]) -> Dict[str, str]:
        pass

    # This returned dict will be converted and exported to a csv file
    @abstractmethod
    def generate_report(self, output_dir: str) -> dict:
        pass

    # Return best report dict index
    @abstractmethod
    def best_result(self, reports: List[dict]) -> int:
        pass
