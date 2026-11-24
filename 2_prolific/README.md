# 2 Online study (Prolific)

Between-subjects comparison of unfolded vs. (edge-)folded BioFabric (Origraphi) with participants
recruited on Prolific. 258 participant IDs in the export; 107 completed the study and 104 are analysed
(52 per condition).

## Contents

| File | Contents |
|---|---|
| `data/biofabric-study_prolific_tidy.csv` | reVISit export: one row per participant × trial × response |
| `study_analysis.ipynb` | Exclusions, exploration and hypothesis tests |
| `biofab_stats.py` | Preprocessing, exclusions, tests and LaTeX table, used by the notebook |
| `estimation_graph_truth.csv` | True edge count of each task 3 graph, used to score the estimates |
| `results/study_results.csv` | Every test with estimates, CIs, p-values and effect sizes |
| `results/study_results_table.tex` | LaTeX table of the three primary results, as in the paper (needs `booktabs` and the paper's `\hyp` and `\task` macros) |
| `results/study_results_by_task.tex` | LaTeX table of all results per measure and task: per-condition values, differences with CIs, p and outcomes (full page width; same macros) |
| `results/study_session_progress.csv` | Per participant: completion status, how far they got, trials per task; `test_session` marks sessions that were not real participants |
| `figures/*.svg` | Every figure in the notebook (text stays editable) |
| `requirements.txt` | Python packages |

## Running

Requires Python 3.12 or newer. From this folder:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/jupyter notebook study_analysis.ipynb
```

Run all cells. This re-creates `results/study_results.csv`, `results/study_results_table.tex` and
`figures/`. All settings (margins, exclusion thresholds) are in the first code cell.

## Hypotheses and tests

| | Hypothesis | Test |
|---|---|---|
| H1 | Folding preserves task accuracy | TOST (Welch) on overall accuracy, margin ±5 points; bootstrap CI as check |
| H2 | Folding does not meaningfully affect perceived workload (RTLX) | TOST (Welch) on overall RTLX, margin ±10 points; bootstrap CI as check |
| H3 | Folding shortens response times on the common-neighbors task (task 2) | One-sided Mann-Whitney U; Hodges-Lehmann shift, rank-biserial r |

- Each test uses one value per participant: the mean of the 3 trials per task (median for
  response times). `overall` is the mean of a participant's three tasks.
- Each hypothesis is decided by one primary test, which is not corrected for multiple comparisons.
- All other tests are exploratory: the per-task tests for H1 and H2, and the task 1, task 3 and
  overall response-time comparisons for H3 (two-sided). They are Holm-corrected within each hypothesis.
- Differences are folded − unfolded.

## Exclusions

| Level | Rule | Effect |
|---|---|---|
| Participant | Incomplete session | excluded |
| Participant | Any failed attention check | excluded |
| Participant | Median trial time under 8 s (click-through) | excluded |
| Trial | Response time under 3 s | trial dropped |
| Trial | Response time above the task median + 3 MAD (log scale) | response time dropped, accuracy kept |

Response times use reVISit's `cleanedDuration`, which excludes time the browser tab was hidden.

## Data

- Participant IDs are pseudonyms (`P001`–`P258`).
- The export records the conditions as `collapsed` (folded) and `normal` (unfolded);
  `biofab_stats.py` relabels them when loading the data.
- Tasks 1 and 2 have their correct answers in the export. Task 3 (edge-count estimation) is
  scored as 100 − the absolute percentage error, against `estimation_graph_truth.csv`.
