from dataclasses import dataclass, field, Field
from datetime import datetime, date
from typing import Any, Dict, Optional, Type
import numpy as np
from geojson.geometry import Geometry

@dataclass(eq=False, frozen=True)
class OVertex:
    vertex_id: str = field(metadata={"unique": True, "mandatory": True, "notnull": True})

    def __hash__(self) -> int:
        return hash(self.vertex_id)

def normalize_properties(v: OVertex) -> Dict[str, Any]:
    properties: Dict[str, Any] = {}
    for name, value in vars(v).items():
        if type(value) == int and value < 0:
            properties[name] = "NULL"
        elif type(value) == float and np.isnan(value):
            properties[name] = "NULL"
        elif type(value) == str and value == "nan":
            properties[name] = "NULL"
        elif value is None:
            properties[name] = "NULL"
        elif type(value) == str:
            properties[name] = f'"{value}"'
        elif type(value) == date:
            properties[name] = f"DATE('{value.strftime('%Y-%m-%d')}')"
        elif type(value) == datetime:
            properties[name] = f"DATE('{value.strftime('%Y-%m-%d %H:%M:%S')}')"
        else:
            properties[name] = value
    return properties

def is_collection(type: Type) -> bool:
    if not hasattr(type, "__origin__"):
        return type == list or type == dict or type == set
    origin = type.__origin__
    return origin == list or origin == dict or origin == set

def owned_field(clazz: Any, field: Field) -> bool:
    if "__annotations__" not in clazz.__dict__:
        return False
    if field.name in clazz.__dict__["__annotations__"]:
        return True
    return False
