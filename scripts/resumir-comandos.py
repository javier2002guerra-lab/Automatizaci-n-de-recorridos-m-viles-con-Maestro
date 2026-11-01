"""Resume los commands.json generados por Maestro: estado de cada comando por flujo.

Uso: python scripts/resumir-comandos.py
"""
import collections
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "resultados" / "ejecuciones"

for f in sorted(RAIZ.glob("*/maestro/**/commands.json")):
    datos = json.loads(f.read_text(encoding="utf-8"))
    estados = collections.Counter(c.get("metadata", {}).get("status") for c in datos)
    tipos = collections.Counter(next((k for k, v in c["command"].items() if v is not None), "?") for c in datos)
    verif = sum(n for k, n in tipos.items() if "assert" in k.lower() or "wait" in k.lower())
    ejecucion = f.relative_to(RAIZ).parts[0]
    print(f"{ejecucion:36} {f.parent.name[:13]:14} comandos={len(datos):3} "
          f"verificaciones={verif:3} estados={dict(estados)}")
