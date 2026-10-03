# 10 · Información que necesito antes de comenzar

Para cada pregunta propongo una respuesta por defecto. Si estás de acuerdo con ella, basta con confirmar.

## A. Propósito y audiencia

| # | Pregunta | Propuesta por defecto |
|---|---|---|
| A1 | ¿Para quién es el observatorio? (uso personal de investigación, docencia, sitio público, publicación académica) | Herramienta de investigación propia con sitio público, cuidando su calidad desde el inicio. |
| A2 | ¿Idioma? | Español; nombres de variables y código en inglés técnico o español consistente (propongo: código en inglés, contenido en español). |
| A3 | ¿Repositorio y sitio públicos o privados? | Repositorio público (CI gratuito y transparencia); datos con restricciones de licencia fuera del repositorio. |
| A4 | Licencias del proyecto | Código: MIT. Contenido y datos derivados: CC BY 4.0 (salvo lo que restrinjan las fuentes). |
| A5 | ¿Cuáles son las 5–10 preguntas que más te importan? | Las preguntas rectoras de [02 · Arquitectura §2](02-arquitectura.md#2-preguntas-analíticas-rectoras). Tus preguntas propias ayudarían mucho a priorizar. |

## B. Alcance analítico

| # | Pregunta | Propuesta por defecto |
|---|---|---|
| B1 | Horizonte histórico prioritario | 1980–hoy para la mayoría de los análisis; 1950 o antes cuando las fuentes lo permitan (Maddison, V-Dem). |
| B2 | Países de ALC prioritarios | Los 33 de CEPAL en los datos; en las visualizaciones, foco en `G.ALC_GRANDES`. |
| B3 | Comparadores fuera de ALC | Pares estructurales por regla + EE.UU., Canadá, China, OCDE. ¿Hay países que quieras incluir siempre (p. ej., España, Corea, Turquía, Polonia)? |
| B4 | Profundidad subnacional en México | Estados en la fase 2; municipios solo para seguridad y elecciones en la fase 3. |
| B5 | Tercer dashboard: ¿democracia e instituciones (recomendado) o violencia letal? | Democracia e instituciones; violencia letal como D4. |
| B6 | ¿Incluir encuestas de aprobación presidencial y de intención de voto? | Aprobación sí (fase 2, agregada con modelo y con incertidumbre); intención de voto no (riesgo de percepción de influencia electoral). |
| B7 | Criterios para la línea de tiempo de eventos: ¿quién los valida? | Yo propongo los criterios y la lista; tú validas antes de publicar. |

## C. Recursos y operación

| # | Pregunta | Propuesta por defecto |
|---|---|---|
| C1 | ¿Con qué lenguajes te sientes cómodo/a? (Python, R, JavaScript, SQL) | Python como base; JavaScript solo dentro de los componentes visuales. Si dominas R, lo usamos para microdatos con diseño muestral. |
| C2 | ¿Dónde ejecutarás el sistema? (computadora propia — ¿qué sistema operativo? —, servidor, solo en la nube) | Desarrollo local + CI en GitHub Actions. |
| C3 | Presupuesto mensual | US$0–5/mes (almacenamiento de objetos + dominio opcional). |
| C4 | ¿Dónde archivamos los datos crudos? | Cloudflare R2 (10 GB gratis) o Backblaze B2. Necesitaría que crees la cuenta y agregues las credenciales como secretos del repositorio. |
| C5 | Tokens de API | Necesito que solicites (son gratuitos): **token de INEGI** (API del Banco de Indicadores) y **token de Banxico** (SIE). Más adelante: UN Comtrade, ACLED y registro en Latinobarómetro y LAPOP. |
| C6 | ¿Cuánto tiempo semanal puedes dedicar a revisión? | 30–60 minutos semanales para revisar PR de datos y avances. |
| C7 | ¿Las actualizaciones rutinarias se publican automáticamente o siempre con tu aprobación? | Automáticas si pasan todos los controles; revisión humana si hay advertencias. |

## D. Diseño

| # | Pregunta | Propuesta por defecto |
|---|---|---|
| D1 | Referentes visuales que te gusten (p. ej., Financial Times, The Economist, Our World in Data, The Pudding, Datawrapper, Nexos, El País) | Sobriedad tipo FT/OWID, con narrativa tipo Pudding en piezas especiales. |
| D2 | ¿Nombre y marca del observatorio? | "Observatorio socioeconómico" (provisional). |
| D3 | ¿Modo oscuro? | Sí, desde el inicio (es más barato diseñarlo desde el principio). |
| D4 | ¿Publicar también informes en PDF? | Sí, en la fase 2, con Quarto. |

## E. Decisiones que necesito confirmar para avanzar a la etapa 2–3

1. **Stack:** Python + DuckDB + Polars + Parquet; Quarto + Observable Plot; GitHub Actions. ([04 · Stack](04-stack.md))
2. **Estructura del repositorio** propuesta en [02 · Arquitectura §7](02-arquitectura.md#7-estructura-del-repositorio).
3. **Los tres primeros dashboards** (y la elección de D3).
4. **Archivo de datos crudos:** R2, B2 u otra opción.
5. **Tokens** de INEGI y Banxico (pueden llegar después; el primer corte vertical usará el Banco Mundial, que no requiere token).

## Siguiente paso propuesto (al confirmar)

**Primera rebanada vertical:** estructura del proyecto + esquemas del catálogo + un conector
(Banco Mundial WDI) recorriendo todo el pipeline (raw → staging → validación → processed →
transformación → dataset de visualización con procedencia) hasta **una gráfica** publicada en
el sitio Quarto, con CI funcionando. Si ese corte funciona de punta a punta, el resto es
agregar fuentes, indicadores y componentes sobre una base probada.
