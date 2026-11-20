#!/usr/bin/env python3
"""Scan library/ for .zip packages, unpacked folders (paper.json), and legacy .html files,
and generate a rich catalog.json index for Universal Bilingual Reader."""

import json
import os
import re
import zipfile
from datetime import datetime, timezone

LIBRARY_DIR = "library"
OUT_FILE = "catalog.json"


def format_authors(raw_authors):
    if isinstance(raw_authors, list):
        names = []
        for a in raw_authors:
            if isinstance(a, str) and a.strip():
                names.append(a.strip())
            elif isinstance(a, dict) and str(a.get("name", "")).strip():
                names.append(str(a["name"]).strip())
        return ", ".join(names)
    return str(raw_authors or "").strip()


def parse_tags(subjects):
    if not subjects:
        return []
    parts = [p.strip() for p in re.split(r"[,;、]+", str(subjects)) if p.strip()]
    return list(dict.fromkeys(parts))


def extract_summary(paper_obj):
    blocks = paper_obj.get("blocks") or []
    for b in blocks:
        if isinstance(b, dict) and b.get("type") == "abstract":
            txt = str(b.get("zh") or b.get("en") or "").strip()
            txt = re.sub(r"<[^>]+>", "", txt)
            txt = re.sub(r"\s+", " ", txt).strip()
            if len(txt) > 120:
                txt = txt[:118].rstrip() + "…"
            return txt
    return ""


def build_entry(file_rel, kind, paper_obj):
    meta = (paper_obj.get("meta") or {}) if isinstance(paper_obj, dict) else {}
    return {
        "file": file_rel,
        "kind": kind,
        "docId": str(meta.get("docId") or "").strip(),
        "sourceLabel": str(meta.get("sourceLabel") or "").strip(),
        "titleEn": str(meta.get("titleEn") or "").strip(),
        "titleZh": str(meta.get("titleZh") or "").strip(),
        "authors": format_authors(meta.get("authors")),
        "venue": str(meta.get("venue") or "").strip(),
        "date": str(meta.get("date") or meta.get("submitted") or "").strip(),
        "tags": parse_tags(meta.get("subjects")),
        "summary": extract_summary(paper_obj),
    }


def read_zip_paper(zip_path):
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = [n for n in zf.namelist() if not n.endswith("/") and not n.startswith("__MACOSX/")]
        json_names = [n for n in names if n.lower().endswith(".json") and not n.lower().endswith("annotations.json")]
        if not json_names:
            return {}
        json_names.sort(key=lambda n: (0 if n.lower().endswith("doc.json") else (1 if n.lower().endswith("paper.json") else 2), len(n)))
        return json.loads(zf.read(json_names[0]).decode("utf-8"))


def read_html_paper(html_path):
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    m = re.search(r'<script[^>]*\bid=["\']paper-data["\'][^>]*>([\s\S]*?)</script>', text, re.I)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    t = re.search(r"<title[^>]*>([\s\S]*?)</title>", text, re.I)
    return {"meta": {"titleEn": re.sub(r"\s+", " ", t.group(1)).strip()}} if t else {}


def main():
    items = []
    if os.path.isdir(LIBRARY_DIR):
        for name in sorted(os.listdir(LIBRARY_DIR)):
            if name.startswith(".") or name.startswith("__"):
                continue
            full = os.path.join(LIBRARY_DIR, name)
            try:
                if os.path.isfile(full) and name.lower().endswith(".zip"):
                    items.append(build_entry(name, "zip", read_zip_paper(full)))
                elif os.path.isdir(full):
                    json_cand = os.path.join(full, "doc.json")
                    if not os.path.isfile(json_cand):
                        json_cand = os.path.join(full, "paper.json")  # [compat <= 1.1.0]
                    if os.path.isfile(json_cand):
                        with open(json_cand, "r", encoding="utf-8") as f:
                            items.append(build_entry(name + "/", "folder", json.load(f)))
                elif os.path.isfile(full) and name.lower().endswith((".html", ".htm")):
                    items.append(build_entry(name, "html", read_html_paper(full)))
            except Exception as exc:
                print(f"[warn] skipped {name}: {exc}")

    items.sort(key=lambda x: (x.get("date") or "", x.get("titleEn") or x.get("file") or ""), reverse=True)

    payload = {
        "dir": LIBRARY_DIR,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "items": items,
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Generated {OUT_FILE} with {len(items)} item(s).")


if __name__ == "__main__":
    main()
