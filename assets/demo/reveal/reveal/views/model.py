from ipycytoscape import CytoscapeWidget
import typing as t
import ipyvuetify as v
from reveal.ontologies import create_schema_graph
from reveal.model import OVertex

def create(model: t.Type) -> v.VuetifyWidget:
    G = create_schema_graph(model)
    cyto = CytoscapeWidget()
    cyto.graph.add_graph_from_networkx(G)
    cyto.set_style(
        [
            {
                "selector": "node",
                "style": {
                    "label": "data(id)",
                    "font-family": "helvetica",
                    "font-size": "15px",
                    "color": "dimgrey",
                    "background-color": "#11479e",
                    "shape":"roundrectangle"
                },
            },
            {
                "selector": f"node[id='{model.__name__}']",
                "style": {
                    "background-color": "darkorchid",
                },
            },
            {
                "selector": "edge",
                "style": {
                    "label": "data(type)",
                    "font-family": "helvetica",
                    "font-size": "10px",
                    "line-color": "#9dbaea",
                    "width": 1.5,
                    "color": "#11479e",
                    "shape":"roundrectangle",
                    "target-arrow-shape": "diamond",
                    "target-arrow-color": "#9dbaea",
                    "curve-style": "bezier"
                },
            },
            {
                "selector": "edge[type='extend']",
                "style": {
                    "label": "data(type)",
                    "color": "lightgray",
                    "line-color": "lightgray",
                    "line-style": "dashed",
                    "target-arrow-shape": "triangle",
                    "target-arrow-color": "lightgray",
                    "curve-style": "bezier"
                },
            },

        ]
    )
    cyto.layout.height = '700px'
    cyto.layout.width = '99%'

    def on_menu_click(widget, event, data):
        idx = items.index(widget)
        l = items[idx].children[0].children[0]
        print(type(l), l)
        cyto.set_layout(name=l)

    graph_layouts = [
        "cola",
        "dagre",
        "random",
        "grid",
        "circle",
        "concentric",
        "breadthfirst",
        "cose"
    ]

    items = [v.ListItem(children=[
        v.ListItemTitle(children=[
            f'{buttons}'])]) 
            for buttons in graph_layouts]

    for item in items:
        item.on_event('click', on_menu_click)

    menu = v.Menu(offset_y=True,
        v_slots=[{
            'name': 'activator',
            'variable': 'menuData',
            'children': v.Btn(v_on='menuData.on', class_='ma-2', color='primary', children=[
                'choose layout', 
                v.Icon(right=True, children=[
                    'mdi-menu-down'
                ])
            ]),
        }]
        , 
        children=[
            v.List(children=items)
        ]
    )


    buttons = v.Layout(children=[
        menu
    ])
    return v.Container(children=[
        buttons,
        cyto,
    ])