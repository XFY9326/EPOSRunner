import asyncio
import os
import time
from copy import deepcopy
from itertools import product
from typing import Dict, List, Tuple, Any, Optional

from epos_runner import AbstractAnalyzer
from epos_runner.epos_files import EPOSFolder
from epos_runner.log import logger
from epos_runner.properties import Properties
from epos_runner.report import Report


class ParallerExecutor:
    EPOS_EXECUTOR_DIR = "executor"
    EPOS_EXECUTOR_PROPERTIES_DIR = "properties"
    EPOS_EXECUTOR_LOG_DIR = "log"
    _EPOS_JAR_PATH = "IEPOS-Tutorial.jar"
    # EPOS output folder name is depend on seconds
    _MIN_EXECUTE_INTERVAL_SECOND = 1

    # Return ('full properties list', 'modified properties list')
    @staticmethod
    def _generate_properties(template: Dict[str, Any], params: Dict[str, List[Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        items_list = []
        for key, value in params.items():
            if not isinstance(value, list) and not isinstance(value, tuple) and not isinstance(value, set):
                raise ValueError("Params value must be list, tuple or set!")
            items_list.append([(key, v) for v in value])
        new_properties_list = []
        modified_properties_list = []
        for items in product(*items_list):
            new_properties = deepcopy(template)
            modified_properties = {}
            for key, value in items:
                new_properties[key] = value
                modified_properties[key] = value
            new_properties_list.append(new_properties)
            modified_properties_list.append(modified_properties)
        return new_properties_list, modified_properties_list

    @staticmethod
    def _validate_workspace(workspace_path: str) -> str:
        if not os.path.isfile(os.path.join(workspace_path, ParallerExecutor._EPOS_JAR_PATH)):
            raise ValueError(f"Can't find '{ParallerExecutor._EPOS_JAR_PATH}' in workspace '{workspace_path}'")
        datasets_path = os.path.join(workspace_path, EPOSFolder.DATASETS_DIR)
        if not os.path.isdir(datasets_path):
            raise ValueError(f"Can't find '{EPOSFolder.DATASETS_DIR}' in workspace '{workspace_path}'")
        if len([i for i in os.listdir(datasets_path) if os.path.isdir(os.path.join(datasets_path, i))]) == 0:
            raise ValueError(f"Can't find any datasets in workspace '{workspace_path}'")
        if not os.path.isdir(os.path.join(workspace_path, EPOSFolder.CONF_DIR)):
            raise ValueError(f"Can't find '{EPOSFolder.CONF_DIR}' in workspace '{workspace_path}'")
        return workspace_path

    def __init__(self, workspace_dir: str, report_path: str, parallel_size: int, template: Dict[str, Any], params: Dict[str, List[Any]], analyzer: AbstractAnalyzer):
        self.workspace_dir = ParallerExecutor._validate_workspace(workspace_dir)
        self.report_path = report_path
        self.executor_amount = parallel_size
        self.analyzer = analyzer
        self.executor_dir = os.path.join(workspace_dir, ParallerExecutor.EPOS_EXECUTOR_DIR, str(int(time.time())))
        self.executor_properties_path = os.path.join(self.executor_dir, self.EPOS_EXECUTOR_PROPERTIES_DIR)
        self.executor_log_path = os.path.join(self.executor_dir, self.EPOS_EXECUTOR_LOG_DIR)
        self.properties_list, self.modified_value_list = self._generate_properties(template, params)
        self._task_name_list = self._init_environment()
        self._task_counter = 0
        self._last_execute_time = 0
        self._total_tasks_amount = len(self._task_name_list)

    # Return [(properties name, log name, modified values)]
    def _init_environment(self) -> List[Tuple[str, str, dict]]:
        if not os.path.isdir(self.executor_properties_path):
            os.makedirs(self.executor_properties_path)
        if not os.path.isdir(self.executor_log_path):
            os.makedirs(self.executor_log_path)
        result = [(f"{i}.properties", f"{i}.log", self.modified_value_list[i]) for i in range(len(self.properties_list))]
        for i, properties in enumerate(self.properties_list):
            properties = self.analyzer.required_propreties(properties)
            # Force use LogLevel.SEVERE
            properties["logLevel"] = "SEVERE"
            properties_path = os.path.join(self.executor_properties_path, result[i][0])
            Properties.save_file(properties_path, properties)
        return result

    # Return report dict
    async def _execute_jar(self,
                           execute_lock: asyncio.Lock, print_lock: asyncio.Lock, report_lock: asyncio.Lock, execute_semaphore: asyncio.Semaphore,
                           jar_path: str, properties_name: str, log_name: str, modified_values: dict) -> Optional[dict]:
        output_dir = None
        properties_path = os.path.join(self.executor_properties_path, properties_name)
        log_path = os.path.join(self.executor_log_path, log_name)
        cmd = ["java", "-jar", jar_path, properties_path]
        async with execute_semaphore:
            await execute_lock.acquire()
            execute_time_diff = time.time() - self._last_execute_time
            if execute_time_diff < ParallerExecutor._MIN_EXECUTE_INTERVAL_SECOND:
                await asyncio.sleep(execute_time_diff)
            self._last_execute_time = start_second = time.time()
            with open(log_path, "w") as log_file:
                process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, cwd=self.workspace_dir)
                config_start = False
                while True:
                    line = await process.stdout.readline()
                    if line == b'':
                        break
                    if line:
                        line_str = line.decode().strip()
                        # Write log
                        log_file.write(line_str + os.linesep)
                        log_file.flush()
                        # Read output dir
                        if output_dir is None:
                            if line_str.startswith("CONFIGURATION"):
                                config_start = True
                            elif config_start and line_str.startswith("output") and "=" in line_str:
                                output_dir = line_str[line_str.index("=") + 1:].strip()
                                execute_lock.release()
                exit_value = await process.wait()
                if exit_value != 0:
                    logger.info(f"Task error! Properties: {properties_name}  Log: {log_name}")
            end_second = time.time()
        async with print_lock:
            self._task_counter += 1
            logger.info(f"Task: {self._task_counter}/{self._total_tasks_amount} finished in %.2fs" % (end_second - start_second))
        if output_dir is not None and os.path.isdir(output_dir) and exit_value == 0:
            bundled_report = Report.generate_bundled_report(output_dir, modified_values, self.analyzer)
            async with report_lock:
                Report.append_bundled_report(self.report_path, bundled_report)
            return bundled_report
        return None

    async def _run(self) -> List[dict]:
        execute_lock = asyncio.Lock()
        print_lock = asyncio.Lock()
        report_lock = asyncio.Lock()
        execute_semaphore = asyncio.Semaphore(self.executor_amount)
        tasks = []
        jar_path = os.path.join(self.workspace_dir, ParallerExecutor._EPOS_JAR_PATH)
        for properties_name, log_name, modified_values in self._task_name_list:
            task = self._execute_jar(
                execute_lock, print_lock, report_lock, execute_semaphore,
                jar_path, properties_name, log_name, modified_values
            )
            tasks.append(task)
        logger.info(f"Total tasks: {len(tasks)}")
        logger.info(f"Execution start!")
        # noinspection PyTypeChecker
        bundled_reports: List[Optional[dict]] = await asyncio.gather(*tasks)
        success_bundled_reports: List[dict] = [i for i in bundled_reports if i is not None]
        failed_task_amount = len(tasks) - len(success_bundled_reports)
        if failed_task_amount > 0:
            logger.warning(f"{failed_task_amount} tasks failed!")
        logger.info(f"All tasks executed!")
        return success_bundled_reports

    # Return [{"output": "", "modified": {}, "report": ""}]
    def run(self) -> List[dict]:
        return asyncio.run(self._run())
