# 0 Benchmark: edge-lane savings of Origraphi edge folding

Computes how many horizontal edge lanes Origraphi edge folding saves compared with unfolded
BioFabric, where every edge gets its own lane.

1. Nodes are ordered by incidence.
2. Edges are ordered "degreecending": by their topmost node in the incidence-ordered node list, then by edge length.
3. The unfolded layout assigns one horizontal lane to every edge.
4. The folded layout reuses a lane for consecutive edges with the same topmost node. `partially collapsed lanes` is the number of edges placed into an already-used lane.

Every graph is assumed to have a single depth layer. The tool predates the name Origraphi:
its output calls the unfolded layout "uncollapsed" and the folded layout "partially collapsed".

## Contents

| File                                           | Contents                                                                  |
|------------------------------------------------|---------------------------------------------------------------------------|
| `src/biofabric_collapse_stats/bfstats.py`      | Lane statistics per graph and in total (`bfstats`)                        |
| `src/biofabric_collapse_stats/visualize.py`    | Plots of the statistics (`bfplot`)                                        |
| `pyproject.toml`, `uv.lock`, `.python-version` | Dependencies, pinned for [uv](https://docs.astral.sh/uv/) and Python 3.12 |

## Running

Requires [uv](https://docs.astral.sh/uv/); it creates the environment on first run.

```bash
uv run bfstats path/to/data
uv run bfplot rome/data randDAG/data north/data -o collapse_visualizations.svg
```

- `bfstats` takes a folder of node-link `.json` graphs and prints, per graph and in total or on average: the edge count (unfolded lanes), the folded lane count, the layered edges and the lane savings. Without an argument it reads `rome/data`.
- `bfplot` plots the statistics for one or more folders (by default `rome/data`, `randDAG/data` and `north/data`). The output can be PNG, SVG, PDF or any other format Matplotlib supports.

## Datasets

The benchmark datasets (Rome, randDAG, At&T north) are **not included**. Place them as
node-link `.json` files in `rome/data/`, `randDAG/data/` and `north/data/` inside this folder.

You can download the different datasets from <https://visdunneright.github.io/gd_benchmark_sets/>. You need to download them as JSON formatted data. Finally, extract the downloaded zip in the base directory of this project.
