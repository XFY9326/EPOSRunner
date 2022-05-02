import csv
import os
import sys
from itertools import product
from typing import Union, Tuple, List

from epos_runner import EPOSOutput


# range: Union[float, Tuple[float, float, float]] -> (specific float) or (inclusive start, exclusive end, step)
def generate_weights(alpha_range: Union[float, Tuple[float, float, float]],
                     beta_range: Union[float, Tuple[float, float, float]],
                     float_precision: int,
                     ignore_overflow: bool = True) -> List[str]:
    def _parse_float_range(float_range: Union[float, Tuple[float, float, float]], min_value: float, max_value: float) -> List[float]:
        if isinstance(float_range, float):
            if float_range > max_value or float_range < min_value:
                raise ValueError(f"Alpha range error! {float_range}")
            float_list = [float_range]
        else:
            if float_range[0] > max_value or float_range[0] < min_value or float_range[1] > max_value or float_range[1] < min_value or float_range[0] > float_range[1]:
                raise ValueError(f"Alpha range error! [{float_range[0]}:{float_range[1]}] step {float_range[2]}")
            temp = float_range[0]
            float_list = [temp]
            while temp < float_range[1]:
                temp += float_range[2]
                float_list.append(temp)
        return float_list

    alpha_list = _parse_float_range(alpha_range, 0, 1)
    beta_list = _parse_float_range(beta_range, 0, 1)

    result = []
    for items in product(alpha_list, beta_list):
        # noinspection PyStringFormat
        content = f"%.{float_precision}f,%.{float_precision}f" % items
        if items[0] + items[1] > 1:
            if ignore_overflow:
                continue
            else:
                raise ValueError(f"Wrong alpha and beta '{content}'!")
        result.append(content)
    return result


def report_minium_global_cost(output_dir: str) -> dict:
    csv_file_path = os.path.join(output_dir, EPOSOutput.GLOBAL_COST_CSV_FILE)
    if os.path.isfile(csv_file_path):
        min_cost = {
            "iteration": None,
            "run": None,
            "var": sys.float_info.max
        }
        with open(csv_file_path, "r") as f:
            skip_head = False
            for row in csv.reader(f.readlines()):
                if not skip_head or row[0] == "Iteration":
                    skip_head = True
                    continue
                for i in range(3, len(row)):
                    value = float(row[i])
                    if value < min_cost["var"]:
                        min_cost["iteration"] = int(row[0])
                        min_cost["run"] = f"Run-{i - 3}"
                        min_cost["var"] = value
        return min_cost
    else:
        raise IOError(f"Global cost csv can't be found in: {csv_file_path}")
