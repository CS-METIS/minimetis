import ipyvuetify as v
import pandas as pd
from ipyleaflet import Map, Marker
import shapely.geometry as sg
from reveal.orientapi import OrientDBClient
from geojson.geometry import Point


def create(database: str, lng: float, lat: float) -> v.VuetifyWidget:
    client = OrientDBClient()
    center = (lat, lng)
    synchronized = False
    def create_request(bounds):
        if bounds is None or not bounds:
            return  "select from Adresse"
        lat_i = 0
        lng_i = 1
        bb = sg.box(minx=bounds[0][lng_i], miny=bounds[0][lat_i], maxx=bounds[1][lng_i], maxy=bounds[1][lat_i])
        request = f"select from Adresse where ST_WITHIN(location,'{bb}') = true"
        return request

    # request = create_request(None)

    def create_markers(bounds):
        request = create_request(bounds)
        res = client.command(database, request)
        # visible_addresses = pd.DataFrame.from_dict(res.result)
        for adresse in res.result:
            coords = adresse["location"]["coordinates"]
            p = (coords[1], coords[0])
            marker = Marker(location=p, draggable=False)
            m.add_layer(marker)

    def on_bounds_change(evt):
        if synchronized or m.zoom > 12:
            print("synchro")
            create_markers(m.bounds)

    def recenter(widget, event, data):
        print("recenter")
        m.center = center
        m.zoom = 5
        
    def afficher(widget, event, data):
        print("afficher")
        create_markers(m.bounds)
        
        
    m = Map(center=center, zoom=6)
    m.observe(on_bounds_change, "bounds")
    m.layout.height = '800px'
    m.layout.width = '1600px'

    center_button = v.Btn(color='primary', class_='ma-2',children=['recentrer'])
    center_button.on_event('click', recenter)

    afficher_button = v.Btn(color='primary', class_='ma-2',children=['afficher'])
    afficher_button.on_event('click', afficher)

    buttons = v.Layout(class_="pa-2", children=[center_button, afficher_button])

   
    return v.Html(
        tag="div",
        class_="d-flex flex-row",
        children=[
            v.Html(tag="div", class_="d-flex flex-column", children=[buttons, m]),
        ],
    )
    # return v.Container(children=[
    #     buttons,
    #     m,
    # ])
    # display(buttons)
    # display(m)