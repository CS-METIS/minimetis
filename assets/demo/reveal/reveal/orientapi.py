from dataclasses import dataclass, fields, field
import dataclasses
import io
from typing import (
    List,
    Optional,
    Type,
    Union,
    get_origin,
    get_args,
    Set,
    Any,
    Type,
    Dict,
)
import requests
from enum import Enum
import more_itertools as mit
from datetime import datetime, date
from reveal.typings import JSONType
from reveal.model import normalize_properties, OVertex, is_collection
from requests.models import HTTPBasicAuth
import json
import os
import urllib
from geojson.geometry import Geometry, Point, Polygon
from reveal.model import is_collection, owned_field
import sys


class OrientDBRequestStatus(Enum):
    SUCCESS = 0
    ERROR = 0


@dataclass
class OrientDBCommand:
    command: str
    language: str = "sql"


@dataclass
class OrientDBResult:
    status: OrientDBRequestStatus
    result: Optional[JSONType] = None
    error_message: Optional[str] = None


class OrientDBClient:
    def __init__(self) -> None:
        self.server_url: str = os.environ["ORIENTDB_URL"]
        self.user: str = os.environ["ORIENTDB_USER"]
        self.password: str = os.environ["ORIENTDB_PASSWORD"]

    def create_database(self, db_name: str) -> OrientDBResult:
        create_database_url = f"{self.server_url}/database/{db_name}/plocal"
        res = requests.post(
            create_database_url, auth=HTTPBasicAuth(self.user, self.password)
        )
        if 200 <= res.status_code < 300:
            return OrientDBResult(OrientDBRequestStatus.SUCCESS, result=res.json())
        error_msg = f"request {create_database_url} failed with status code {res.status_code}: {res.text}"
        return OrientDBResult(OrientDBRequestStatus.ERROR, error_message=error_msg)

    def batch(
        self,
        database: str,
        commands: List[OrientDBCommand],
        transaction: bool = False,
        chunks: int = 1000,
    ) -> OrientDBResult:
        batch_url = f"{self.server_url}/batch/{database}"
        commands_chunks = mit.chunked(commands, chunks)
        results = []
        for commands_chunk in commands_chunks:
            data = {"transation": transaction, "operations": []}
            for cmd in commands_chunk:
                data["operations"].append(
                    {"type": "cmd", "language": cmd.language, "command": cmd.command}
                )
            res = requests.post(
                batch_url, auth=HTTPBasicAuth(self.user, self.password), json=data
            )
            if not (200 <= res.status_code < 300):
                print(res.status_code, res.text)
                error_msg = f"request {batch_url} failed with status code {res.status_code}: {res.text}"
                return OrientDBResult(OrientDBRequestStatus.ERROR, error_msg)

            results.extend(res.json()["result"])
        return OrientDBResult(OrientDBRequestStatus.SUCCESS, result=results)

    def command(
        self,
        database: str,
        command: str,
        language: str = "sql",
        transaction: bool = False,
    ) -> OrientDBResult:
        return self.batch(
            database, [OrientDBCommand(command, language)], transaction, chunks=1
        )

    def get(self, database: str, classname: str, rid: str) -> OVertex:
        request = f"SELECT FROM {classname} WHERE @rid={rid}"
        res = self.command(database, request)
        if res.status != OrientDBRequestStatus.SUCCESS:
            raise ValueError(
                f"Failed to get {classname}({rid}) from database {database}: {res.error_message}"
            )
        if len(res.result) == 0:
            raise ValueError(
                f"{classname}({rid}) does not exist in database {database}"
            )
        if len(res.result) > 1:
            raise ValueError(
                f"{database} is inconsistent: {classname}({rid}) appears more than once"
            )
        data = res.result[0]
        return from_json(classname, data)

    def update(self, database: str, obj: OVertex) -> OrientDBResult:
        properties: List[str] = []
        for name, value in normalize_properties(obj).items():
            value_type = type(value)
            if value is None or value == "NULL":
                continue
            if name == "vertex_id":
                continue
            if (
                name.startswith("@")
                or name.startswith("in_")
                or name.startswith("out_")
            ):
                continue
            if isusbclass_safe(value_type, Geometry):
                geo_value = f"ST_GeomFromGeoJSON('{json.dumps(value)}')"
                properties.append(f"{name}={geo_value}")
            elif is_collection(value_type):
                continue
            elif isusbclass_safe(type(value), OVertex):
                continue
            # add properties values
            else:
                properties.append(f"{name}={value}")
                print(name, value_type, value)
        set_values = ", ".join(properties)
        update = f"UPDATE {obj.__class__.__name__} SET {set_values} WHERE vertex_id='{obj.vertex_id}'"
        return self.command(database=database, command=update)


def _optional_type(v: Type) -> Type:
    if get_origin(v) == Union:
        args = get_args(v)
        if args[1] == type(None):
            return args[0]
    else:
        return v


def from_json(classname: str, data: Dict[str, Any]) -> OVertex:
    clazz = str_to_class(classname)
    attributes = {}
    for f in fields(clazz):
        if is_collection(f.type):
            attributes[f.name] = None
        elif isusbclass_safe(f.type, OVertex):
            attributes[f.name] = None
        elif isusbclass_safe(f.type, Geometry):
            attributes[f.name] = to_geojson(data.get(f.name, None))
        else:
            attributes[f.name] = decode(f.type, data.get(f.name, None))
    return clazz(**attributes)


def is_geometry(v: Type) -> bool:
    try:
        return issubclass(_optional_type(v), Geometry)
    except TypeError:
        return False


def orient_type_name(type: Type) -> Optional[str]:
    type = _optional_type(type)
    if type == bool:
        return "BOOLEAN"
    if type == int:
        return "INTEGER"
    if type == float:
        return "FLOAT"
    if type == str or issubclass(type, io.TextIOBase):
        return "STRING"
    if type == datetime:
        return "DATE"
    if issubclass(type, Geometry):
        if hasattr(type, "__name__"):
            return f"EMBEDDED O{type.__name__}"
    return None




def extract_attributes(obj: object) -> str:
    attributes: List[str] = []
    for n, v in normalize_properties(obj).items():
        attributes.append(f"{n}={v}")
    return ", ".join(attributes)


@dataclass
class ImportCommands:
    vertex_id: str
    vertex_class: str
    upsert: Optional[str]
    edges: List[str]


def import_commands(obj: OVertex, existing_vertex: Set[str]) -> List[ImportCommands]:
    properties: List[str] = []
    edges: List[str] = []
    commands: List[ImportCommands] = []
    existing = obj.vertex_id in existing_vertex
    existing_vertex.add(obj.vertex_id)
    for name, value in normalize_properties(obj).items():
        # create the edges
        if issubclass(type(value), Geometry):
            geo_value = f"ST_GeomFromGeoJSON('{json.dumps(value)}')"
            properties.append(f"{name}={geo_value}")
        elif is_collection(type(value)):
            from_select = f"SELECT FROM {obj.__class__.__name__} WHERE vertex_id='{obj.vertex_id}'"
            if type(value) == list or type(value) == set:

                for item in value:
                    commands.extend(import_commands(item, existing_vertex))
                    to_select = f"SELECT FROM {item.__class__.__name__} WHERE vertex_id='{item.vertex_id}'"
                    edges.append(
                        f"CREATE EDGE {name} FROM ({from_select}) TO ({to_select}) SET name='{name}', from_class='{obj.__class__.__name__}', to_class='{item.__class__.__name__}'"
                    )
            if type(value) == dict:
                raise ValueError("a relation cannot be a dict")
        elif issubclass(type(value), OVertex):
            commands.extend(import_commands(value, existing_vertex))
            from_select = f"SELECT FROM {obj.__class__.__name__} WHERE vertex_id='{obj.vertex_id}'"
            to_select = f"SELECT FROM {value.__class__.__name__} WHERE vertex_id='{value.vertex_id}'"
            edges.append(
                f"CREATE EDGE {name} FROM ({from_select}) TO ({to_select}) SET name='{name}', from_class='{obj.__class__.__name__}', to_class='{value.__class__.__name__}'"
            )
        # add properties values
        else:
            properties.append(f"{name}={value}")
    if not existing:
        set_values = ", ".join(properties)
        upsert = f"UPDATE {obj.__class__.__name__} SET {set_values} UPSERT WHERE vertex_id='{obj.vertex_id}'"
        # upsert = f"INSERT INTO {obj.__class__.__name__} SET {set_values}"
        new_commands = [
            ImportCommands(obj.vertex_id, obj.__class__.__name__, upsert, edges)
        ]
        new_commands.extend(commands)
        return new_commands
    else:
        new_commands = [
            ImportCommands(obj.vertex_id, obj.__class__.__name__, None, edges)
        ]
        new_commands.extend(commands)
        return new_commands


def create_schema_commands(clazz: Any) -> List[str]:
    """Creates OrientDB commands from a class Hierarchy representing an ontologie"""
    raw_cmds = create_schema_commands_rec(clazz, set(), set())
    return [OrientDBCommand(cmd) for cmd in raw_cmds]


def create_schema_commands_rec(
    clazz: Any, node_classes: Set[Type], egdes: Set[str], class_type="V"
) -> List[str]:
    if not dataclasses.is_dataclass(clazz):
        raise ValueError("clazz argument must be a dataclass")
    if clazz in node_classes:
        return []
    node_classes.add(clazz)
    commands: List[str] = []
    if clazz.__base__ != object:
        commands.extend(create_schema_commands_rec(clazz.__base__, node_classes, egdes))

    fields = dataclasses.fields(clazz)
    classname = clazz.__name__
    if dataclasses.is_dataclass(clazz.__base__):
        class_type = clazz.__base__.__name__
    commands.append(f"CREATE CLASS {classname} extends {class_type}")
    for f in fields:
        if not owned_field(clazz, f):
            continue
        if is_geometry(f.type):
            type_name = orient_type_name(f.type)
            if type_name is not None:
                commands.append(f"CREATE PROPERTY {classname}.{f.name} {type_name}")
                for key, value in f.metadata.items():
                    if key == "unique":
                        commands.append(f"CREATE INDEX {classname}.{f.name} UNIQUE")
                    else:
                        commands.append(
                            f"ALTER PROPERTY {classname}.{f.name} {key} {value}"
                        )
                commands.append(
                    f"CREATE INDEX {classname}_{f.name} ON {classname}({f.name}) SPATIAL ENGINE LUCENE"
                )
        elif is_collection(f.type):
            if f.type.__origin__ == set or f.type.__origin__ == list:
                if f.name not in egdes:
                    egdes.add(f.name)
                    commands.append(f"CREATE CLASS {f.name} extends E")
                arg_type = f.type.__args__[0]
                commands.extend(
                    create_schema_commands_rec(arg_type, node_classes, egdes)
                )
        elif dataclasses.is_dataclass(f.type):
            if f.name not in egdes:
                egdes.add(f.name)
                commands.append(f"CREATE CLASS {f.name} extends E")
            commands.extend(create_schema_commands_rec(f.type, node_classes, egdes))
        else:
            type_name = orient_type_name(f.type)
            if type_name is not None:
                commands.append(f"CREATE PROPERTY {classname}.{f.name} {type_name}")
                for key, value in f.metadata.items():
                    if key == "unique":
                        commands.append(f"CREATE INDEX {classname}.{f.name} UNIQUE")
                    else:
                        commands.append(
                            f"ALTER PROPERTY {classname}.{f.name} {key} {value}"
                        )
    if clazz != OVertex:
        for c in clazz.__subclasses__():
            commands.extend(create_schema_commands_rec(c, node_classes, egdes))
    return commands


def isusbclass_safe(a_type: Type, clazz: Type) -> bool:
    try:
        return issubclass(a_type, clazz)
    except Exception:
        return False


def str_to_class(classname):
    # TODO improve to pass the model as parameter
    import dvf.model as model

    return getattr(sys.modules[model.__name__], classname)


def to_geojson(value: Optional[Dict[str, Any]]) -> Optional[Geometry]:
    if value is None:
        return None
    if ("@class" not in value) or ("coordinates" not in value):
        return None
    if value["@class"] == "OPoint":
        return Point(value["coordinates"])
    if value["@class"] == "OPolygon":
        return Polygon(value["coordinates"])
    return None


def decode(target_type: Type, value: Optional[str]) -> Any:
    if value is None:
        return None
    if target_type == int:
        return int(value)
    if target_type == float:
        return float(value)
    if target_type == datetime:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    if target_type == date:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    if is_geometry(value):
        return to_geojson(value)
    if issubclass(target_type, io.TextIOBase):
        return io.StringIO(value)
    return value


def encode(value: Any) -> str:
    if value is None:
        return 'NULL'
    value_type = _optional_type(type)
    if value_type == bool or type == int or type == float:
        return f'{value}'
    if value_type == str:
         return value
    if issubclass(value_type, io.TextIOBase):
        return value.getvalue()
    if value_type == datetime:
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if is_geometry(value):
        return f"ST_GeomFromGeoJSON('{json.dumps(value)}')"
    return None
