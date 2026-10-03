// Componentes de visualización del observatorio.
//
// Se escriben como una fábrica que recibe sus dependencias (Plot y document) para que el
// mismo código funcione en Quarto (OJS), en Observable Framework y en pruebas con Node.
// Uso en Quarto:   charts = (await import("/components/charts.js")).createCharts({Plot, document})
//
// Reglas del sistema visual (docs/diseno/09-dashboards-iniciales.md §6):
// contexto en gris y foco en color; líneas de 2px; marcadores ≥ 8px con anillo del color de
// superficie; etiquetas directas selectivas + leyenda cuando hay ≥ 2 series; texto en tinta,
// nunca en el color de la serie; una sola escala vertical; fuente y procedencia en cada gráfica.

const DEFAULT_TOKENS = {
  surface: "#fcfcfb", ink: "#0b0b0b", ink2: "#52514e", muted: "#898781", grid: "#e1e0d9",
  axis: "#c3c2b7", context: "#c9c8c0", band: "rgba(82, 81, 78, 0.12)", focus: "#4a3aa7",
  compare: "#c98500", font: "system-ui, -apple-system, 'Segoe UI', sans-serif",
};

const TOKEN_VARS = {
  surface: "--obs-surface", ink: "--obs-ink", ink2: "--obs-ink-2", muted: "--obs-muted",
  grid: "--obs-grid", axis: "--obs-axis", context: "--obs-context", band: "--obs-band",
  focus: "--obs-focus", compare: "--obs-compare", font: "--obs-font",
};

export function readTokens(doc = globalThis.document) {
  const t = { ...DEFAULT_TOKENS };
  if (!doc?.body || typeof getComputedStyle === "undefined") return t;
  const style = getComputedStyle(doc.body);
  for (const [k, v] of Object.entries(TOKEN_VARS)) {
    const val = style.getPropertyValue(v).trim();
    if (val) t[k] = val;
  }
  return t;
}

// Generador para OJS: emite tokens nuevos cuando cambia el tema (claro/oscuro).
export function themeTokens(Generators, doc = globalThis.document) {
  return Generators.observe((notify) => {
    notify(readTokens(doc));
    const mo = new MutationObserver(() => notify(readTokens(doc)));
    mo.observe(doc.body, { attributes: true, attributeFilter: ["class", "data-theme"] });
    mo.observe(doc.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    const mq = globalThis.matchMedia?.("(prefers-color-scheme: dark)");
    const onMq = () => notify(readTokens(doc));
    mq?.addEventListener?.("change", onMq);
    return () => { mo.disconnect(); mq?.removeEventListener?.("change", onMq); };
  });
}

const fmtNum = new Intl.NumberFormat("es-MX", { maximumFractionDigits: 0 });
const fmt1 = new Intl.NumberFormat("es-MX", { maximumFractionDigits: 1 });
const year = (d) => +String(d.period).slice(0, 4);

export function createCharts({ Plot, document: doc = globalThis.document }) {
  const el = (tag, attrs = {}, children = []) => {
    const node = doc.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "text") node.textContent = v;
      else if (k === "style") node.setAttribute("style", v);
      else node.setAttribute(k, v);
    }
    for (const c of [].concat(children)) if (c != null) node.append(c);
    return node;
  };

  function legend(items) {
    return el("div", { class: "obs-legend", role: "list" }, items.map((it) =>
      el("span", { role: "listitem" }, [
        it.kind === "band"
          ? el("i", { class: "obs-key-band", style: `background:${it.color}` })
          : el("i", { class: "obs-key-line", style: `border-color:${it.color}` }),
        it.label,
      ])));
  }

  function baseStyle(t) {
    return { fontFamily: t.font, fontSize: "12px", color: t.ink2, background: "transparent",
      overflow: "visible" };
  }

  // Gráfica 1.1 · Serie de un país foco dentro de la distribución de su grupo.
  function serieDistribucion(data, { tokens: t = DEFAULT_TOKENS, width = 720, unidad = "" } = {}) {
    const foco = data.paises.filter((d) => d.geo_id === data.foco);
    const contexto = data.paises.filter((d) => d.geo_id !== data.foco);
    const dist = data.distribucion.map((d) => ({ ...d, year: year(d) }));
    const lastFoco = foco.at(-1);
    const lastMed = dist.filter((d) => d.mediana != null).at(-1);
    const focoName = lastFoco?.nombre ?? data.foco;
    const years = data.paises.map(year);
    const [y0, y1] = [Math.min(...years), Math.max(...years)];
    // Solo eventos dentro del periodo con datos: no se extiende el eje para mostrar un evento.
    const eventos = (data.eventos ?? [])
      .map((e) => ({ ...e, year: +String(e.inicio).slice(0, 4) }))
      .filter((e) => e.year >= y0 && e.year <= y1);

    const yMax = Math.max(...data.paises.map((d) => d.value), ...dist.map((d) => d.p75 ?? 0));
    // Si las etiquetas finales quedarían encimadas, la mediana se identifica solo por la leyenda.
    const labelMedian = lastMed && lastFoco &&
      Math.abs(lastMed.mediana - lastFoco.value) > yMax * 0.06;

    const fig = Plot.plot({
      document: doc, width, height: Math.round(Math.min(440, Math.max(300, width * 0.55))),
      marginLeft: 56, marginRight: 96, marginTop: 44,
      style: baseStyle(t),
      x: { label: null, tickFormat: "d", domain: [y0, y1], ticks: Math.max(4, Math.floor(width / 110)) },
      y: { label: unidad, labelAnchor: "top", nice: true, domain: [0, yMax * 1.05],
        tickFormat: (v) => fmtNum.format(v) },
      marks: [
        Plot.gridY({ stroke: t.grid, strokeOpacity: 1 }),
        Plot.ruleY([0], { stroke: t.axis }),
        Plot.ruleX(eventos, { x: "year", stroke: t.axis, strokeWidth: 1 }),
        Plot.text(eventos, { x: "year", frameAnchor: "top", dy: -14, text: (d) => d.titulo,
          textAnchor: "start", dx: 3, fill: t.muted, fontSize: 10, lineWidth: 9 }),
        Plot.areaY(dist, { x: "year", y1: "p25", y2: "p75", fill: t.band,
          defined: (d) => d.p25 != null }),
        Plot.lineY(contexto, { x: year, y: "value", z: "geo_id", stroke: t.context,
          strokeWidth: 1 }),
        Plot.lineY(dist, { x: "year", y: "mediana", stroke: t.ink2, strokeWidth: 1.5,
          defined: (d) => d.mediana != null }),
        Plot.lineY(foco, { x: year, y: "value", stroke: t.focus, strokeWidth: 2,
          strokeLinejoin: "round", strokeLinecap: "round" }),
        Plot.dot(lastFoco ? [lastFoco] : [], { x: year, y: "value", r: 4, fill: t.focus,
          stroke: t.surface, strokeWidth: 2 }),
        Plot.text(lastFoco ? [lastFoco] : [], { x: year, y: "value", text: () => focoName,
          dx: 9, textAnchor: "start", fill: t.ink, fontWeight: 600 }),
        Plot.text(labelMedian ? [lastMed] : [], { x: "year", y: "mediana",
          text: () => "Mediana ALC", dx: 9, textAnchor: "start", fill: t.ink2 }),
        Plot.ruleX(data.paises, Plot.pointerX({ x: year, stroke: t.axis })),
        Plot.tip(data.paises, Plot.pointer({ x: year, y: "value", fill: t.surface,
          stroke: t.axis, title: (d) => `${d.nombre} · ${d.period}\n${fmtNum.format(d.value)} ${unidad}` })),
      ],
    });
    fig.setAttribute("role", "img");
    fig.setAttribute("aria-label",
      `Serie anual de ${focoName} con la mediana y el rango intercuartil de ${data.grupo_nombre ?? "su grupo"}.` +
      (lastFoco ? ` Último dato de ${focoName}: ${fmtNum.format(lastFoco.value)} (${lastFoco.period}).` : ""));
    return el("div", {}, [
      legend([
        { label: focoName, color: t.focus },
        { label: "Mediana de ALC", color: t.ink2 },
        { label: "50 % central de ALC (p25–p75)", color: t.band, kind: "band" },
        { label: "Países de ALC con más de 10 M hab.", color: t.context },
      ]),
      fig,
    ]);
  }

  // Gráfica 1.2 · Small multiples: foco como referencia en cada panel.
  function multiplesReferencia(data, { tokens: t = DEFAULT_TOKENS, width = 720, unidad = "" } = {}) {
    const byGeo = d3group(data.relativo, (d) => d.geo_id);
    const foco = byGeo.get(data.foco) ?? [];
    const focoName = foco[0]?.nombre ?? data.foco;
    const yMax = Math.max(100, ...data.relativo.map((d) => d.value));
    const cols = Math.max(1, Math.floor(width / 230));
    const panelW = Math.floor((width - (cols - 1) * 20) / cols);
    const panels = [...byGeo.entries()]
      .filter(([g]) => g !== data.foco && data.paneles.includes(g))
      .sort((a, b) => a[1][0].nombre.localeCompare(b[1][0].nombre, "es"))
      .map(([, rows]) => {
        const last = rows.at(-1);
        const p = Plot.plot({
          document: doc, width: panelW, height: 150, marginLeft: 32, marginRight: 8,
          marginTop: 8, marginBottom: 22, style: baseStyle(t),
          x: { label: null, tickFormat: "d", ticks: 3 },
          y: { label: null, domain: [0, yMax], ticks: [0, 50, 100] },
          marks: [
            Plot.gridY([0, 50, 100], { stroke: t.grid, strokeOpacity: 1 }),
            Plot.lineY(foco, { x: year, y: "value", stroke: t.focus, strokeWidth: 2 }),
            Plot.lineY(rows, { x: year, y: "value", stroke: t.compare, strokeWidth: 2 }),
            Plot.dot([last], { x: year, y: "value", r: 4, fill: t.compare, stroke: t.surface,
              strokeWidth: 2 }),
            Plot.tip([...rows, ...foco], Plot.pointerX({ x: year, y: "value", fill: t.surface,
              stroke: t.axis, title: (d) => `${d.nombre} · ${d.period}: ${fmt1.format(d.value)} ${unidad}` })),
          ],
        });
        p.setAttribute("role", "img");
        p.setAttribute("aria-label", `${last.nombre}: ${fmt1.format(last.value)} ${unidad} en ${last.period}; ${focoName} como referencia.`);
        return el("div", {}, [
          el("p", { class: "obs-panel-title", text: last.nombre }),
          el("p", { class: "obs-sub", style: "margin:0;font-size:.8rem",
            text: `${fmt1.format(last.value)} en ${last.period}` }),
          p,
        ]);
      });
    return el("div", {}, [
      legend([
        { label: `${focoName} (referencia en cada panel)`, color: t.focus },
        { label: "País del panel", color: t.compare },
      ]),
      el("div", { class: "obs-grid-multiples" }, panels),
    ]);
  }

  // Pie de fuente + panel de procedencia ("¿De dónde viene esto?").
  function procedencia(prov, { csv = [] } = {}) {
    const fuentes = [...new Set(prov.series.map((s) => `${s.source}, ${s.dataset}`))].join("; ");
    const vint = prov.series.map((s) => s.vintage).sort().at(-1);
    const items = prov.series.map((s) => el("li", {}, [
      el("code", { text: s.series_id }), ` · vintage ${s.vintage} · consultado ${s.retrieved_at}`,
      s.source_declared_version ? ` · versión declarada por la fuente: ${s.source_declared_version}` : "",
      ` · validación: ${s.validation_status}`,
      el("br"), "SHA-256 del crudo: ", el("code", { text: s.raw_content_sha256 }),
      el("ul", {}, s.raw_files.map((f) => el("li", {}, [el("code", { text: `${f.name}` }), ` ← ${f.url}`]))),
      ...(s.known_breaks ?? []).map((b) => el("div", { text: `Ruptura conocida (${b.fecha}): ${b.descripcion}` })),
    ]));
    const transf = prov.transformations.map((tr) =>
      el("li", {}, [el("code", { text: tr.transform }), ` ${JSON.stringify(tr.params)}`]));
    const grupos = Object.entries(prov.groups).map(([g, m]) =>
      el("li", {}, [el("code", { text: g }), ` (${m.length}): ${m.join(", ")}`]));
    return el("div", {}, [
      el("p", { class: "obs-source" }, [
        `Fuente: ${fuentes} (vintage ${vint}). Licencia: ${prov.licenses.join(", ")}. `,
        ...csv.flatMap(([name, href], i) => [i ? " · " : "Datos: ", el("a", { href, text: name })]),
      ]),
      el("details", {}, [
        el("summary", { text: "Fuente y método: ¿de dónde viene esta gráfica?" }),
        el("p", {}, [el("strong", { text: "Pregunta: " }), prov.question]),
        el("p", { text: "Indicadores:" }),
        el("ul", {}, prov.indicators.map((i) => el("li", {}, [el("code", { text: i.id }), ` — ${i.nombre} (${i.unidad})`]))),
        transf.length ? el("p", { text: "Transformaciones:" }) : null,
        transf.length ? el("ul", {}, transf) : null,
        grupos.length ? el("p", { text: "Grupos usados:" }) : null,
        grupos.length ? el("ul", {}, grupos) : null,
        el("p", { text: "Cadena hasta los datos originales:" }),
        el("ul", {}, items),
        el("p", { text: `Construido: ${prov.built_at} · commit ${prov.git_sha ?? "—"}` }),
      ]),
    ]);
  }

  function advertencias(prov) {
    return el("div", { class: "obs-caveats" }, [
      el("p", {}, [el("span", { class: "obs-tag", text: "ADVERTENCIAS" }), "Qué no podemos concluir:"]),
      el("ul", {}, prov.caveats.map((c) => el("li", { text: c }))),
    ]);
  }

  return { legend, serieDistribucion, multiplesReferencia, procedencia, advertencias };
}

function d3group(rows, key) {
  const m = new Map();
  for (const r of rows) {
    const k = key(r);
    if (!m.has(k)) m.set(k, []);
    m.get(k).push(r);
  }
  for (const v of m.values()) v.sort((a, b) => year(a) - year(b));
  return m;
}
