from ipycytoscape import CytoscapeWidget
import ipycytoscape.cytoscape as cy
import ipywidgets as widget
from traitlets import Instance
import networkx as nx
import json
import typing as t
import ipyvuetify as v
from reveal.graph import convert
from reveal.model import OVertex
from reveal.orientapi import OrientDBClient, OrientDBRequestStatus, from_json
from pprint import pformat
from IPython.display import clear_output, display
from ipywidgets import widget_serialization, Output


class GrahView(v.Html):
    def __init__(
        self,
        database: str,
        colors: t.Dict[str, str],
        element_id: t.Optional[str],
        hidden_keys: t.List[str], 
        frozen_keys: t.List[str]
    ) -> None:
        self.database = database
        self.colors = colors
        self.element_id = element_id
        self.hidden_keys = hidden_keys
        self.frozen_keys = frozen_keys
        self.cyto = CytoscapeWidget()
        self.cyto.layout.height = "700px"
        self.cyto.layout.width = "900px"
        self.cyto.set_layout(name="cola", nodeSpacing=35)
        self.update_graph(element_id)

        def on_menu_layout_click(widget, event, data):
            idx = items.index(widget)
            l = items[idx].children[0].children[0]
            self.cyto.set_layout(name=l, nodeSpacing=40)


        layouts = [
            "cola",
            "dagre",
            "random",
            "grid",
            "circle",
            "concentric",
            "breadthfirst",
            "cose",
        ]

        items = [
            v.ListItem(children=[v.ListItemTitle(children=[f"{buttons}"])])
            for buttons in layouts
        ]

        for item in items:
            item.on_event("click", on_menu_layout_click)

        layout_menu = v.Menu(
            offset_y=True,
            v_slots=[
                {
                    "name": "activator",
                    "variable": "menuData",
                    "children": v.Btn(
                        v_on="menuData.on",
                        class_="ma-2",
                        color="primary",
                        children=[
                            "choisir le layout",
                            v.Icon(right=True, children=["mdi-menu-down"]),
                        ],
                    ),
                }
            ],
            children=[v.List(children=items)],
        )


        def fit_graph(*args):
            self.cyto.relayout()

        fit_button = v.Btn(color='primary', class_='ma-2',children=['fit'])
        fit_button.on_event('click', fit_graph)


        self.buttons = v.Layout(children=[layout_menu, fit_button])

        self.property_view = widget.Output()
        def on_node_clicked(node):
            with self.property_view:
                self.property_view.clear_output()
                display(self.create_json_view(node))

        self.cyto.on("node", "click", on_node_clicked)

        super().__init__(
            tag="div",
            class_="d-flex flex-row",
            children=[
                v.Html(
                    tag="div",
                    class_="d-flex flex-column",
                    children=[
                        self.buttons,
                        v.Layout(children=[self.cyto, self.property_view]),
                    ],
                ),
            ],
        )


    def create_style(self, colors: t.Dict[str, str]) -> t.Dict[str, t.Any]:
        style = [
            {
                "selector": "node",
                "style": {
                    "label": "data(_label)",
                    "font-family": "helvetica",
                    "font-size": "10px",
                    "color": "dimgrey",
                    "background-color": "#11479e",
                    "shape": "roundrectangle",
                },
            },
            {
                "selector": f"node[id='{self.element_id}']",
                "style": {
                    "background-color": "darkorchid",
                },
            },
            {
                "selector": "edge",
                "style": {
                    # "label": "data(_class)",
                    "font-family": "helvetica",
                    "font-size": "8px",
                    "line-color": "#9dbaea",
                    "width": 1.5,
                    "color": "#11479e",
                    "shape": "roundrectangle",
                    "target-arrow-shape": "diamond",
                    "target-arrow-color": "#9dbaea",
                    "curve-style": "bezier",
                },
            },
        ]
        for cl, co in colors.items():
            style.append(
                {
                    "selector": f"node[_class='{cl}']",
                    "style": {
                        "background-color": f"{co}",
                    },
                }
            )
        return style

    def clear_graphe(self):
        self.cyto.graph.edges.clear()
        self.cyto.graph.nodes.clear()
        self.cyto.graph._adj.clear()

    def update_graph(self, element_id: str):
        self.element_id = element_id
        self.clear_graphe()
        if element_id is None or element_id == "":
            return
        client = OrientDBClient()
        res = client.command(self.database, f"TRAVERSE * FROM {element_id}")
        if res.status != OrientDBRequestStatus.SUCCESS:
            return
        G = convert(res.result)
        self.cyto.graph.add_graph_from_networkx(G)
        self.update_style(self.colors)


    def update_style(self, colors: t.Dict[str, str]):
        self.colors = colors
        self.cyto.set_style(self.create_style(colors))


    def create_json_view(self, node_data: t.Dict[str, t.Any]) -> v.VuetifyWidget:
        hidden_keys = self.hidden_keys
        frozen_keys = self.frozen_keys
        children = []
        textfields = {}
        for key, value in node_data["data"].items():
            if key in hidden_keys:
                continue
            if key.startswith("out_") or key.startswith("in_"):
                continue
            if type(value) == str:
                if key in frozen_keys:
                    tf =  v.TextField(dense=True, readonly=True, label=key, v_model=str(value))
                    children.append(tf)
                else:
                    tf =  v.TextField(dense=True, label=key, v_model=str(value))
                    children.append(tf)
                    textfields[key] = tf
            if type(value) == dict:
                l2_children = []
                for key2, value2 in value.items():
                    if (key2 in hidden_keys) or (key in hidden_keys):
                        continue
                    if (key2 in frozen_keys) or (key in frozen_keys):
                        l2_children.append(v.TextField(dense=True, readonly=True, label=f"{key}.{key2}", v_model=str(value2)))
                    else:
                        l2_children.append(v.TextField(dense=True, label=f"{key}.{key2}", v_model=str(value2)))
                children.append(v.Container(children=l2_children))
        update_button = v.Btn(
            class_="ma-2",
            color="primary",
            children=[v.Icon(right=False, children=["mdi-filter"]), "Mettre à jour"],
        )

        def update(*args):
            client = OrientDBClient()
            node_id = node_data["data"]["_rid"]
            vertex = client.get(self.database, node_data["data"]["_class"], node_id)
            vertex_data = vertex.__dict__
            for key, _ in node_data["data"].items():
                if key in vertex_data and key in textfields:
                    vertex_data[key]=textfields[key].v_model
            new_vertex = from_json(node_data["data"]["_class"], vertex_data)
            res = client.update(self.database, new_vertex)
            if res.status != OrientDBRequestStatus.SUCCESS:
                raise ValueError(f"Error updating {new_vertex}")

        update_button.on_event("click", update)

        children.append(update_button)
        container = v.Container(children=children)
        return container

def create(
    database: str,
    elemet_id: str,
    colors: t.Dict[str, str],
    hidden_keys: t.List[str], 
    frozen_keys: t.List[str]
) -> v.VuetifyWidget:
    return GrahView(
        database=database,
        element_id=elemet_id,
        colors=colors,
        hidden_keys=hidden_keys,
        frozen_keys=frozen_keys
    )
