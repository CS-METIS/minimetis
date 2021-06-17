import typing as t
from networkx import DiGraph
from reveal.typings import JSONType
from reveal.model import OVertex

def normalize_elt(elt: JSONType) -> JSONType:
    n_elt = {}
    elt["_label"] = f"{elt['@class']}({elt['@rid']})"
    for key, value in elt.items():
        n_elt[key.replace('@', '_')] = value
    return n_elt

def convert(js: JSONType) -> DiGraph:
    vertice: t.List[t.Dict[str, str]] = []
    edges: t.List[t.Dict[str, str]] = []
    for elt in js:
        if "in" in elt and "out" in elt:
            edges.append(normalize_elt(elt))
        else:
            vertice.append(normalize_elt(elt))

    graph = DiGraph()
    for vertex in vertice:
        graph.add_node(vertex["_rid"], **vertex)
    for edge in edges:
        graph.add_edge(edge["in"], edge["out"], **edge)
    return graph

