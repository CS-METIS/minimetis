import dvf.model as model
import geojson.geometry as geom
from typing import Optional, Any
from geopy.geocoders import Pelias
from dvf.convert import is_no_value

def opt_str(v: Any) -> str:
    if is_no_value(v):
        return ""
    return f"{v} "

cpt = 0

def geocode_adresse(adresse: model.Adresse) -> Optional[geom.Point]:
    global cpt
    cpt = cpt+1
    domain = "192.168.0.153:4000"
    b_t_q = opt_str(adresse.b_t_q)
    type_de_voie = opt_str(adresse.type_de_voie)
    voie = opt_str(adresse.voie)
    code_postal = opt_str(adresse.code_postal)
    adresse_str = f"{opt_str(adresse.no_voie)}{b_t_q}{type_de_voie}{voie}, {code_postal}{opt_str(adresse.commune)}"
    pelias = Pelias(domain=domain, scheme="http", timeout=20)
    res = pelias.geocode(adresse_str, exactly_one=True)
    if res is not None:
        adresse.location["coordinates"] = [res.longitude, res.latitude]
    else:
        adresse_str = f"{opt_str(adresse.commune)}"
        res = pelias.geocode(adresse_str, exactly_one=True)
        if res is not None:
            adresse.location["coordinates"] = [res.longitude, res.latitude]
    print("geocodage", cpt, adresse_str)


def geocode_parcelle(parcelle: model.Parcelle) -> Optional[geom.Polygon]:
    parcelle.location = None