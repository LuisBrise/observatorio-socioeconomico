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
  compare: "#c98500", ord1: "#b3abeb", ord2: "#7c6fd6", ord3: "#4a3aa7",
  font: "system-ui, -apple-system, 'Segoe UI', sans-serif",
};

const TOKEN_VARS = {
  surface: "--obs-surface", ink: "--obs-ink", ink2: "--obs-ink-2", muted: "--obs-muted",
  grid: "--obs-grid", axis: "--obs-axis", context: "--obs-context", band: "--obs-band",
  focus: "--obs-focus", compare: "--obs-compare", font: "--obs-font",
  ord1: "--obs-ord-1", ord2: "--obs-ord-2", ord3: "--obs-ord-3",
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
          : el("i", { class: "obs-key-line",
            style: `border-color:${it.color}${it.kind === "dash" ? ";border-top-style:dashed" : ""}` }),
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


  // Gráfica de abanico: serie observada (continua) + proyección (mediana discontinua) con
  // intervalos de predicción del 80 % y 95 %. Codificación de prospectiva del sistema visual.
  function abanico(data, { tokens: t = DEFAULT_TOKENS, width = 720, unidad = "", nombre = "" } = {}) {
    const obs = data.observado.map((d) => ({ ...d, year: year(d) }));
    const proj = data.proyeccion.map((d) => ({ ...d, year: year(d) }));
    const lastObs = obs.at(-1);
    // La mediana parte del último dato observado para que la línea sea continua visualmente.
    const med = lastObs ? [{ year: lastObs.year, mediana: lastObs.value }, ...proj] : proj;
    const yMax = Math.max(...obs.map((d) => d.value), ...proj.map((d) => d.u95 ?? d.mediana));
    const minimo = data.minimo;
    const fig = Plot.plot({
      document: doc, width, height: Math.round(Math.min(420, Math.max(280, width * 0.5))),
      marginLeft: 48, marginRight: 24, marginTop: 30,
      style: baseStyle(t),
      x: { label: null, tickFormat: "d", ticks: Math.max(4, Math.floor(width / 100)) },
      y: { label: unidad, labelAnchor: "top", domain: [0, yMax * 1.05], nice: true },
      marks: [
        Plot.gridY({ stroke: t.grid, strokeOpacity: 1 }),
        Plot.ruleY([0], { stroke: t.axis }),
        Plot.areaY(proj, { x: "year", y1: "l95", y2: "u95", fill: t.focus, fillOpacity: 0.10 }),
        Plot.areaY(proj, { x: "year", y1: "l80", y2: "u80", fill: t.focus, fillOpacity: 0.18 }),
        Plot.ruleX(lastObs ? [lastObs] : [], { x: "year", stroke: t.axis, strokeDasharray: "2,3" }),
        Plot.text(lastObs ? [lastObs] : [], { x: "year", frameAnchor: "top", dy: -16, dx: 4,
          textAnchor: "start", fill: t.muted, fontSize: 10, text: () => "Proyección ONU →" }),
        Plot.lineY(obs, { x: "year", y: "value", stroke: t.focus, strokeWidth: 2 }),
        Plot.lineY(med, { x: "year", y: "mediana", stroke: t.focus, strokeWidth: 2,
          strokeDasharray: "5,4" }),
        // Tramo del mínimo (puede abarcar varios años): segmento horizontal + etiqueta.
        Plot.ruleY(minimo ? [minimo] : [], { y: "value", x1: (d) => +d.desde, x2: (d) => +d.hasta,
          stroke: t.ink, strokeWidth: 3 }),
        Plot.text(minimo ? [minimo] : [], { x: (d) => (+d.desde + +d.hasta) / 2, y: "value", dy: 14,
          fill: t.ink2, fontSize: 11,
          text: (d) => `Mínimo${d.es_proyeccion ? " proyectado" : ""}: ${fmt1.format(d.value)}` +
            (d.desde === d.hasta ? ` (${d.desde})` : ` (${d.desde}–${d.hasta})`) }),
        Plot.ruleX([...obs, ...proj], Plot.pointerX({ x: "year", stroke: t.axis })),
        Plot.tip([...obs, ...proj], Plot.pointerX({ x: "year", y: (d) => d.value ?? d.mediana,
          fill: t.surface, stroke: t.axis,
          title: (d) => d.value != null
            ? `${d.period} (estimación): ${fmt1.format(d.value)}`
            : `${d.period} (proyección)\nMediana: ${fmt1.format(d.mediana)}\n80 %: ${fmt1.format(d.l80)}–${fmt1.format(d.u80)}\n95 %: ${fmt1.format(d.l95)}–${fmt1.format(d.u95)}` })),
      ],
    });
    fig.setAttribute("role", "img");
    fig.setAttribute("aria-label", `${nombre}: estimaciones hasta ${lastObs?.period} y proyección de la ONU con intervalos del 80 % y 95 %.`);
    return el("div", {}, [
      legend([
        { label: "Estimación", color: t.focus },
        { label: "Proyección (mediana)", color: t.focus, kind: "dash" },
        { label: "Intervalo de predicción 80 %", color: t.focus + "2e", kind: "band" },
        { label: "Intervalo de predicción 95 %", color: t.focus + "1a", kind: "band" },
      ]),
      fig,
    ]);
  }


  // Varias series (p. ej., líneas de pobreza) cortadas en rupturas de comparabilidad: cada tramo
  // se dibuja por separado y la ruptura se anota. Colores: rampa ordinal de un tono.
  function lineasTramos(data, { tokens: t = DEFAULT_TOKENS, width = 720, unidad = "", serieKey = "linea",
                                series = [] } = {}) {
    const rows = data.pobreza.map((d) => ({ ...d, year: year(d) }));
    const colors = [t.ord1, t.ord2, t.ord3];
    const color = Object.fromEntries(series.map((s, i) => [s.key, colors[i] ?? t.ink2]));
    const label = Object.fromEntries(series.map((s) => [s.key, s.label]));
    // Etiquetas finales solo si no chocan (no se desplazan: la leyenda y el tooltip identifican el resto).
    const last = [];
    for (const d of series.map((s) => rows.filter((r) => r[serieKey] === s.key).at(-1)).filter(Boolean)
      .sort((a, b) => b.value - a.value)) {
      if (last.every((l) => Math.abs(l.value - d.value) >= 7)) last.push(d);
    }
    const rupt = (data.rupturas ?? []).map((p) => ({ year: +p }));
    const fig = Plot.plot({
      document: doc, width, height: Math.round(Math.min(400, Math.max(280, width * 0.5))),
      marginLeft: 44, marginRight: 110, marginTop: 30, style: baseStyle(t),
      x: { label: null, tickFormat: "d", ticks: Math.max(4, Math.floor(width / 110)) },
      y: { label: unidad, labelAnchor: "top", domain: [0, 100], ticks: 5 },
      marks: [
        Plot.gridY({ stroke: t.grid, strokeOpacity: 1, ticks: 5 }),
        Plot.ruleY([0], { stroke: t.axis }),
        // La ruptura se ubica entre el último año del tramo anterior y el primero del nuevo.
        Plot.ruleX(rupt, { x: (d) => d.year - 1, stroke: t.axis, strokeDasharray: "3,3" }),
        Plot.text(rupt, { x: (d) => d.year - 1, frameAnchor: "top", dy: -16, textAnchor: "middle",
          fill: t.muted, fontSize: 10, text: () => "Cambio de encuesta" }),
        Plot.lineY(rows, { x: "year", y: "value", z: (d) => `${d[serieKey]}-${d.tramo}`,
          stroke: (d) => color[d[serieKey]], strokeWidth: 2 }),
        Plot.dot(rows, { x: "year", y: "value", r: 3, fill: (d) => color[d[serieKey]],
          stroke: t.surface, strokeWidth: 1.5 }),
        Plot.text(last, { x: "year", y: "value", dx: 8, textAnchor: "start", fill: t.ink,
          text: (d) => `${label[d[serieKey]]}: ${fmt1.format(d.value)} %` }),
        Plot.tip(rows, Plot.pointer({ x: "year", y: "value", fill: t.surface, stroke: t.axis,
          title: (d) => `${d.period} · ${label[d[serieKey]]}\n${fmt1.format(d.value)} % de la población` +
            (d.obs_status === "B" ? "\nInicio de un nuevo tramo comparable" : "") })),
      ],
    });
    fig.setAttribute("role", "img");
    fig.setAttribute("aria-label", "Porcentaje de la población bajo líneas internacionales de pobreza; " +
      "la serie se corta en los cambios de encuesta.");
    return el("div", {}, [
      legend(series.map((s) => ({ label: s.label, color: color[s.key] }))),
      fig,
    ]);
  }

  // Pesas (dumbbell): valor inicial y final por país, ordenado por el final; foco resaltado.
  // Punto final hueco = hubo cambio de encuesta o método entre ambos puntos.
  function pesas(data, { tokens: t = DEFAULT_TOKENS, width = 720, unidad = "",
                         etiquetas = { inicio: "Alrededor de 2000", fin: "Dato más reciente",
                                       ruptura: "Dato más reciente, con cambio de encuesta en el periodo" } } = {}) {
    const rows = data.gini;
    const fig = Plot.plot({
      document: doc, width, height: 26 * rows.length + 60, marginLeft: 150, marginRight: 30,
      marginTop: 30, style: baseStyle(t),
      x: { label: unidad, labelAnchor: "right", nice: true, grid: true },
      y: { label: null, domain: rows.map((d) => d.nombre + (d.cobertura === "urbano" ? " (urbano)" : "")) },
      marks: [
        Plot.gridX({ stroke: t.grid, strokeOpacity: 1 }),
        Plot.link(rows, { x1: "inicio", x2: "fin", y1: (d) => d.nombre + (d.cobertura === "urbano" ? " (urbano)" : ""),
          y2: (d) => d.nombre + (d.cobertura === "urbano" ? " (urbano)" : ""),
          stroke: (d) => (d.geo_id === data.foco ? t.focus : t.context), strokeWidth: 2 }),
        Plot.dot(rows, { x: "inicio", y: (d) => d.nombre + (d.cobertura === "urbano" ? " (urbano)" : ""),
          r: 4, fill: (d) => (d.geo_id === data.foco ? t.focus : t.ink2), stroke: t.surface, strokeWidth: 2 }),
        Plot.dot(rows, { x: "fin", y: (d) => d.nombre + (d.cobertura === "urbano" ? " (urbano)" : ""),
          r: 5, fill: (d) => (d.ruptura ? t.surface : (d.geo_id === data.foco ? t.focus : t.ink)),
          stroke: (d) => (d.geo_id === data.foco ? t.focus : t.ink), strokeWidth: 2 }),
        Plot.tip(rows, Plot.pointerY({ x: "fin", y: (d) => d.nombre + (d.cobertura === "urbano" ? " (urbano)" : ""),
          fill: t.surface, stroke: t.axis,
          title: (d) => `${d.nombre}${d.cobertura === "urbano" ? " (solo urbano)" : ""}\n` +
            (d.anio_inicio === d.anio_fin
              ? `${d.anio_fin} · ${etiquetas.inicio}: ${fmt1.format(d.inicio)} · ${etiquetas.fin}: ${fmt1.format(d.fin)}`
              : `${d.anio_inicio}: ${fmt1.format(d.inicio)} → ${d.anio_fin}: ${fmt1.format(d.fin)}`) +
            (d.ruptura ? "\nHubo cambio de encuesta o método entre ambos años" : "") })),
      ],
    });
    fig.setAttribute("role", "img");
    fig.setAttribute("aria-label", "Índice de Gini por país alrededor de 2000 y en el dato más reciente.");
    const key = (filled, label) => el("span", {}, [
      el("i", { style: `display:inline-block;width:10px;height:10px;border-radius:50%;border:2px solid ${t.ink};` +
        `background:${filled ? t.ink : "transparent"}` }), label]);
    return el("div", {}, [
      el("div", { class: "obs-legend" }, [
        el("span", {}, [el("i", { style: `display:inline-block;width:8px;height:8px;border-radius:50%;background:${t.ink2}` }), etiquetas.inicio]),
        key(true, etiquetas.fin),
        rows.some((d) => d.ruptura) ? key(false, etiquetas.ruptura) : null,
        el("span", {}, [el("i", { class: "obs-key-line", style: `border-color:${t.focus}` }), data.foco === "MEX" ? "México" : data.foco]),
      ]),
      fig,
    ]);
  }


  // Paneles por definición: misma escala vertical, una medida por panel, intervalo de confianza
  // como barra vertical cuando existe. Para mostrar que una cifra depende de su definición.
  function panelesDefiniciones(data, { tokens: t = DEFAULT_TOKENS, width = 720, unidad = "" } = {}) {
    const rows = data.medidas.map((d) => ({ ...d, year: year(d) }));
    const yMax = Math.max(...rows.map((d) => d.hi ?? d.value));
    const cols = width >= 640 ? data.orden.length : 1;
    const panelW = Math.floor((width - (cols - 1) * 20) / cols);
    const panels = data.orden.map((key) => {
      const r = rows.filter((d) => d.medida === key);
      const last = r.at(-1);
      const p = Plot.plot({
        document: doc, width: panelW, height: 220, marginLeft: 36, marginRight: 46, marginTop: 12,
        marginBottom: 24, style: baseStyle(t),
        x: { label: null, tickFormat: "d", domain: [r[0].year - 0.5, last.year + 0.5],
          ticks: r.map((d) => d.year).filter((_, i, a) => i % 2 === 0 || i === a.length - 1) },
        y: { label: null, domain: [0, Math.ceil(yMax / 10) * 10], ticks: 4 },
        marks: [
          Plot.gridY({ stroke: t.grid, strokeOpacity: 1, ticks: 4 }),
          Plot.ruleY([0], { stroke: t.axis }),
          Plot.ruleX(r.filter((d) => d.lo != null), { x: "year", y1: "lo", y2: "hi", stroke: t.focus,
            strokeWidth: 3, strokeOpacity: 0.45 }),
          Plot.lineY(r, { x: "year", y: "value", stroke: t.focus, strokeWidth: 2 }),
          Plot.dot(r, { x: "year", y: "value", r: 4, fill: t.focus, stroke: t.surface, strokeWidth: 2 }),
          Plot.text([last], { x: "year", y: "value", dx: 8, textAnchor: "start", fill: t.ink, fontWeight: 600,
            text: (d) => `${fmt1.format(d.value)} %` }),
          Plot.tip(r, Plot.pointerX({ x: "year", y: "value", fill: t.surface, stroke: t.axis,
            title: (d) => `${d.titulo} · ${d.period}\n${fmt1.format(d.value)} % de la población` +
              (d.lo != null ? `\nIntervalo de confianza 95 %: ${fmt1.format(d.lo)}–${fmt1.format(d.hi)}` : "") })),
        ],
      });
      p.setAttribute("role", "img");
      p.setAttribute("aria-label", `${r[0].titulo}: ${fmt1.format(last.value)} % en ${last.period}.`);
      return el("div", {}, [
        el("p", { class: "obs-panel-title", text: r[0].titulo }),
        el("p", { class: "obs-sub", style: "margin:0 0 .3rem;font-size:.8rem", text: r[0].definicion }),
        p,
      ]);
    });
    return el("div", {}, [
      el("p", { class: "obs-sub", style: "font-size:.85rem", text: `${unidad} · misma escala en los tres paneles` }),
      el("div", { class: "obs-grid-multiples", style: `grid-template-columns:repeat(${cols}, 1fr)` }, panels),
    ]);
  }


  // Dos fuentes del mismo concepto (p. ej., encuesta vs cuentas distributivas). Tramos cortados en
  // rupturas; valores imputados (obs_status I) con línea punteada, conectada al último dato medido.
  function dosFuentes(data, { tokens: t = DEFAULT_TOKENS, width = 720, unidad = "", fuentes = [] } = {}) {
    const rows = data.serie.map((d) => ({ ...d, year: year(d) }));
    const colors = [t.compare, t.focus];
    const color = Object.fromEntries(fuentes.map((f, i) => [f.key, colors[i] ?? t.ink2]));
    const label = Object.fromEntries(fuentes.map((f) => [f.key, f.label]));
    const medidos = rows.filter((d) => d.obs_status !== "I");
    // Tramos imputados: cada corrida de I más el punto medido adyacente (para no dejar huecos).
    const imputados = [];
    for (const f of fuentes) {
      const r = rows.filter((d) => d.fuente === f.key);
      r.forEach((d, i) => {
        if (d.obs_status !== "I") return;
        const prev = r[i - 1], next = r[i + 1];
        const seg = `${f.key}-imp-${i}`;
        if (prev) imputados.push({ ...prev, seg });
        imputados.push({ ...d, seg });
        if (next) imputados.push({ ...next, seg });
      });
    }
    const last = fuentes.map((f) => rows.filter((d) => d.fuente === f.key).at(-1)).filter(Boolean);
    const rupt = (data.rupturas ?? []).map((p) => ({ year: +p }));
    const fig = Plot.plot({
      document: doc, width, height: Math.round(Math.min(400, Math.max(280, width * 0.5))),
      marginLeft: 44, marginRight: 150, marginTop: 30, style: baseStyle(t),
      x: { label: null, tickFormat: "d", ticks: Math.max(4, Math.floor(width / 110)) },
      y: { label: unidad, labelAnchor: "top", domain: [0, 100], ticks: 5 },
      marks: [
        Plot.gridY({ stroke: t.grid, strokeOpacity: 1, ticks: 5 }),
        Plot.ruleY([0], { stroke: t.axis }),
        Plot.ruleX(rupt, { x: (d) => d.year - 1, stroke: t.axis, strokeDasharray: "3,3" }),
        Plot.text(rupt, { x: (d) => d.year - 1, frameAnchor: "top", dy: -16, textAnchor: "middle",
          fill: t.muted, fontSize: 10, text: () => "Cambio de encuesta" }),
        Plot.lineY(imputados, { x: "year", y: "value", z: "seg", stroke: (d) => color[d.fuente],
          strokeWidth: 1.5, strokeDasharray: "2,3" }),
        Plot.lineY(medidos, { x: "year", y: "value", z: (d) => `${d.fuente}-${d.tramo}`,
          stroke: (d) => color[d.fuente], strokeWidth: 2 }),
        Plot.dot(rows.filter((d) => d.fuente === "encuesta"), { x: "year", y: "value", r: 3,
          fill: (d) => color[d.fuente], stroke: t.surface, strokeWidth: 1.5 }),
        Plot.text(last, { x: "year", y: "value", dx: 8, textAnchor: "start", fill: t.ink, lineWidth: 12,
          text: (d) => `${label[d.fuente]}: ${fmt1.format(d.value)} %` }),
        Plot.tip(rows, Plot.pointer({ x: "year", y: "value", fill: t.surface, stroke: t.axis,
          title: (d) => `${label[d.fuente]} · ${d.period}\n${fmt1.format(d.value)} %` +
            (d.obs_status === "I" ? "\nImputado por la fuente (no es una medición)" : "") +
            (d.obs_status === "B" ? "\nInicio de un nuevo tramo comparable" : "") })),
      ],
    });
    fig.setAttribute("role", "img");
    fig.setAttribute("aria-label", fuentes.map((f) => label[f.key]).join(" frente a ") + ".");
    return el("div", {}, [
      el("div", { class: "obs-legend" }, [
        ...fuentes.map((f) => el("span", {}, [el("i", { class: "obs-key-line", style: `border-color:${color[f.key]}` }), f.label])),
        el("span", {}, [el("i", { class: "obs-key-line", style: `border-color:${t.ink2};border-top-style:dotted` }), "Imputado por la fuente"]),
      ]),
      fig,
    ]);
  }

  return { legend, serieDistribucion, multiplesReferencia, abanico, lineasTramos, pesas,
    panelesDefiniciones, dosFuentes, procedencia, advertencias };
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
