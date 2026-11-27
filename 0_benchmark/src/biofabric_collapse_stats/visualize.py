"""Create publication-oriented plots for BioFabric lane collapse."""

from __future__ import annotations

import argparse
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Literal

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import EngFormatter

from .bfstats import GraphStats, calculate_dataset_stats


@dataclass(frozen=True)
class Dataset:
    """A named collection of graph statistics."""

    name: str
    stats: tuple[GraphStats, ...]


def _half_filled_circle_marker():
    """Return a circular marker whose lower half is filled."""
    from matplotlib.path import Path as MarkerPath

    control = 0.5522848
    return MarkerPath(
        vertices=[
            (1.0, 0.0),
            (1.0, -control),
            (control, -1.0),
            (0.0, -1.0),
            (-control, -1.0),
            (-1.0, -control),
            (-1.0, 0.0),
            (1.0, 0.0),
            (0.0, 0.0),
        ],
        codes=[
            MarkerPath.MOVETO,
            MarkerPath.CURVE4,
            MarkerPath.CURVE4,
            MarkerPath.CURVE4,
            MarkerPath.CURVE4,
            MarkerPath.CURVE4,
            MarkerPath.CURVE4,
            MarkerPath.LINETO,
            MarkerPath.CLOSEPOLY,
        ],
    )


def average_collapse_factor(dataset: Dataset) -> float:
    """Return aggregate uncollapsed-to-collapsed lane factor for a dataset."""
    uncollapsed = sum(row.uncollapsed_lanes for row in dataset.stats)
    collapsed = sum(row.partially_collapsed_lanes for row in dataset.stats)
    if collapsed == 0:
        raise ValueError(f"{dataset.name}: collapsed lane total cannot be zero")
    return uncollapsed / collapsed


def load_datasets(dataset_dirs: Iterable[Path]) -> list[Dataset]:
    """Calculate statistics for each non-empty dataset directory."""
    datasets = []
    for data_dir in dataset_dirs:
        datasets.append(
            Dataset(data_dir.parent.name, tuple(calculate_dataset_stats(data_dir)))
        )
    return datasets


def _percentile(values: Sequence[int], percentile: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


COLORS = (
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#E69F00",
    "#0C0B5B",
    "#F0E442",
    "#0DA927",
)
LANE_AXIS_FORMATTER = EngFormatter(places=0, sep="")


def _plot_degree_distribution(
    ax: Axes,
    dataset: Dataset,
    color: str,
    field: str,
    title: str,
    xlabel: str,
) -> None:
    """Plot an absolute degree distribution for one dataset."""
    values = [getattr(row, field) for row in dataset.stats]
    if not values:
        return
    minimum, maximum = min(values), max(values)
    bins = 12 if minimum != maximum else [minimum - 0.5, maximum + 0.5]
    ax.hist(
        values,
        bins=bins,
        alpha=0.65,
        color=color,
        edgecolor=color,
        linewidth=0.8,
    )
    ax.set(title=title, xlabel=xlabel, ylabel="")
    ax.yaxis.set_major_formatter(LANE_AXIS_FORMATTER)


def _plot_curve(
    ax: Axes,
    sizes: list[float],
    medians: list[float],
    color: str,
    *,
    collapsed: bool,
) -> None:
    """Plot a median curve with the matching layout marker."""
    if collapsed:
        ax.plot(
            sizes,
            medians,
            color=color,
            linestyle="--",
            marker="o",
            markerfacecolor="white",
            markeredgecolor=color,
            markersize=4,
        )
        ax.plot(
            sizes,
            medians,
            color=color,
            linestyle="none",
            marker=_half_filled_circle_marker(),
            markerfacecolor=color,
            markeredgecolor="none",
            markersize=4,
        )
        return
    ax.plot(
        sizes,
        medians,
        color=color,
        linestyle="-",
        marker="o",
        markerfacecolor="white",
        markeredgecolor=color,
        markersize=4,
    )


def _plot_binned_curves(
    ax: Axes, dataset: Dataset, color: str, max_bins: int = 12
) -> None:
    """Plot median lane counts in graph-size bins for any dataset."""
    rows = sorted(dataset.stats, key=lambda row: row.node_count)
    if not rows:
        return

    bin_size = max(1, math.ceil(len(rows) / max_bins))
    bins = [rows[start : start + bin_size] for start in range(0, len(rows), bin_size)]
    sizes = [median([row.node_count for row in group]) for group in bins]

    for field, collapsed in (
        ("uncollapsed_lanes", False),
        ("partially_collapsed_lanes", True),
    ):
        values = [[getattr(row, field) for row in group] for group in bins]
        medians = [median(group) for group in values]
        lower = [_percentile(group, 0.25) for group in values]
        upper = [_percentile(group, 0.75) for group in values]
        _plot_curve(ax, sizes, medians, color, collapsed=collapsed)
        ax.fill_between(sizes, lower, upper, color=color, alpha=0.10)


def _plot_lane_curves(
    ax: Axes,
    datasets: Sequence[Dataset],
    *,
    scale: Literal["linear", "log"],
) -> None:
    """Plot binned median lane counts and interquartile ranges."""
    for index, dataset in enumerate(datasets):
        _plot_binned_curves(ax, dataset, COLORS[index % len(COLORS)])

    ax.set(
        title="Median lanes by graph-size bin",
        xlabel="Nodes",
        ylabel="Lanes",
    )
    ax.set_xscale(scale)
    ax.set_yscale(scale)
    ax.yaxis.set_major_formatter(LANE_AXIS_FORMATTER)


def _plot_lane_distributions(ax: Axes, datasets: Sequence[Dataset]) -> None:
    """Plot uncollapsed and partially collapsed lane distributions."""
    positions = []
    box_values = []
    box_colors = []
    for index, dataset in enumerate(datasets):
        center = index * 3 + 1.5
        color = COLORS[index % len(COLORS)]
        positions.extend((center - 0.4, center + 0.4))
        box_values.extend(
            (
                [row.uncollapsed_lanes for row in dataset.stats],
                [row.partially_collapsed_lanes for row in dataset.stats],
            )
        )
        box_colors.extend((color, color))

    if box_values:
        ax.boxplot(
            box_values,
            positions=positions,
            widths=0.65,
            patch_artist=True,
            boxprops={"alpha": 0.7},
            medianprops={"color": "#222222", "linewidth": 1.5},
            flierprops={"marker": ".", "markersize": 2, "alpha": 0.15},
        )
        for index, (patch, color) in enumerate(zip(ax.patches, box_colors)):
            patch.set_facecolor("white")
            patch.set_hatch("oo" if index % 2 == 0 else "..")
            patch.set_edgecolor(color)

    ax.set(
        title="Lane-count distributions by dataset",
        ylabel="Lanes",
        xticks=[],
    )
    ax.yaxis.set_major_formatter(LANE_AXIS_FORMATTER)


def _add_figure_annotations(figure, datasets: Sequence[Dataset]) -> None:
    """Add the overall title, subtitle, and shared figure legend."""
    factors = ", ".join(
        f"{dataset.name}: {average_collapse_factor(dataset):.2f}x"
        for dataset in datasets
    )
    figure.suptitle("BioFabric Lane Collapse Statistics", fontsize=13, y=0.995)
    figure.text(
        0.5,
        0.96,
        f"Average collapse factor: {factors}",
        ha="center",
        va="center",
        fontsize=9.5,
    )

    dataset_handles = [
        Patch(facecolor=COLORS[index % len(COLORS)], label=dataset.name)
        for index, dataset in enumerate(datasets)
    ]
    style_handle = Line2D(
        [],
        [],
        linestyle="none",
        marker=None,
        label="○ uncollapsed    ◒ partially collapsed",
    )
    figure.legend(
        handles=[*dataset_handles, style_handle],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.925),
        ncol=min(4, len(dataset_handles) + 1),
        frameon=False,
    )


def create_collapse_figure(
    datasets: Sequence[Dataset],
    *,
    figsize: tuple[float, float] = (13, 9),
    scale: Literal["linear", "log"] = "linear",
):
    """Create degree and lane-distribution views of lane collapse.

    The returned Matplotlib figure is not shown or saved, allowing callers to
    choose a notebook, interactive window, or file output.
    """
    figure = plt.figure(figsize=figsize)
    top_row_plots = len(datasets) * 2
    grid = figure.add_gridspec(2, top_row_plots, height_ratios=(0.5, 1))
    degree_axes = [figure.add_subplot(grid[0, index]) for index in range(top_row_plots)]
    curve_ax = figure.add_subplot(grid[1, : top_row_plots // 2])
    distribution_ax = figure.add_subplot(grid[1, top_row_plots // 2 :])
    figure.subplots_adjust(top=0.85, bottom=0.12, hspace=0.3, wspace=0.5)

    degree_plots = [
        (dataset, field, label)
        for dataset in datasets
        for field, label in (
            ("average_degree", "Avg Degree"),
            ("maximum_degree", "Max Degree"),
        )
    ]
    for index, ax in enumerate(degree_axes[: len(degree_plots)]):
        dataset, field, label = degree_plots[index]
        _plot_degree_distribution(
            ax,
            dataset,
            COLORS[index // 2 % len(COLORS)],
            field,
            f"{label}",
            "degree",
        )
    for ax in degree_axes[len(degree_plots) :]:
        ax.set_visible(False)

    _plot_lane_curves(curve_ax, datasets, scale=scale)
    _plot_lane_distributions(distribution_ax, datasets)
    _add_figure_annotations(figure, datasets)
    return figure


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "data_dirs",
        nargs="*",
        type=Path,
        default=[
            Path("rome/data"),
            Path("randDAG/data"),
            Path("north/data"),
        ],
        help="directories containing node-link JSON files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("collapse_visualizations.png"),
        help="output image path (PNG, SVG, or any Matplotlib-supported format)",
    )
    args = parser.parse_args()

    datasets = load_datasets(args.data_dirs)
    figure = create_collapse_figure(datasets)
    figure.savefig(args.output, dpi=220, bbox_inches="tight")
    print(f"Saved {args.output}")
