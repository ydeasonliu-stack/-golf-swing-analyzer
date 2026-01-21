import json
import os
from typing import Optional

from openpyxl import Workbook


def export_index_to_excel(index_path: str, excel_path: Optional[str] = None):
    """Read an index.json created by the generator and export scripts+meta to an Excel file.

    Produces one sheet per length (15/30/60) with columns:
    product, audience, benefits, tone, length, script, script_file, meta_file, generated_at
    """
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    outputs = index.get("outputs", {})
    product = index.get("product", "")

    if excel_path is None:
        base = os.path.splitext(index_path)[0]
        excel_path = base + "_scripts.xlsx"

    wb = Workbook()
    # remove default sheet
    default = wb.active
    wb.remove(default)

    for length_key, info in outputs.items():
        # length_key in JSON is a string like '15' — convert to int for clarity
        try:
            key = int(length_key)
        except Exception:
            # skip unexpected keys
            continue
        text_path = info.get("text")
        meta_path = info.get("meta")

        script_text = ""
        meta = {}
        if text_path and os.path.exists(text_path):
            with open(text_path, "r", encoding="utf-8") as f:
                script_text = f.read()
        if meta_path and os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

        sheet = wb.create_sheet(title=f"{key}s")
        headers = [
            "product",
            "audience",
            "benefits",
            "tone",
            "length",
            "script",
            "script_file",
            "meta_file",
            "generated_at",
        ]
        sheet.append(headers)

        row = [
            meta.get("product", product),
            meta.get("audience", ""),
            (", ".join(meta.get("benefits", [])) if meta.get("benefits") else ""),
            meta.get("tone", ""),
            meta.get("length", key),
            script_text,
            os.path.basename(text_path) if text_path else "",
            os.path.basename(meta_path) if meta_path else "",
            meta.get("generated_at", index.get("generated", "")),
        ]
        sheet.append(row)

    wb.save(excel_path)
    return excel_path


def export_folder(output_dir: str, excel_path: Optional[str] = None):
    idx_candidates = [
        os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith("_index.json")
    ]
    if not idx_candidates:
        raise FileNotFoundError("No index.json found in output directory")
    # pick first
    index_path = idx_candidates[0]
    return export_index_to_excel(index_path, excel_path=excel_path)


if __name__ == "__main__":
    # quick local test (no-op if not present)
    import sys

    if len(sys.argv) > 1:
        out = sys.argv[1]
    else:
        out = "./output_maotai"
    try:
        p = export_folder(out)
        print("Excel exported:", p)
    except Exception as e:
        print("Export failed:", e)
