#!/usr/bin/env python3
"""CEGH Day-Ahead-Export holen und data/ceghix.csv mergen (Lieferstag + CEGHIX)."""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATHS = [ROOT / "data" / "ceghix.csv", ROOT / "docs" / "data" / "ceghix.csv"]
URL = "https://www.cegh.at/wp-admin/admin-ajax.php?action=exportPosts&postType=day-ahead&market=AT"
HEADER = """# CEGHIX — EEX European Gas Spot Index, CEGH VTP Austria
# Volumengewichteter Durchschnittspreis der Day-Ahead- und Wochenendkontrakte, EUR/MWh.
# Quelle: CEGH Day-Ahead-Export (live) + Historie
# Format: JJJJ-MM-TT;Preis
"""


def num(s: str):
    s = (s or "").strip()
    if not s or s == "-":
        return None
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def parse_export(text: str) -> dict[str, float]:
    da, we = {}, {}
    for line in text.splitlines():
        cols = line.split(";")
        if len(cols) < 11:
            continue
        contract = cols[1].strip()
        ix = num(cols[10])
        if ix is None:
            ix = num(cols[9])
        if ix is None:
            continue
        m_da = re.search(r"CEGH VTP DA (\d{4}-\d{2}-\d{2})", contract, re.I)
        if m_da:
            da[m_da.group(1)] = ix
            continue
        m_we = re.search(r"CEGH VTP WE (\d{4}-\d{2}-\d{2})/(\d{2})", contract, re.I)
        if m_we:
            a = m_we.group(1)
            b = a[:8] + m_we.group(2)
            we.setdefault(a, ix)
            we.setdefault(b, ix)
    for d, v in we.items():
        da.setdefault(d, v)
    return da


def parse_existing(path: Path) -> dict[str, float]:
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"(\d{4}-\d{2}-\d{2})[;,\t ]+(-?[\d.,]+)", line)
        if not m:
            continue
        v = num(m.group(2))
        if v is not None:
            out[m.group(1)] = v
    return out


def write_csv(path: Path, data: dict[str, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [HEADER.rstrip(), ""]
    for day in sorted(data):
        lines.append(f"{day};{data[day]:.3f}".replace(".", ","))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    req = urllib.request.Request(URL, headers={"User-Agent": "Xolvix-Spotpreis/1.0", "Accept": "text/csv,*/*"})
    with urllib.request.urlopen(req, timeout=40) as r:
        text = r.read().decode("utf-8", "replace")
    live = parse_export(text)
    if not live:
        raise SystemExit("CEGH-Export ohne CEGHIX-Werte")
    merged = {}
    for p in CSV_PATHS:
        merged.update(parse_existing(p))
    merged.update(live)
    for p in CSV_PATHS:
        write_csv(p, merged)
    print(f"OK {len(live)} live / {len(merged)} gesamt")


if __name__ == "__main__":
    main()
