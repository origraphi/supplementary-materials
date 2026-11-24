# Supplementary Material: Origraphi

**Origraphi** is our approach to folding graphs with BioFabric. The name is inspired by
*origami*, which joins two Japanese words: *ori* (折り), "to fold", and *gami* (紙, from *kami*),
"paper". Just as origami is the art of folding paper, Origraphi is the art of folding graphs
using BioFabric.

## Conditions

| Name              | What it shows                                                             | Used in                        |
|-------------------|---------------------------------------------------------------------------|--------------------------------|
| **Unfolded**      | Standard BioFabric: every edge has its own lane                           | pilot, online study, benchmark |
| **(Edge-)folded** | Origraphi edge folding: consecutive edges from the same node share a lane | pilot, online study, benchmark |
| **Fully folded**  | Further folding (see the paper)                                           | expert study                   |

The study software and its raw exports record the unfolded and folded conditions as `normal`
and `collapsed`. The analyses relabel them as `unfolded` and `folded`.

## Contents

Each folder is self-contained: it has its own README and its own dependencies.

| Folder                                        | Phase          | What it contains                                                      | Runs with             |
|-----------------------------------------------|----------------|-----------------------------------------------------------------------|-----------------------|
| [`0_benchmark/`](0_benchmark/README.md)       | 0 Benchmark    | How many edge lanes folding saves on benchmark graph collections      | uv (Python 3.12)      |
| [`demo/`](demo/README.md)                     | –              | Interactive Origraphi demo                                            | a web browser         |
| [`revisit/`](revisit/README.md)               | 1, 2           | Study setup on the reVISit platform (tasks, tutorial, questionnaires) | Node.js + yarn        |
| [`1_pilot/`](1_pilot/README.md)               | 1 Pilot        | Pilot study data, analysis notebook and figures                       | Python venv + Jupyter |
| [`2_prolific/`](2_prolific/README.md)         | 2 Online study | Prolific study data, hypothesis tests, results table and figures      | Python venv + Jupyter |
| [`3_expert_study/`](3_expert_study/README.md) | 3 Expert study | Expert interviews (German and English) and qualitative coding         | –                     |

```
.
├── README.md                          this file
├── 0_benchmark/                       edge-lane statistics (bfstats, bfplot)
│   ├── README.md
│   ├── pyproject.toml, uv.lock
│   └── src/biofabric_collapse_stats/
├── demo/                              interactive Origraphi
│   ├── README.md
│   ├── index.html, style.css
│   ├── src/js/
│   └── data/                          example networks and study graphs
├── revisit/                           study setup (reVISit)
│   ├── README.md
│   └── public/biofabric-study/         our study: configuration, texts, stimuli, graphs
├── 1_pilot/
│   ├── README.md, requirements.txt
│   ├── pilot_analysis.ipynb
│   ├── extract_figures.py
│   ├── estimation_graph_truth.csv     true edge counts for task 3
│   ├── data/                          pilot responses (reVISit export)
│   └── figures/                       charts (PNG)
├── 2_prolific/
│   ├── README.md, requirements.txt
│   ├── study_analysis.ipynb
│   ├── biofab_stats.py                preprocessing, exclusions and tests
│   ├── estimation_graph_truth.csv     true edge counts for task 3
│   ├── data/                          study responses (reVISit export)
│   ├── results/                       test results (CSV, LaTeX) and completion report
│   └── figures/                       charts (SVG)
└── 3_expert_study/
    ├── README.md
    ├── interviews/original_de/        transcripts (German)
    ├── interviews/translated_en/      transcripts (English translation)
    └── coding/                        qualitative coding
```

## Studies at a glance

| Phase                     | Participants                    | Design                                                           |
|---------------------------|---------------------------------|------------------------------------------------------------------|
| 0 Benchmark               | –                               | lane counts, unfolded vs. folded, on benchmark graph collections |
| 1 Pilot                   | 15 with a complete session      | unfolded vs. folded, between subjects                            |
| 2 Online study (Prolific) | 104 analysed (52 per condition) | unfolded vs. folded, between subjects                            |
| 3 Expert study            | see `3_expert_study/`           | interviews with unfolded, folded and fully folded versions       |

The pilot and the online study use the same three tasks: (1) select all nodes connected to a
highlighted node, (2) select all common neighbors of two highlighted nodes, and (3) estimate the
number of edges in a graph. NASA-TLX was collected after each task block.

## Participant data and anonymization

- Participant IDs in the pilot and online-study files are pseudonyms (`PILOT01`–`PILOT27` in the pilot, `P001`–`P258` in the online study); the data contains no other personal information.
- For review, author names, affiliations and contact details, the Prolific completion codes and all database credentials have been replaced with placeholders.
- Python environments are not included; each folder's README explains how to create one.