#!/usr/bin/env python3
"""Export all Pydantic schemas from nomos-api as JSON Schema.
Usage: python scripts/export-schemas.py > schemas.json
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "nomos-api"))

from nomos_api import schemas
from pydantic import BaseModel


def export_all():
    result = {}
    for name in dir(schemas):
        obj = getattr(schemas, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, BaseModel)
            and obj is not BaseModel
            and obj.__module__ == schemas.__name__
        ):
            result[name] = obj.model_json_schema()
    return result


if __name__ == "__main__":
    print(json.dumps(export_all(), indent=2))
