from typing import Any, List, Set, Type
from dataclasses import Field
import dataclasses
import networkx as nx
from geojson.geometry import Geometry
from reveal.typings import NodeType
from reveal.orientapi import orient_type_name, OrientDBCommand, is_geometry
from reveal.model import is_collection, owned_field

def create_schema_graph(clazz: Any) -> nx.DiGraph:
    graph = nx.DiGraph()
    create_schema_graph_rec(clazz, set(), graph)
    return graph
    

def create_schema_graph_rec(clazz: Any, nodes: Set[Any], graph: nx.DiGraph):
    if not dataclasses.is_dataclass(clazz):
        raise ValueError("clazz argument must be a dataclass")
    if clazz in nodes:
        return []
    nodes.add(clazz)

    classname = clazz.__name__
    fields = dataclasses.fields(clazz)
    node : NodeType = (classname, {})
    for f in fields:
        if not owned_field(clazz, f):
            continue
        if is_collection(f.type):
            if f.type.__origin__ == set or f.type.__origin__ == list:
                arg_type = f.type.__args__[0]
            elif f.type.__origin__ == dict:
                arg_type = f.type.__args__[1]
            create_schema_graph_rec(arg_type, nodes, graph)
            graph.add_edge(classname, arg_type.__name__, type="many")
        elif dataclasses.is_dataclass(f.type):
            arg_type = f.type
            create_schema_graph_rec(arg_type, nodes, graph)
            graph.add_edge(classname, arg_type.__name__, type="one")
        else:
            type_name = orient_type_name(f.type)
            if type_name is not None:
                node[1][f.name]=type_name
    graph.add_nodes_from([node])

    for c in clazz.__subclasses__():
        create_schema_graph_rec(c, nodes, graph)
        graph.add_edge(c.__name__, classname, type="extend")

