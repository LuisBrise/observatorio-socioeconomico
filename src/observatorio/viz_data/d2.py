"""Datasets de visualización del dashboard D2 · Pulso de México.

Diseño (docs/diseno/09-dashboards-iniciales.md §4): no hay índice compuesto ni semáforo. Cada
indicador se muestra en una tarjeta con su propio contexto histórico: último dato, fecha de la
fuente, línea de los últimos 10 años sobre el rango histórico, percentil del dato actual en su
historia (color neutral) y cambio en 12 meses frente a su rango típico.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import polars as pl

from observatorio.catalog import Catalog
from observatorio.ingestion.base import RawStore
from observatorio.paths import Paths
from observatorio.pipeline import indicator_values, load_current, read_lock
from observatorio.transform import LineageStep, get_transform
from observatorio.viz_data.common import ChartSpec, write_chart

VENTANA = "2005-01"  # inicio común de la historia de referencia (la ENOE empieza en 2005)
ANIOS_LINEA = 10
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


@dataclass
class Tarjeta:
    id: str
    titulo: str
    indicador: str            # indicador mostrado (puede ser derivado)
    base: str                 # indicador con serie (para la derivación y la fecha de la fuente)
    unidad: str
    derivar_anual: bool = False
    cambio_en: str = "pp"     # "pp" (puntos) o "%" (variación relativa)
    nota: str = ""
    # Las series con tendencia (índices de nivel) casi siempre están en su máximo: su percentil
    # histórico no informa y no se muestra.
    percentil: bool = True


def _mes(period: str) -> str:
    y, m = period.split("-")
    return f"{MESES[int(m) - 1]} {y}"


def _fecha_fuente(paths: Paths, catalog: Catalog, series_id: str) -> str | None:
    """Fecha de última actualización declarada por la fuente para una serie del BIE de INEGI."""
    dataset_id, codigo = series_id.split(":", 1)
    entry = read_lock(paths).get(dataset_id)
    if not entry:
        return None
    store = RawStore(paths.raw, paths.root)
    carpeta = store.dataset_dir(catalog.datasets[dataset_id].fuente, dataset_id) / entry["vintage"]
    path = carpeta / f"bie_{codigo}.json"
    if not path.exists():
        return None
    texto = json.loads(path.read_text(encoding="utf-8"))["Series"][0].get("LASTUPDATE") or ""
    d, m, y = (texto.split(" ")[0].split("/") + ["", "", ""])[:3]
    return f"{y}-{m}-{d}" if y else None


def _contexto(v: pl.DataFrame, cambio_en: str, rupturas: list[str], con_percentil: bool = True) -> dict:
    """Estadísticos de contexto histórico de una serie mensual (columnas period, period_start, value)."""
    v = v.sort("period_start")
    ultimo = v.row(-1, named=True)
    hist = v.filter(pl.col("period") >= VENTANA)
    ruptura = next((r for r in rupturas if r <= ultimo["period"]), None)
    # Con una ruptura metodológica, la historia anterior no es comparable: sin percentil ni rango.
    comparable = hist if ruptura is None else hist.filter(pl.col("period") >= ruptura)
    n = comparable.height
    percentil = (None if ruptura is not None or n < 60 or not con_percentil
                 else round(float((comparable["value"] <= ultimo["value"]).mean()) * 100))
    inicio = ultimo["period_start"]
    hace12 = v.filter(pl.col("period_start") == inicio.replace(year=inicio.year - 1))
    cambio = None
    if hace12.height and (ruptura is None or hace12["period"][0] >= ruptura):
        prev = hace12["value"][0]
        cambio = ultimo["value"] - prev if cambio_en == "pp" else (ultimo["value"] / prev - 1) * 100
    # Rango típico del cambio en 12 meses: mediana del valor absoluto en la ventana histórica.
    s = hist.with_columns(pl.col("period_start").dt.offset_by("12mo").alias("_k"))
    pares = s.join(s.select(pl.col("_k").alias("period_start"), pl.col("value").alias("_prev")),
                   on="period_start")
    dif = ((pares["value"] - pares["_prev"]) if cambio_en == "pp"
           else (pares["value"] / pares["_prev"] - 1) * 100)
    tipico = float(dif.abs().median()) if pares.height and ruptura is None else None
    corte = f"{int(ultimo['period'][:4]) - ANIOS_LINEA}{ultimo['period'][4:]}"
    linea = v.filter(pl.col("period") > corte).select("period", "value")
    return {
        "valor": ultimo["value"], "periodo": ultimo["period"], "periodo_texto": _mes(ultimo["period"]),
        "percentil": percentil, "cambio_12m": cambio, "cambio_tipico": tipico,
        "rango": {"min": float(hist["value"].min()), "max": float(hist["value"].max()),
                  "desde": hist["period"].min()},
        "ruptura": ruptura, "linea": linea.to_dicts(),
    }


SECCIONES: dict[str, tuple[str, list[Tarjeta]]] = {
    "precios": ("Precios", [
        Tarjeta("inflacion", "Inflación general anual (INPC)", "eco.precios.inflacion.anual",
                "eco.precios.inflacion.inpc", "%", derivar_anual=True,
                nota="Meta de Banxico: 3 % ± 1 punto. El percentil compara con la historia de la serie, "
                     "no con la meta."),
    ]),
    "actividad": ("Actividad económica", [
        Tarjeta("igae", "IGAE: variación anual (serie original)", "eco.actividad.coyuntura.igae_var_anual",
                "eco.actividad.coyuntura.igae", "%", derivar_anual=True,
                nota="Aproximación mensual al PIB. La serie original compara meses con distinto número de "
                     "días hábiles."),
        Tarjeta("igae_sa", "IGAE desestacionalizado", "eco.actividad.coyuntura.igae_sa",
                "eco.actividad.coyuntura.igae_sa", "índice 2018 = 100", cambio_en="%",
                nota="INEGI reestima la serie desestacionalizada cada mes: los meses recientes cambian. "
                     "Es un índice con tendencia: no se muestra percentil histórico.", percentil=False),
    ]),
    "empleo": ("Empleo", [
        Tarjeta("desocupacion", "Tasa de desocupación (desestacionalizada)",
                "eco.laboral.desocupacion.tasa_sa",
                "eco.laboral.desocupacion.tasa_sa", "% de la PEA",
                nota="Baja en parte porque mucha gente se ocupa en la informalidad: no mide la calidad "
                     "del empleo. "
                     "Abril-junio de 2020: encuesta telefónica (ETOE)."),
    ]),
    "seguridad": ("Seguridad", [
        Tarjeta("homicidio", "Víctimas de homicidio doloso por mes (SESNSP)",
                "seg.violencia_letal.homicidio.victimas_doloso_mensual",
                "seg.violencia_letal.homicidio.victimas_doloso_mensual", "víctimas", cambio_en="%",
                nota="Carpetas de investigación. Nueva metodología desde enero de 2026: no se compara con la "
                     "historia anterior. Ver el tablero de violencia letal."),
    ]),
}


def build(paths: Paths, catalog: Catalog) -> list[str]:
    obs = load_current(paths)
    lock = read_lock(paths)
    var12 = get_transform("var_interanual@1")
    built = []
    for seccion, (titulo, tarjetas) in SECCIONES.items():
        filas, lineas, indicadores, series, transformaciones, caveats = [], [], [], [], [], []
        for t in tarjetas:
            if catalog.indicators[t.base].series[0].split(":", 1)[0] not in lock:
                continue  # datos aún no fijados: la página muestra un aviso en lugar de la tarjeta
            base = indicator_values(obs, catalog, t.base)
            sid = catalog.indicators[t.base].series[0]
            valores = var12(base.select("geo_id", "period", "period_start", "value"), rezago=12) \
                if t.derivar_anual else base.select("geo_id", "period", "period_start", "value")
            if t.derivar_anual:
                transformaciones.append(LineageStep("var_interanual@1", {"rezago": 12}, [t.base]).to_dict())
            rupturas = sorted(obs.filter((pl.col("series_id") == sid) & (pl.col("obs_status") == "B"))
                              ["period"].unique().to_list())
            ctx = _contexto(valores, t.cambio_en, rupturas, t.percentil)
            vintage = read_lock(paths)[sid.split(":", 1)[0]]["vintage"]
            lineas += [{"tarjeta": t.id, **x} for x in ctx.pop("linea")]
            filas.append({"id": t.id, "titulo": t.titulo, "unidad": t.unidad, "cambio_en": t.cambio_en,
                          "nota": t.nota, "actualizado_fuente": _fecha_fuente(paths, catalog, sid),
                          "consultado": f"{vintage[:4]}-{vintage[5:7]}-{vintage[8:10]}", **ctx})
            indicadores += [t.indicador] if t.indicador == t.base else [t.indicador, t.base]
            series.append(sid)
        if not filas:
            continue
        caveats += [
            f"Percentil: posición del último dato entre todos los meses desde {VENTANA[:4]} o desde el "
            "inicio de la serie si es posterior (0 = el más bajo, 100 = el más alto). No es un juicio: un "
            "percentil alto puede ser bueno o malo según el indicador.",
            "Cambio típico: mediana del cambio absoluto en 12 meses en el mismo periodo.",
            "Las cifras de los meses más recientes pueden revisarse en publicaciones posteriores.",
        ]
        spec = ChartSpec(
            chart_id=f"d2/{seccion}",
            question=(f"¿Cómo están los indicadores de {titulo.lower()} respecto a su propia historia "
                      "reciente?"),
            indicators=list(dict.fromkeys(indicadores)),
            caveats=caveats,
            transformations=transformaciones,
            series_usadas=series,
            periodos=sorted({f["periodo"] for f in filas}),
        )
        write_chart(paths, catalog, spec, {"lineas": pl.DataFrame(lineas)},
                    extra={"seccion": titulo, "tarjetas": filas})
        built.append(spec.chart_id)
    return built
