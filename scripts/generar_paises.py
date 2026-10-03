"""Genera catalog/geographies/paises.csv a partir de ISO 3166-1 (pycountry).

Se ejecuta una sola vez (o al actualizar pycountry); el CSV resultante se versiona
y se revisa a mano. Los nombres en español provienen de las traducciones de
iso-codes (Debian) incluidas en pycountry, con ajustes a nombres de uso común.
"""

from __future__ import annotations

import csv
import gettext
from pathlib import Path

import pycountry

OUT = Path(__file__).resolve().parents[1] / "catalog" / "geographies" / "paises.csv"

# Nombres de uso común en español (las traducciones ISO usan formas oficiales largas).
OVERRIDES_ES = {
    "BOL": "Bolivia", "VEN": "Venezuela", "IRN": "Irán", "KOR": "Corea del Sur",
    "PRK": "Corea del Norte", "RUS": "Rusia", "SYR": "Siria", "TZA": "Tanzania",
    "VNM": "Vietnam", "LAO": "Laos", "MDA": "Moldavia", "FSM": "Micronesia",
    "CZE": "Chequia", "GBR": "Reino Unido", "USA": "Estados Unidos", "TWN": "Taiwán",
    "PSE": "Palestina", "COD": "República Democrática del Congo", "COG": "Congo",
    "MKD": "Macedonia del Norte", "VCT": "San Vicente y las Granadinas",
    "KNA": "San Cristóbal y Nieves", "LCA": "Santa Lucía", "TUR": "Turquía",
    "NLD": "Países Bajos", "CIV": "Costa de Marfil", "BRN": "Brunéi",
    "CPV": "Cabo Verde", "SWZ": "Esuatini", "TLS": "Timor Oriental",
}
EXTRA = [  # Códigos usados por fuentes internacionales que no están en ISO 3166-1.
    ("XKX", "Kosovo", "Kosovo"),
    ("CHI", "Islas del Canal", "Channel Islands"),
]


def main() -> None:
    es = gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["es"])
    rows = []
    for c in pycountry.countries:
        name_en = getattr(c, "common_name", None) or c.name
        name_es = OVERRIDES_ES.get(c.alpha_3) or es.gettext(c.name)
        rows.append((c.alpha_3, name_es, name_en))
    rows.extend(EXTRA)
    rows.sort()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["geo_id", "nombre_es", "nombre_en", "tipo", "valido_desde", "valido_hasta"])
        for iso3, es_name, en_name in rows:
            w.writerow([iso3, es_name, en_name, "pais", "", ""])
    print(f"{len(rows)} países → {OUT}")


if __name__ == "__main__":
    main()
