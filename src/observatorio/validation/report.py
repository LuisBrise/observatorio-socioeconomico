"""Reportes de validación (JSON para máquinas, Markdown para personas)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from observatorio.validation.checks import ERROR, INFO, WARN, CheckResult

ORDER = {ERROR: 0, WARN: 1, INFO: 2}


def status(results: list[CheckResult]) -> str:
    sev = {r.severity for r in results}
    if ERROR in sev:
        return "error"
    if WARN in sev:
        return "advertencia"
    return "ok"


def write_report(results: list[CheckResult], out_dir: Path, header: dict) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    ordered = sorted(results, key=lambda r: ORDER.get(r.severity, 9))
    summary = {**header, "status": status(results),
               "counts": {s: sum(r.severity == s for r in results) for s in ORDER},
               "results": [asdict(r) for r in ordered]}
    (out_dir / "report.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    lines = [f"# Validación · {header.get('dataset_id')} · {header.get('vintage_id')}", "",
             f"Estado: **{summary['status']}** · "
             + " · ".join(f"{k}: {v}" for k, v in summary["counts"].items()), ""]
    if not ordered:
        lines.append("Sin hallazgos.")
    for r in ordered:
        lines.append(f"- **{r.severity}** `{r.check}` — {r.message}"
                     + (f" ({r.count})" if r.count else ""))
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary
