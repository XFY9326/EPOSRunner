import logging
import os

logger = logging.getLogger("EPOS_Runner")


def _init_logger():
    logger.setLevel(logging.DEBUG)
    stdout = logging.StreamHandler()
    stdout.setLevel(logging.DEBUG)
    stdout.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(stdout)
    log_path = os.getenv("EPOS_RUNNER_LOG_PATH")
    if log_path is None or log_path.strip() == "":
        log_path = "epos-runner.log"
    file = logging.FileHandler(log_path)
    file.setLevel(logging.DEBUG)
    file.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(file)


_init_logger()
