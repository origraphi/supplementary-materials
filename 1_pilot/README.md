# 1 Pilot study

Pilot of the online study: unfolded vs. (edge-)folded BioFabric (Origraphi), between subjects. It was used to
check the study setup and to estimate effect sizes and sample sizes for the online study.

## Contents

| File | Contents |
|---|---|
| `data/biofabric-study-pilot_all_tidy.csv` | reVISit export: one row per participant × trial × response |
| `pilot_analysis.ipynb` | Response times, accuracy and NASA-TLX per task and condition; effect sizes and bootstrap power analysis |
| `estimation_graph_truth.csv` | True edge count of each task 3 graph, used to score the estimates |
| `extract_figures.py` | Saves every chart in the notebook to `figures/` |
| `figures/*.png` | Charts from the notebook |
| `requirements.txt` | Python packages |

## Running

Requires Python 3.12 or newer. From this folder:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/jupyter notebook pilot_analysis.ipynb
```

Run all cells. To re-create the PNG files afterwards: `.venv/bin/python extract_figures.py`.

## Data

- 27 participant IDs in the export, 15 with a complete session (9 folded, 6 unfolded).
  An automated test run of the survey was removed from the export.
- Participant IDs are pseudonyms (`PILOT01`–`PILOT27`).
- The export records the conditions as `collapsed` (folded) and `normal` (unfolded); the notebook
  relabels them when loading the data.
- Tasks 1 and 2 have their correct answers in the export. Task 3 (edge-count estimation)
  is scored as 100 − the absolute percentage error, against `estimation_graph_truth.csv`.
