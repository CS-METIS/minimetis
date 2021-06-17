from dataclasses import Field, dataclass, field
import dataclasses
from multiprocessing import pool
from typing import Any, Dict, Iterable, List, Optional, Set, Type
from datetime import date, datetime
import pandas as pd
import numpy as np
from hashlib import sha256
import more_itertools as mit
from dvf import model
from reveal.ontologies import is_collection
from reveal.orientapi import OrientDBClient, OrientDBCommand, import_commands, create_schema_commands
from reveal.model import OVertex
from geojson.geometry import Geometry, Point, Polygon
from dvf import geocoder
import json
from dvf.convert import is_no_value
from dvf.convert import f2ui, is_no_value, n_b_t_q, n_type_de_voie, n_voie, n_code_postal, int_value
from reveal.model import normalize_properties
import requests
from requests.models import HTTPBasicAuth


def hexify(s: str):
    enc = sha256()
    enc.update(s.encode("utf-8"))
    return enc.hexdigest()

@dataclass
class DVFLot:
    no_lot: str
    surface_loi_carrez: int

@dataclass
class DVFRow:
    code_service_ch: str
    reference_document: str
    articles_cgi: List[str]
    no_dispostion: str
    date_mutation: date
    nature_mutation: str
    valeur_fonciere: float
    no_voie: str
    b_t_q: str
    type_de_voie: str
    code_voie: str
    voie: str
    code_postal: str
    commune: str
    code_departement: str
    code_commune: str
    prefixe_section: str
    section: str
    no_plan: str
    no_volume: str
    lots = List[DVFLot]
    code_type_local: str
    identifiant_local: str
    surface_reelle_bati: int
    nombre_pieces_principales: int
    nature_culture: str
    nature_culture_speciale: str
    surface_terrain: int

    def __init__(self, row: pd.Series) -> None:
        self.code_service_ch = row["Code service CH"]
        self.reference_document = row["Reference document"]
        self.articles_cgi = [
            row["1 Articles CGI"],
            row["2 Articles CGI"],
            row["3 Articles CGI"],
            row["4 Articles CGI"],
            row["5 Articles CGI"],
        ]
        self.no_dispostion = row["No disposition"]
        self.date_mutation = datetime.strptime(row["Date mutation"], "%d/%m/%Y")
        self.nature_mutation = row["Nature mutation"]
        self.valeur_fonciere = row["Valeur fonciere"]
        self.no_voie = row["No voie"]
        self.b_t_q = row["B/T/Q"]
        self.type_de_voie = row["Type de voie"]
        self.code_voie = row["Code voie"]
        self.voie = row["Voie"]
        self.code_postal = row["Code postal"]
        self.commune = row["Commune"]
        self.code_departement = row["Code departement"]
        self.code_commune = row["Code commune"]
        self.prefixe_section = row["Prefixe de section"]
        self.section = row["Section"]
        self.no_plan = row["No plan"]
        self.no_volume = row["No Volume"]
        self.lots = [
            DVFLot(
                no_lot=row["1er lot"],
                surface_loi_carrez=f2ui(row["Surface Carrez du 1er lot"]),
            ),
            DVFLot(
                no_lot=row["2eme lot"],
                surface_loi_carrez=f2ui(row["Surface Carrez du 2eme lot"]),
            ),
            DVFLot(
                no_lot=row["3eme lot"],
                surface_loi_carrez=f2ui(row["Surface Carrez du 3eme lot"]),
            ),
            DVFLot(
                no_lot=row["4eme lot"],
                surface_loi_carrez=f2ui(row["Surface Carrez du 4eme lot"]),
            ),
            DVFLot(
                no_lot=row["5eme lot"],
                surface_loi_carrez=f2ui(row["Surface Carrez du 5eme lot"]),
            ),
        ]
        self.code_type_local = row["Code type local"]
        self.identifiant_local = row["Type local"]
        self.surface_reelle_bati = f2ui(row["Surface reelle bati"])
        self.nombre_pieces_principales = f2ui(row["Nombre pieces principales"])
        self.nature_culture = row["Nature culture"]
        self.nature_culture_speciale = row["Nature culture speciale"]
        self.surface_terrain = f2ui(row["Surface terrain"])


def create_adresse_id(row: DVFRow) -> str:
    return hexify(
        "|".join(
            [
                str(row.no_voie),
                str(row.b_t_q),
                str(row.type_de_voie),
                str(row.voie),
                str(row.code_voie),
                str(row.code_postal),
                str(row.code_commune),
                str(row.code_departement),
            ]
        )
    )


def create_mutation_id(row: DVFRow) -> str:
    sid = "|".join(
        [
            str(row.code_service_ch),
            str(row.reference_document),
            row.date_mutation.strftime("%m-%d-%Y"),
            str(row.valeur_fonciere),
            create_adresse_id(row),
        ]
    )
    return hexify(sid)


def create_parcelle_id(row: DVFRow) -> str:
    return hexify(
        "|".join([str(row.prefixe_section), str(row.section), str(row.no_plan)])
    )


def create_bien_foncier_id(row: DVFRow) -> str:
    return hexify(
        "|".join(
            [
                create_parcelle_id(row),
                str(row.no_volume),
                "|".join([str(lot.no_lot) for lot in row.lots if lot is not np.nan]),
                str(row.code_type_local),
                str(row.surface_reelle_bati),
                str(row.identifiant_local),
                str(row.nombre_pieces_principales),
                str(row.nature_culture),
                str(row.nature_culture_speciale),
                str(row.surface_terrain),
            ]
        )
    )


def create_lot_id(row: DVFRow, lot: DVFLot) -> str:
    return hexify("|".join(["Lot", create_parcelle_id(row), str(lot.no_lot)]))


def create_volume_id(row: DVFRow) -> str:
    return hexify("|".join(["Volume", create_parcelle_id(row), str(row.no_volume)]))


def create_local_id(row: DVFRow) -> str:
    return hexify(
        "|".join(
            [
                "Local",
                create_parcelle_id(row),
                str(row.code_type_local),
                str(row.identifiant_local),
                str(row.surface_reelle_bati),
                str(row.nombre_pieces_principales),
            ]
        )
    )


def create_suf_id(row: DVFRow) -> str:
    return hexify(
        "|".join(
            [
                "Suf",
                create_parcelle_id(row),
                str(row.surface_terrain),
                str(row.nature_culture),
                str(row.nature_culture_speciale),
            ]
        )
    )


def create_disposition_id(mutation: model.Mutation, row: DVFRow) -> str:
    return hexify(
        "|".join(
            [
                "Disposition",
                str(mutation.vertex_id),
                str(len(mutation.dispositions_de_mutation) + 1),
            ]
        )
    )

def create_media_id(mutation: model.Mutation) -> str:
    return hexify(
        "|".join(
            [
                "Media",
                str(mutation.vertex_id),
                str(len(mutation.dispositions_de_mutation) + 1),
            ]
        )
    )


def extract_biens_foncier(
    row: DVFRow, adresse: model.Adresse, biens_foncier: Dict[str, model.BienFoncier]
) -> Set[model.BienFoncier]:
    lots: List[model.Lot] = []
    biens_foncier_disposition: Set[model.BienFoncier] = set()
    for lot in row.lots:
        if is_no_value(lot.no_lot):
            continue
        lot_id = create_lot_id(row, lot)
        if lot_id not in biens_foncier:
            biens_foncier[lot_id] = model.Lot(
                vertex_id=create_lot_id(row, lot),
                surface_carrez_lot=lot.surface_loi_carrez,
                no_lot=lot.no_lot,
                biens_foncier_de_lot=set(),
            )
        lots.append(biens_foncier[lot_id])
        biens_foncier_disposition.add(biens_foncier[lot_id])

    if not is_no_value(row.surface_reelle_bati) or not is_no_value(
        row.code_type_local
    ):
        local_id = create_local_id(row)
        if local_id not in biens_foncier:
            biens_foncier[local_id] = model.Local(
                vertex_id=create_local_id(row),
                code_type_local=row.code_type_local,
                identifiant_local=row.identifiant_local,
                nombre_pieces_principales=row.nombre_pieces_principales,
                surface_reelle_bati=row.surface_reelle_bati,
                adresse_de_local=adresse
            )
        for lot in lots:
            lot.biens_foncier_de_lot.add(biens_foncier[local_id])
        if len(lots) == 0:
            biens_foncier_disposition.add(biens_foncier[local_id])

    if not is_no_value(row.no_volume):
        volume_id = create_volume_id(row)
        if volume_id not in biens_foncier:
            biens_foncier[volume_id] = model.Volume(
                vertex_id=volume_id, no_volume=row.no_volume
            )
        for lot in lots:
            lot.biens_foncier_de_lot.add(biens_foncier[volume_id])
        if len(lots) == 0:
            biens_foncier_disposition.add(biens_foncier[volume_id])

    if not is_no_value(row.surface_terrain) and not is_no_value(
        row.nature_culture
    ):
        suf_id = create_suf_id(row)
        if suf_id not in biens_foncier:
            biens_foncier[suf_id] = model.Suf(
                vertex_id=suf_id,
                surface_terrain=row.surface_terrain,
                nature_culture=row.nature_culture,
                nature_culture_special=row.nature_culture_speciale,
            )
        for lot in lots:
            lot.biens_foncier_de_lot.add(biens_foncier[suf_id])
        if len(lots) == 0:
            biens_foncier_disposition.add(biens_foncier[suf_id])
    return biens_foncier_disposition


def extract_articles_cgi(row: DVFRow) -> Set[model.ArticleCGI]:
    return set(
        [
            model.ArticleCGI(article_cgi, article_cgi, "")
            for article_cgi in row.articles_cgi
            if article_cgi is not np.nan
        ]
    )



def parse_dvf_file(dvf_file_path: str, separator: str = "|") -> Iterable[model.Mutation]:
    types = {
        "Code service CH": "str",
        "Reference document": "str",
        "1 Articles CGI": "str",
        "2 Articles CGI": "str",
        "3 Articles CGI": "str",
        "4 Articles CGI": "str",
        "5 Articles CGI": "str",
        "No disposition": "str",
        "Date mutation": "str",
        "Nature mutation": "str",
        "Valeur fonciere": "float32",
        "No voie": "str",
        "B/T/Q": "str",
        "Type de voie": "str",
        "Code voie": "str",
        "Voie": "str",
        "Code postal": "str",
        "Commune": "str",
        "Code departement": "str",
        "Code commune": "str",
        "Prefixe de section": "str",
        "Section": "str",
        "No plan": "str",
        "No Volume": "str",
        "1er lot": "str",
        "Surface Carrez du 1er lot": "float32",
        "2eme lot": "str",
        "Surface Carrez du 2eme lot": "float32",
        "3eme lot": "str",
        "Surface Carrez du 3eme lot": "float32",
        "4eme lot": "str",
        "Surface Carrez du 4eme lot": "float32",
        "5eme lot": "str",
        "Surface Carrez du 5eme lot": "float32",
        "Code type local": "str",
        "Type local": "str",
        "Surface reelle bati": "float32",
        "Nombre pieces principales": "float32",
        "Nature culture": "str",
        "Nature culture speciale": "str",
        "Surface terrain": "float32",
    }
    data_df = pd.read_csv(
        dvf_file_path, decimal=",", sep=separator, low_memory=False, parse_dates=False
    )
    data_df = data_df.astype(types)
    mutations: Dict[str, model.Mutation] = {}
    adresses: Dict[str, model.Adresse] = {}
    parcelles: Dict[str, model.Parcelle] = {}
    biens_foncier: Dict[str, model.BienFoncier] = {}
    idx = 0
    for row in data_df.iterrows():
        idx = idx + 1
        print("Dispostion", idx)
        dvf_row = DVFRow(row=row[1])
        mutation_id = create_mutation_id(dvf_row)
        adresse_id = create_adresse_id(dvf_row)
        parcelle_id = create_parcelle_id(dvf_row)

        if adresse_id not in adresses:
            adresses[adresse_id] = model.Adresse(
                vertex_id=adresse_id,
                code_voie=dvf_row.code_voie,
                type_de_voie=n_type_de_voie(dvf_row.type_de_voie),
                voie=n_voie(dvf_row.voie),
                no_voie=int_value(dvf_row.no_voie),
                code_postal=n_code_postal(dvf_row.code_postal),
                b_t_q= n_b_t_q(dvf_row.b_t_q),
                commune=dvf_row.commune,
                code_commune=dvf_row.code_commune,
                location=Point([-180, -90])
            )

        if parcelle_id not in parcelles:
            parcelles[parcelle_id] = model.Parcelle(
                vertex_id=parcelle_id,
                code_commune=dvf_row.code_commune,
                code_departement=dvf_row.code_departement,
                prefixe_de_section=dvf_row.prefixe_section,
                section=dvf_row.section,
                no_plan=dvf_row.no_plan,
                location=None,
            )

        if mutation_id not in mutations:
            mutations[mutation_id] = model.Mutation(
                vertex_id=mutation_id,
                code_service_ch=dvf_row.code_service_ch,
                date=dvf_row.date_mutation,
                nature_mutation=dvf_row.nature_mutation,
                reference_document=dvf_row.reference_document,
                description="",
                articles_cgi_de_mutation=set(),
                dispositions_de_mutation=set(),
                medias_de_mutation=set()
            )
            media = model.Media(
                vertex_id=create_media_id(mutations[mutation_id]),
                description="",
                url=""
            )
            mutations[mutation_id].medias_de_mutation.add(media)
        biens_foncier_disposition = extract_biens_foncier(
            dvf_row, adresses[adresse_id], biens_foncier
        )
        mutation = mutations[mutation_id]
        disposition = model.Disposition(
            vertex_id=create_disposition_id(mutation, row),
            valeur_fonciere=dvf_row.valeur_fonciere,
            adresse_de_disposition=adresses[adresse_id],
            parcelle_de_disposition=parcelles[parcelle_id],
            biens_foncier_de_dispostion=biens_foncier_disposition,
        )
        mutation = mutations[mutation_id]
        mutation.dispositions_de_mutation.add(disposition)


    # geocode
    t_pool = pool.ThreadPool(10)
    t_pool.map(geocoder.geocode_adresse, adresses.values())
    return list(mutations.values())


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


@dataclass
class ModelUploadCommands:
    vertice_upsert_commands: List[str]
    edge_creation_commands: List[str]


def load_data(data: Iterable[OVertex]) -> ModelUploadCommands:
    edges: List[str] = []
    vertice: List[str] = []
    existing_vertex: Set[str] = set()
    for obj in data:
        commands = import_commands(obj, existing_vertex)
        for c in commands:
            if c.upsert is not None:
                vertice.append(c.upsert)
            edges.extend(c.edges)
    return ModelUploadCommands(vertice, edges)


def create_database(client: OrientDBClient, database: str, clazz: Any, csv_file: str):
    client.create_database(database)
    # create schema
    commands = create_schema_commands(clazz)
    for c in commands:
        print(c.command)
    res = client.batch(database, commands)
    print(res.status)
    # load csv
    mutations = parse_dvf_file(csv_file)
    commands = load_data(mutations)

    # create vertice
    vertice_cmds = [OrientDBCommand(cmd) for cmd in commands.vertice_upsert_commands]
    res = client.batch(database, vertice_cmds)
    print(res.status)
    edges_cmds = [OrientDBCommand(cmd) for cmd in commands.edge_creation_commands]
    res = client.batch(database, edges_cmds)


if __name__ == "__main__":
    client = OrientDBClient()
    create_database(client, "DVF3", model.Mutation, "dvf/data/valeursfoncieres-2019-1000.csv")
