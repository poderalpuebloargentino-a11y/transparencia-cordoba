#!/usr/bin/env python3
"""
Monitor de Transparencia - Datos Abiertos de la Municipalidad de Córdoba
=======================================================================
Corre periódicamente (GitHub Actions). En cada corrida:
  1. Lee el catálogo completo de datos abiertos.
  2. Para cada dataset registra: última actualización, periodicidad declarada,
     categoría, si su PÁGINA oficial abre o da error, y si su ARCHIVO descarga.
  3. Reconstruye index.html (la página pública) con los datos del día.
  4. Guarda un snapshot fechado en data/historial/  ->  evidencia reproducible.

A diferencia de un entorno restringido, los runners de GitHub tienen salida
abierta a internet, así que ACÁ sí se puede verificar la descarga real de los
archivos alojados en S3. Honestidad: si un chequeo no llega al archivo por un
problema de red, se registra como "no verificado", nunca como "roto".
"""
import requests, json, datetime as dt, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://gobiernoabierto.cordoba.gob.ar"
UA   = "transparencia-cba-monitor/1.0 (auditoria ciudadana datos abiertos)"
ROOT = Path(__file__).resolve().parent.parent
HOY  = dt.datetime.now(dt.timezone.utc)

# Tolerancia por periodicidad declarada (período + margen). Ajustable.
UMBRALES = {"En tiempo real":7,"Cada quince días":21,"Mensual":45,
            "Trimestral":120,"Semestral":210,"Anual":430}

# Acentos para prettificar el slug de categoría.
ACC = {"economia":"Economía","geografia":"Geografía","educacion":"Educación",
       "poblacion":"Población","administracion":"Administración","publica":"Pública",
       "publicas":"Públicas","participacion":"Participación","informacion":"Información",
       "energia":"Energía","trafico":"Tráfico","transito":"Tránsito","gestion":"Gestión",
       "credito":"Crédito","planificacion":"Planificación"}

def sesion():
    s = requests.Session(); s.headers.update({"User-Agent": UA}); return s

def pretty_cat(url):
    if not url: return "—"
    parts = [p for p in url.split("/") if p]
    try: slug = parts[parts.index("categoria")+1]
    except (ValueError, IndexError): return "—"
    chico = {"y","de","del","la","el","los","las","en","por","a"}
    out = [w if w in chico else ACC.get(w, w.capitalize()) for w in slug.split("-")]
    s = " ".join(out)
    return (s[0].upper()+s[1:]) if s else "—"

def listar(s):
    items, url = [], f"{BASE}/api/datos-abiertos/dato?page=1"
    while url:
        r = s.get(url, timeout=15); r.raise_for_status(); d = r.json()
        items += d.get("results", [])
        url = d.get("next")
    return items

def dias(iso):
    if not iso: return None
    t = dt.datetime.fromisoformat(iso)
    if t.tzinfo is None: t = t.replace(tzinfo=dt.timezone.utc)
    return (HOY - t).days

def inspeccionar(meta):
    """Para un dataset: última modificación, estado de la página y de la descarga."""
    s = sesion(); did = meta["id"]
    rec = {"id":did, "t":meta.get("titulo"), "p":meta.get("periodicidad"),
           "c":pretty_cat(meta.get("url")), "u":(meta.get("url") or "").replace(BASE,""),
           "mod":None, "x":0, "dl":None, "err":""}
    # 1) última modificación
    try:
        vr = s.get(f"{BASE}/api/datos-abiertos/dato/{did}/version-dato", timeout=10)
        if vr.status_code == 200:
            res = vr.json().get("results", [])
            mods = [v.get("ultima_modificacion") or v.get("creado") for v in res]
            mods = [m for m in mods if m]
            rec["mod"] = max(mods) if mods else None
            # 3) descarga del primer recurso de la última versión
            if res:
                vid = res[0]["id"]
                rr = s.get(f"{BASE}/api/datos-abiertos/dato/{did}/version-dato/{vid}/recurso", timeout=10)
                recs = rr.json().get("results", []) if rr.status_code == 200 else []
                durl = next((x.get("url") for x in recs if x.get("url")), None)
                if durl:
                    full = durl if durl.startswith("http") else BASE+durl
                    try:
                        h = s.get(full, headers={"Range":"bytes=0-0"}, timeout=15, stream=True)
                        rec["dl"] = "ok" if h.status_code in (200,206) else f"http_{h.status_code}"
                    except Exception:
                        rec["dl"] = "no_verificado"   # no se pudo llegar: NO es "roto"
                else:
                    rec["dl"] = "sin_url"
        else:
            rec["err"] = f"version_http_{vr.status_code}"
    except Exception as e:
        rec["err"] = type(e).__name__
    # 2) estado de la página oficial (la que ve el ciudadano)
    if meta.get("url"):
        try:
            rec["x"] = 0 if s.get(meta["url"], timeout=10, stream=True).status_code == 200 else 1
        except Exception:
            rec["x"] = 0   # no verificado -> no afirmamos que está rota
    return rec

def main():
    s = sesion()
    print("Listando catálogo...", file=sys.stderr)
    metas = listar(s)
    print(f"  {len(metas)} datasets. Inspeccionando...", file=sys.stderr)

    recs = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, f in enumerate(as_completed([ex.submit(inspeccionar, m) for m in metas])):
            recs.append(f.result())
            if (i+1) % 100 == 0: print(f"  {i+1}/{len(metas)}", file=sys.stderr)

    # registros para la página (compactos) + clasificación de frescura
    page = []
    for r in recs:
        d = dias(r["mod"]); thr = UMBRALES.get(r["p"])
        page.append({"t":r["t"], "p":r["p"], "f":(r["mod"] or "")[:10],
                     "d":d, "v":bool(thr and d is not None and d>thr),
                     "c":r["c"], "u":r["u"], "x":r["x"]})

    fecha = HOY.date().isoformat()
    (ROOT/"data").mkdir(exist_ok=True)
    (ROOT/"data"/"historial").mkdir(parents=True, exist_ok=True)

    # data para la página
    (ROOT/"data"/"datos_tablero.json").write_text(
        json.dumps(page, ensure_ascii=False, separators=(",",":")), encoding="utf-8")

    # snapshot fechado (evidencia, con detalle de descargas)
    paginas_404 = sum(1 for r in recs if r["x"] == 1)
    desc_ok  = sum(1 for r in recs if r["dl"] == "ok")
    desc_mal = sum(1 for r in recs if r["dl"] and r["dl"].startswith("http_"))
    resumen = {"generado_utc":HOY.isoformat(), "total":len(recs),
               "paginas_404":paginas_404, "descargas_ok":desc_ok,
               "descargas_con_error":desc_mal,
               "vencidos":sum(1 for p in page if p["v"])}
    (ROOT/"data"/"historial"/f"{fecha}.json").write_text(
        json.dumps({"resumen":resumen, "datos":recs}, ensure_ascii=False), encoding="utf-8")

    # reconstruir la página pública
    tpl = (ROOT/"template.html").read_text(encoding="utf-8")
    html = tpl.replace("__DATA__", json.dumps(page, ensure_ascii=False, separators=(",",":"))) \
              .replace("__BUILT_DATE__", fecha)
    (ROOT/"index.html").write_text(html, encoding="utf-8")

    print(json.dumps(resumen, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
