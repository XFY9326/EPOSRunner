import os
from collections import OrderedDict
from typing import Optional, Tuple, Dict


class Properties:
    @staticmethod
    def _read_line(line: str) -> Optional[Tuple[str, str]]:
        line = line.strip()
        if not line.startswith("#") and "=" in line:
            divider_index = line.index("=")
            key = line[:divider_index].strip()
            value = line[divider_index + 1:].strip()
            if len(value) >= 2 and ((value.startswith("\"") and value.endswith("\"")) or (value.startswith("\'") and value.endswith("\'"))):
                value = value[1:-1]
            return key, value
        return None

    @staticmethod
    def _write_line(key: str, value: str) -> str:
        key, value = str(key).strip(), str(value)
        if value != value.strip():
            value = f"\"{value}\""
        return f"{key} = {value}{os.linesep}"

    @staticmethod
    def load(data: str) -> Dict[str, str]:
        result = OrderedDict()
        for line in data.splitlines(keepends=False):
            line_data = Properties._read_line(line)
            if line_data is not None:
                key, value = line_data
                result[key] = value
        return result

    @staticmethod
    def save(data: dict) -> str:
        result = ''
        for key, value in data.items():
            result += Properties._write_line(key, value)
        return result

    @staticmethod
    def load_file(file_path: str) -> Dict[str, str]:
        result = OrderedDict()
        with open(file_path, "r") as f:
            line = f.readline()
            while line != '':
                line_data = Properties._read_line(line)
                if line_data is not None:
                    key, value = line_data
                    result[key] = value
                line = f.readline()
        return result

    @staticmethod
    def save_file(file_path: str, data: dict, sync: bool = True):
        with open(file_path, "w") as f:
            for key, value in data.items():
                f.write(Properties._write_line(key, value))
            if sync:
                os.fsync(f)
