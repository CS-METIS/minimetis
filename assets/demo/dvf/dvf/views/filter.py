import ipyvuetify as v
import ipyleaflet as leaf
import typing as t
import datetime as dt
import pandas as pd
import shapely.geometry as geos
from reveal.views.datepicker import DatePicker
from reveal.orientapi import OrientDBClient


class FilterWidget(v.Html):
    def __init__(self, database: str, on_data_loaded: t.Callable[[pd.DataFrame], None], max_displayable_elements: int):
        self.on_data_loaded = on_data_loaded
        self.max_displayable_elements = None
        self.database = database
        self.orient_client = OrientDBClient()
        self.data: pd.DataFrame = None

        self.marker_cluster = None
        self.bounds = None
        self.from_datepicker = DatePicker(label="Début de période", v_model="")
        self.to_datepicker = DatePicker(label="Fin de période", v_model="")
        self.code_postal_textfield = v.TextField(label="Code postal", v_model="")
        self.commune_textfield = v.TextField(label="Commune", v_model="")
        self. valeur_min_textfield = v.TextField(label="Valeur foncière min", v_model="")
        self.valeur_max_textfield = v.TextField(label="Valeur foncière max", v_model="")
        close_snack_btn = v.Btn(color='pink', text=True, children=['close'])
        self.snackbar = v.Snackbar(
            v_model="",
            children=[
                "La requête demandée comporte trop d'élements. Veuillez affiner les filtres",
                close_snack_btn
            ],
        )
        def close_snackbar(*args):
            self.snackbar.v_model=""

        close_snack_btn.on_event("click", close_snackbar)

        self.appliquer = v.Btn(
            class_="ma-2",
            color="primary",
            children=[v.Icon(right=False, children=["mdi-filter"]), "Appliquer le filtre"],
        )

        def toggleLoading():
            self.appliquer.loading = not self.appliquer.loading
            self.appliquer.disabled = self.appliquer.loading

        lng = 2.213749
        lat = 46.227638
        self.map_widget = leaf.Map(
            center=(lat, lng),
            zoom=6,
            layout={"width": "900px", "height": "700px", "z-index": -1},
        )
        draw_control = leaf.DrawControl()
        draw_control.polyline = {}
        draw_control.polygon = {}
        draw_control.circle = {}
        draw_control.circlemarker = {}
        draw_control.rectangle = {"shapeOptions": {"color": "#fca45d", "fillOpacity": 0.0}}

        def handle_draw(dc, action, geo_json):
            if action == "created":
                shape = geos.shape(geo_json["geometry"])
                self.bounds = shape.bounds
            elif action == "deleted":
                self.bounds = None

        draw_control.on_draw(handle_draw)
        self.map_widget.add_control(draw_control)


        self.map_widget.add_control(
            leaf.SearchControl(
                position="topleft",
                url="https://nominatim.openstreetmap.org/search.php?format=json&q={s}",
                jsonp_param="json_callback",
                property_name="display_name",
                property_loc=["lat", "lon"],
                zoom=10,
            )
        )

        def attributes(link, attrs):
            return ",".join([f"first(out('{link}').{attr}) as {attr}" for attr in attrs])

        def create_where_clause():
            from_date_str = self.from_datepicker.v_model
            to_date_str = self.to_datepicker.v_model
            predicates = []
            try:
                from_date = dt.datetime.strptime(from_date_str, "%Y-%m-%d")
                to_date = dt.datetime.strptime(to_date_str, "%Y-%m-%d")
                predicates.append(f"(date between '{from_date}' and '{to_date}')")
            except ValueError:
                ...
            code_postal = self.code_postal_textfield.v_model
            if code_postal:
                predicates.append(f"(code_postal = '{code_postal}')")
            try:
                valeur_min = int(self.valeur_min_textfield.v_model)
                predicates.append(f"(valeur_fonciere > {valeur_min})")
            except (ValueError, TypeError):
                ...
            try:
                valeur_max = int(self.valeur_max_textfield.v_model)
                predicates.append(f"(valeur_fonciere < {valeur_max})")
            except (ValueError, TypeError):
                ...

            commune = self.commune_textfield.v_model
            if commune:
                predicates.append(f"(commune = '{commune}')")

            if self.bounds is not None:
                bb = geos.box(*self.bounds)
                predicates.append((f"(ST_WITHIN(location,'{bb}') = true)"))

            if not predicates:
                return ""
            return f' where {" and ".join(predicates)}'

        def create_markers():
            markers = []
            for row in self.data.iterrows():
                try:
                    coord = row[1]["location"]["coordinates"]
                    lng = coord[0]
                    lat = coord[1]
                    if lng == -180 and lat == -90:
                        continue
                    p = (lat, lng)
                    marker = leaf.Marker(
                            icon=leaf.AwesomeIcon(
                                name="location", marker_color="green", icon_color="darkgreen"
                            ),
                            location=p,
                            draggable=False
                    )
                    markers.append(marker)
                except TypeError:
                    continue
            if self.marker_cluster is not None:
                self.map_widget.remove_layer(self.marker_cluster)
            self.marker_cluster = leaf.MarkerCluster(markers=markers)
            self.map_widget.add_layer(self.marker_cluster)

        def apply_filter(*args):
            toggleLoading()
            try:
                attrs = [
                    "no_voie",
                    "type_de_voie",
                    "voie",
                    "code_postal",
                    "commune",
                    "departement",
                    "location",
                ]
                where_clause = create_where_clause()
                count_request = f"SELECT COUNT(*) FROM (SELECT @rid, first(in('dispositions_de_mutation').date) as date ,valeur_fonciere, first(in('dispositions_de_mutation').nature_mutation) as nature_mutation, {attributes('adresse_de_disposition', attrs)} from Disposition){where_clause}"
                res = self.orient_client.command(database, count_request)
                count = int(res.result[0]["COUNT(*)"])
                if count > max_displayable_elements:
                    self.snackbar.v_model = "snackbar = true"
                    toggleLoading()
                    return

                request = f"SELECT FROM (SELECT @rid, first(in('dispositions_de_mutation').date) as date ,valeur_fonciere, first(in('dispositions_de_mutation').nature_mutation) as nature_mutation, {attributes('adresse_de_disposition', attrs)} from Disposition){where_clause}"
                res = self.orient_client.command(database, request)
                self.data = pd.DataFrame.from_dict(res.result)
                self.data.set_index(["@rid"], drop=True, inplace=True)
            except KeyError:
               self.data = pd.DataFrame()
            if self.on_data_loaded is not None:
                self.on_data_loaded(self.data)
                create_markers()
            toggleLoading()

        self.appliquer.on_event("click", apply_filter)

        super().__init__(
            tag="div",
            class_="d-flex flex-row",
            children=[
                v.Html(
                    tag="div",
                    class_="d-flex flex-column",
                    children=[v.Layout(children=[self.map_widget])],
                ),
                v.Html(
                    tag="div",
                    class_="d-flex flex-column ml-10",
                    children=[
                        v.Layout(
                            children=[
                                self.from_datepicker,
                                self.to_datepicker,
                            ]
                        ),
                        self.code_postal_textfield,
                        self.commune_textfield,
                        v.Layout(
                            children=[
                                self.valeur_min_textfield,
                                v.Spacer(),
                                self.valeur_max_textfield,
                            ]
                        ),
                        v.Layout(
                            class_="align-end",
                            children=[self.appliquer, self.snackbar]),
                    ],
                ),
            ],
        )
        self.snackbar.v_model = ""

    def center_on(self, node_id, zoom_level: int):
        print(self.data.head())
        coords = self.data.loc[node_id]["location"]["coordinates"]
        print(coords)
        self.map_widget.center = (coords[1], coords[0])
        self.map_widget.zoom = zoom_level


def create(
    database: str, on_data_loaded: t.Callable[[pd.DataFrame], None], max_displayable_elements: int
) -> v.VuetifyWidget:
    return FilterWidget(database, on_data_loaded, max_displayable_elements)

  
