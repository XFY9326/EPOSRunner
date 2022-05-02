#!/usr/bin/env python3

import asyncio
import csv
import json
import os
import subprocess
import sys
from copy import deepcopy
from itertools import product
from typing import Dict, List, Optional, Tuple, Union

SHOW_TEST_PARAMS = True
SHOW_ALL_JAR_EXECUTING_OUTPUT = False
SHOW_EVERY_ANALYSE_REPORT = True

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
JAR_FILE = os.path.join(CURRENT_DIR, "IEPOS-Tutorial.jar")
OUTPUT_FOLDER = os.path.join(CURRENT_DIR, "output")
CONF_FOLDER = os.path.join(CURRENT_DIR, "conf")
GLOBAL_COST_CSV_FILE = "global-cost.csv"
EPOS_PROPERTIES_FILE = "epos.properties"
EPOS_PROPERTIES_PATH = os.path.join(CONF_FOLDER, EPOS_PROPERTIES_FILE)
EPOS_TEMPLATE_PROPERTIES_FILE = "epos.template.properties"
EPOS_TEMPLATE_PROPERTIES_PATH = os.path.join(
    CURRENT_DIR, EPOS_TEMPLATE_PROPERTIES_FILE)
RUN_RESULT_OUTPUT_CSV_FILE = "results.csv"


# range: Union[float, Tuple[float, float, float]] -> specific float | inclusive start, inclusive end, step
def generate_weights(alpha_range: Union[float, Tuple[float, float, float]], beta_range: Union[float, Tuple[float, float, float]], float_precision: int,
                     ignore_overflow: bool = True) -> List[str]:
    result = []

    if isinstance(alpha_range, float):
        if alpha_range > 1 or alpha_range < 0:
            sys.exit(f"Alpha range error! {alpha_range}")
        alpha_list = [alpha_range]
    else:
        if alpha_range[0] > 1 or alpha_range[0] < 0 or alpha_range[1] > 1 or alpha_range[1] < 0 \
                or alpha_range[0] > alpha_range[1] or alpha_range[2] <= 0:
            sys.exit(
                f"Alpha range error! [{alpha_range[0]}:{alpha_range[1]}] step {alpha_range[2]}")
        temp = alpha_range[0]
        alpha_list = [temp]
        while temp <= alpha_range[1]:
            temp += alpha_range[2]
            alpha_list.append(temp)

    if isinstance(beta_range, float):
        if beta_range > 1 or beta_range < 0:
            sys.exit(f"Beta range error! {beta_range}")
        beta_list = [beta_range]
    else:
        if beta_range[0] > 1 or beta_range[0] < 0 or beta_range[1] > 1 or beta_range[1] < 0 \
                or beta_range[0] > beta_range[1] or beta_range[2] <= 0:
            sys.exit(
                f"Beta range error! [{beta_range[0]}:{beta_range[1]}] step {beta_range[2]}")
        temp = beta_range[0]
        beta_list = [temp]
        while temp <= beta_range[1]:
            temp += beta_range[2]
            beta_list.append(temp)

    for items in product(alpha_list, beta_list):
        if items[0] + items[1] > 1:
            if ignore_overflow:
                continue
            else:
                # noinspection PyStringFormat
                sys.exit(f"Wrong alpha '%.{float_precision}f' beta '%.{float_precision}f'" % items)
        # noinspection PyStringFormat
        result.append(f"%.{float_precision}f,%.{float_precision}f" % items)
    return result


# Dict[str, List[str]]
TEST_PARAMS = {
    "numChildren": [2],
    "weightsString": generate_weights(0.3, (0.20, 0.25, 0.01), 2),
}


def get_latest_output() -> Optional[str]:
    outputs = [p for p in os.listdir(OUTPUT_FOLDER) if os.path.isdir(
        os.path.join(OUTPUT_FOLDER, p)) and not p.startswith(".") and "_" in p]
    if len(outputs) == 0:
        return None
    else:
        return sorted(outputs, key=lambda x: int(x.split("_")[1]))[len(outputs) - 1]


def analyse_output_cost(output_name: str, modified: dict) -> dict:
    csv_file_path = os.path.join(
        OUTPUT_FOLDER, output_name, GLOBAL_COST_CSV_FILE)
    if os.path.isfile(csv_file_path):
        min_cost = {"Iteration": None, "Run": None, "Var": sys.float_info.max}
        with open(csv_file_path, "r") as f:
            skip_head = False
            for row in csv.reader(f.readlines()):
                if not skip_head:
                    skip_head = True
                    continue
                for i in range(3, len(row)):
                    value = float(row[i])
                    if value < min_cost["Var"]:
                        min_cost["Iteration"] = int(row[0])
                        min_cost["Run"] = f"Run-{i - 3}"
                        min_cost["Var"] = value
        if SHOW_EVERY_ANALYSE_REPORT:
            print(
                f"Minuinm global cost:\n" +
                f"\tIteration: {min_cost['Iteration']}\n" +
                f"\tRun: {min_cost['Run']}\n" +
                f"\tVar: {min_cost['Var']}"
            )
            print("Modified properties:")
            for key, value in sorted(modified.items()):
                print(f"\t{key} = {value}")
        return {
            "output": output_name,
            "iteration": min_cost['Iteration'],
            "run": min_cost['Run'],
            "var": min_cost['Var']
        }
    else:
        sys.exit(f"Global cost csv can't be found in: {csv_file_path}")


def run_analyse(modified: dict) -> dict:
    print(os.linesep + "=" * 20 + " Analysing " + "=" * 20, end=os.linesep * 2)
    latest_output = get_latest_output()
    if latest_output is None:
        sys.exit(f"No new output available!")
    else:
        print(f"Target latest output: {latest_output}")
        return analyse_output_cost(latest_output, modified)


async def execute_jar():
    with subprocess.Popen(["java", "-jar", JAR_FILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, errors="replace") as process:
        async def process_output():
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    if SHOW_ALL_JAR_EXECUTING_OUTPUT or (output.startswith("Simulation") or output.startswith("IEPOS Finished")):
                        print(output.strip(), flush=True)

        async def process_error():
            error_content = ""
            while True:
                error = process.stderr.readline()
                exit_value = process.poll()
                if error == '' and exit_value is not None:
                    break
                if error:
                    if SHOW_ALL_JAR_EXECUTING_OUTPUT:
                        print(error.strip(), flush=True)
                    else:
                        error_content += error.strip() + os.linesep
            if exit_value != 0:
                sys.exit(
                    f"{os.linesep}{error_content}{os.linesep}Jar executed failed! Exit code: {exit_value}")

        await asyncio.gather(process_output(), process_error())


def read_properties(file_path: str) -> Dict[str, str]:
    properties = {}
    with open(file_path, "r") as f:
        line = f.readline()
        while line != "":
            line = line.strip()
            if not line.startswith("#") and "=" in line:
                divider_index = line.index("=")
                key = line[:divider_index].strip()
                value = line[divider_index + 1:].strip()
                if len(value) >= 2 and ((value.startswith("\"") and value.endswith("\"")) or (value.startswith("\'") and value.endswith("\'"))):
                    value = value[1:-1]
                properties[key] = value
            line = f.readline()
    return properties


def deploy_properties(properties: dict):
    # Force enable GlobalCostLogger
    properties["logger.GlobalCostLogger"] = "true"
    save_properties(EPOS_PROPERTIES_PATH, properties)


def save_properties(file_path: str, data: dict):
    with open(file_path, "w") as f:
        for key, value in data.items():
            key, value = str(key).strip(), str(value)
            if value != value.strip():
                if not (value.startswith("\"") and value.endswith("\"")) and not (value.startswith("\'") and value.endswith("\'")):
                    value = f"\"{value}\""
            f.write(f"{key} = {value}\r\n")
        os.fsync(f)


# Return [('modified properties', 'full properties')]
def modify_properties(template: Dict[str, str], params: Dict[str, List[str]]) -> List[Tuple[Dict[str, str], Dict[str, str]]]:
    result_list = []
    items_list = []
    for key, value in params.items():
        if not isinstance(value, list) and not isinstance(value, tuple) and not isinstance(value, set):
            sys.exit("Test params value must be list, tuple or set!")
        value_list = []
        for v in value:
            value_list.append((key, v))
        items_list.append(value_list)
    for items in product(*items_list):
        new_properties = deepcopy(template)
        modified_properties = {}
        for key, value in items:
            new_properties[key] = value
            modified_properties[key] = value
        result_list.append((modified_properties, new_properties))
    return result_list


# analyse_result_list: [('result dict', 'modified properties')]
def show_best_result(analyse_result_list: List[Tuple[dict, dict]]):
    best_result, best_modified = min(
        analyse_result_list, key=lambda x: x[0]["var"])
    print(f"Best output: {best_result['output']}")
    print(
        f"Best global cost:\n" +
        f"\tIteration: {best_result['iteration']}\n" +
        f"\tRun: {best_result['run']}\n" +
        f"\tVar: {best_result['var']}"
    )
    print("Best modified properties:")
    for key, value in sorted(best_modified.items()):
        print(f"\t{key} = {value}")


def append_results(result: dict, modified: dict):
    new_file = not os.path.isfile(RUN_RESULT_OUTPUT_CSV_FILE)
    with open(RUN_RESULT_OUTPUT_CSV_FILE, "a") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["Output", "Iteration", "Run", "Var", "Modified"])
        modified_content = ", ".join(
            [f"{k} = {v}" for k, v in sorted(modified.items())])
        writer.writerow([result['output'], result['iteration'],
                         result['run'], result['var'], modified_content])
        os.fsync(f)


def main():
    if SHOW_TEST_PARAMS:
        print("Testing params:")
        print(json.dumps(TEST_PARAMS, ensure_ascii=False, indent=4), end=os.linesep * 2)
    print("Reading properties template ... ...")
    template_properties = read_properties(EPOS_TEMPLATE_PROPERTIES_PATH)
    print("Generate properties list ... ...")
    properties_list = modify_properties(template_properties, TEST_PARAMS)
    print(f"Available properties amount: {len(properties_list)}")
    analyse_result_list = []
    print(os.linesep + "=" * 20 + " Executing " + "=" * 20 + os.linesep)
    try:
        for i, (modified, properties) in enumerate(properties_list):
            print(f"Testing params {i + 1}/{len(properties_list)}", end=os.linesep * 2)
            deploy_properties(properties)
            asyncio.run(execute_jar())
            analyse_result = run_analyse(modified)
            analyse_result_list.append((analyse_result, modified))
            append_results(analyse_result, modified)
            print(os.linesep + "=" * 50 + os.linesep)
    except BaseException as e:
        print(f"Executing error! {os.linesep}{e}{os.linesep}")
    if len(analyse_result_list) > 0:
        show_best_result(analyse_result_list)
    else:
        print(f"No result!{os.linesep}")


if __name__ == "__main__":
    main()
