#!/usr/bin/env python3

import os
import time

import config
from epos_runner import *
from epos_runner.log import logger


# Custom log location before import epos_runner
# os.putenv("EPOS_RUNNER_LOG_PATH", "epos-runner.log")


def main():
    logger.info("EPOS Runner V5.2 Ultra")
    if config.PARALLEL_SIZE < 1:
        raise ValueError("EXECUTOR_AMOUNT must >= 1!")
    if len(config.PARAMS) <= 0:
        raise ValueError("No params available!")
    logger.info(f"Parallel size: {config.PARALLEL_SIZE}")
    logger.info(f"Output CSV path: {config.REPORT_PATH}")
    if config.PRINT_PARAMS:
        Report.print_params(config.PARAMS)
    template = Properties.load_file(config.EPOS_PROPERTIES_TEMPLATE_PATH)
    logger.info("=" * 50)
    start_second = time.time()
    executor = ParallerExecutor(config.WORKSPACE_PATH, config.REPORT_PATH, config.PARALLEL_SIZE, template, config.PARAMS, config.ANALYZER)
    logger.info(f"Executor dir: {executor.executor_dir}")
    reports = executor.run()
    end_second = time.time()
    logger.info("Time cost: %.2f minutes" % ((end_second - start_second) / 60))
    logger.info("=" * 50)
    if config.PRINT_BEST_RESULT:
        Report.print_best_report(reports, config.ANALYZER)
    logger.info(f"{os.linesep}Done")


if __name__ == '__main__':
    try:
        main()
    except BaseException as e:
        logger.exception(e)
        raise e
