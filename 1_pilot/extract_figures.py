"""Extract every chart image embedded in pilot_analysis.ipynb into figures/.

Run from this folder after (re-)executing the notebook:
    .venv/bin/python extract_figures.py
"""
import base64
import sys
from pathlib import Path

import nbformat

NOTEBOOK_PATH = "pilot_analysis.ipynb"
OUTPUT_DIR = "figures"


def main():
    nb = nbformat.read(NOTEBOOK_PATH, as_version=4)

    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(exist_ok=True)

    last_heading = "figure"
    count = 0
    for cell in nb.cells:
        if cell.cell_type == "markdown":
            for line in cell.source.splitlines():
                if line.startswith("#"):
                    last_heading = line.lstrip("#").strip()
            continue
        if cell.cell_type != "code":
            continue
        for out in cell.get("outputs", []):
            if out.get("output_type") == "display_data" and "image/png" in out.get("data", {}):
                count += 1
                safe = "".join(c if c.isalnum() else "_" for c in last_heading).strip("_").lower()
                fname = out_dir / f"{count:02d}_{safe}.png"
                fname.write_bytes(base64.b64decode(out["data"]["image/png"]))
                print(fname)

    if count == 0:
        print("No chart images found — has the notebook been executed?", file=sys.stderr)
        sys.exit(1)
    print(f"{count} images written to {out_dir}/")


if __name__ == "__main__":
    main()
