from typing import Any, Optional
import numpy as np

def is_no_value(v: Any) -> bool:
    if v is None:
        return True
    if type(v) == int:
        if v < 0:
            return True
        return False
    if type(v) == str:
        if v == "nan":
            return True
        if v == "":
            return True
    try:
        return np.isnan(v)
    except TypeError:
        return False

def f2ui(v: float) -> Optional[int]:
    if np.isnan(v):
        return None
    else:
        return int(v)

def n_b_t_q(row_btq: str) -> str:
    if row_btq == "B":
        return "BIS"
    if row_btq == "T":
        return "TER"
    if row_btq == "Q":
        return "Quater"
    return row_btq

def n_type_de_voie(row_type_de_voie: str) -> str:
    types_de_voie = {
        "ALL": "Allée",
        "AV": "Avenue",
        "BD": "Boulevard",
        "CAR": "Carrefour",
        "CHE": "Chemin",
        "CHS": "Chaussée",
        "CITE": "Cité",
        "COR":"Corniche",
        "CRS":"Cours",
        "DOM":"Domaine",
        "DSC":"Descente",
        "ECA":"Ecart",
        "ESP":"Esplanade",
        "FG":"Faubourg",
        "GR":"Grande Rue",
        "HAM":"Hameau",
        "HLE":"Halle",
        "IMP":"Impasse",
        "LD":"Lieu-dit",
        "LOT":"Lotissement",
        "MAR":"Marché",
        "MTE":"Montée",
        "PAS":"Passage",
        "PL":"Place",
        "PLN":"Plaine",
        "PLT":"Plateau",
        "PRO":"Promenade",
        "PRV":"Parvis",
        "QUA":"Quartier",
        "QUAI":"Quai",
        "RES":"Résidence",
        "RLE":"Ruelle",
        "ROC":"Rocade",
        "RPT":"Rond-point",
        "RTE":"Route",
        "RUE":"Rue",
        "SEN":"Sente",
        "SQ":"Square",
        "TPL":"Terre-plein",
        "TRA":"Traverse",
        "VLA":"Villa",
        "VLGE":"Village"
    }
    return types_de_voie.get(row_type_de_voie, row_type_de_voie)

def n_voie(row_voie: str) -> str:
    substitutions = {
        "GEN ": "GENERAL ",
        "COL ": "COLONEL ",
        "DOC ": "DOCTEUR "
    }
    if isinstance(row_voie, str):
        for k, v in substitutions.items():
            row_voie = row_voie.replace(k, v)
        return row_voie

def n_code_postal(row_code_postal: str) -> str:
    if is_no_value(row_code_postal):
        return None
    return row_code_postal.rjust(5, "0")

def int_value(v: Any) -> Any:
    if is_no_value(v):
        return None
    try:
        return int(float(v))
    except ValueError:
        return None