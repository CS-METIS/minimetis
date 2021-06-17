from dataclasses import dataclass
from dataclasses import field
from typing import Set
from datetime import date
from reveal.model import OVertex
import io
from geojson.geometry import Geometry, Point, Polygon


@dataclass(eq=False, frozen=True)
class Parcelle(OVertex):
    code_departement: str
    code_commune: str
    prefixe_de_section: str
    section: str
    no_plan: str
    location: Polygon


@dataclass(eq=False, frozen=True)
class Adresse(OVertex):
    no_voie: str
    b_t_q: str
    type_de_voie: str
    voie: str
    code_voie: str
    code_postal: str
    commune: str
    code_commune: str
    location: Point


@dataclass(eq=False, frozen=True)
class Media(OVertex):
    description: str
    url: str


@dataclass(eq=False, frozen=True)
class BienFoncier(OVertex):
    ...


@dataclass(eq=False, frozen=True)
class Local(BienFoncier):
    identifiant_local: str
    code_type_local: str
    nombre_pieces_principales: str
    surface_reelle_bati: str
    adresse_de_local: Adresse


@dataclass(eq=False, frozen=True)
class Suf(BienFoncier):
    surface_terrain: int
    nature_culture: str
    nature_culture_special: str


@dataclass(eq=False, frozen=True)
class Volume(BienFoncier):
    no_volume: str


@dataclass(eq=False, frozen=True)
class Lot(BienFoncier):
    no_lot: str
    surface_carrez_lot: int
    biens_foncier_de_lot: Set[BienFoncier]


@dataclass(eq=False, frozen=True)
class Disposition(OVertex):
    adresse_de_disposition: Adresse
    parcelle_de_disposition: Parcelle
    biens_foncier_de_dispostion: Set[BienFoncier]
    valeur_fonciere: float


@dataclass(eq=False, frozen=True)
class ArticleCGI(OVertex):
    article_cgi: str
    lib_article_cgi: str


@dataclass(eq=False, frozen=True)
class Mutation(OVertex):
    code_service_ch: str
    reference_document: str
    date: date
    nature_mutation: str
    articles_cgi_de_mutation: Set[ArticleCGI]
    dispositions_de_mutation: Set[Disposition]
    medias_de_mutation: Set[Media]
    description: io.TextIOBase
