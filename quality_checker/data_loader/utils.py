import json
from pathlib import Path
from typing import Union


def save_json(path: Union[Path, str], data: Union[dict, list], indent: int=4):
    with open(path, "w") as f:
        json.dump(data, f, indent=indent)


def load_json(path: Union[Path, str]) -> Union[dict, list]:
    with open(path, "r") as f:
        return json.load(f)
