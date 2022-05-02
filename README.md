# EPOSRunner

Multiprocess parameter searcher for [epournaras/EPOS](https://github.com/epournaras/EPOS)

## Features

- Multiprocess
- Handle error automatically
- Support all parameters in propreties
- Fewer dependencies
- Log modified parameters for each propreties file
- Log all outputs and errors
- Good code quality with type hint

## Requirements

- JRE or JDK (for EPOS)
- Python 3.7 or above (for asyncio)

Attention: This scirpt is tested on python 3.8.

## Built-in EPOS Version

- IEPOS-Tutorial.jar: 0.0.3

## Usage

1. Check [epournaras/EPOS](https://github.com/epournaras/EPOS) website for the latest version.
2. Use the latest EPOS.jar instead of workspace/IEPOS-Tutorial.jar.
3. Replace your dataset and epos.template.properties under the workspace folder.
4. Change parameter that you want to test in config.py
5. Write your own Analyzer implementing the AbstractAnalyzer
6. Run epos.py

Attention: Due to EPOS output security concerns, the minimum processing interval is one second.  
Reason: EPOS output folder name is depend on seconds

## Output

- result.csv: All reported data
- epos-runner.log: This python script's log
- workspace/executor/\<timestamp\>/log/\<task_number\>.log: EPOS log
- workspace/executor/\<timestamp\>/properties/\<task_number\>.properties: EPOS properties

## Customized

In config.py

```python
# Executor parallel size
PARALLEL_SIZE = 4
# Show params before all tasks start
PRINT_PARAMS = True
# Show best result after all task finished
PRINT_BEST_RESULT = True
```

```python
from typing import Dict, List
from epos_runner.analyzer import AbstractAnalyzer


class CustomAnalyzer(AbstractAnalyzer):
    # Force set properties before run EPOS
    def required_propreties(self, properties: Dict[str, str]) -> Dict[str, str]:
        return properties

    # This returned dict will be converted and exported to a csv file
    def generate_report(self, output_dir: str) -> dict:
        pass

    # Return best report dict index
    def best_result(self, reports: List[dict]) -> int:
        pass
```

By implementing the AbstractAnalyzer, you can change the results that need to be analyzed and reported.  
Demo reported data is the minium variance in the global cost.

## How it works

1. Generate all possible parameter combinations.
2. Execute command to run jar in multiple subprocesses using asyncio.

## Single thread version

Single thread version is just for learning and test:

```
old/epos_SingleThread.py
```

## License

```
EPOSRunner
Copyright (C) 2022  XFY9326

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
```
