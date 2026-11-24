"""Preprocessing + hypothesis tests for the BioFab user study.

Scoring follows the pilot notebook (notebook.ipynb); exclusion rules were added for the study.

    H1  Folding preserves task accuracy
        -> TOST (Welch) on overall accuracy, margin in percentage points (primary);
           per-task TOSTs are exploratory
    H2  Folding does not meaningfully affect perceived workload
        -> TOST (Welch) on overall RTLX, margin in RTLX points (primary);
           per-task TOSTs are exploratory
    H3  Folding shortens response times on the common-neighbors task (task 2)
        -> one-sided Mann-Whitney U on task 2 (primary);
           task 1, task 3 and overall are exploratory (two-sided)

Only the primary test decides a hypothesis. All other tests are exploratory and Holm-corrected
within each hypothesis.
Everything is aggregated to ONE value per participant (per task, and pooled
"overall" = mean of that participant's per-task values) before testing, so the
3 trials per task never count as independent samples. Differences are folded - unfolded.
"""
import json

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.weightstats import ttost_ind

NASA_SUBSCALES = ["mental-demand", "physical-demand", "temporal-demand",
                  "performance", "effort", "frustration"]
TLX_TRIAL = "$nasa-tlx.components.nasa-tlx"
TASKS = ["task1", "task2", "task3"]
TASK_ORDER = TASKS + ["overall"]
# reVISit records the conditions as "collapsed" and "normal"; the analysis uses the Origraphi names
CONDITION_LABELS = {"collapsed": "folded", "normal": "unfolded"}
CONDITIONS = ("folded", "unfolded")  # differences are always folded - unfolded


# --------------------------------------------------------------------------- #
# Preprocessing (same scoring as the pilot)
# --------------------------------------------------------------------------- #
def _as_set(value):
    if value == "":
        return None
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        parsed = value
    return set(parsed) if isinstance(parsed, list) else {parsed}


def _extract(frame, trial_regex, response_id):
    mask = (frame["trialId"].str.match(trial_regex)
            & (frame["status"] == "completed")
            & (frame["responseId"] == response_id))
    return frame.loc[mask].copy()


def load_trials(data_path, edge_truth_path, rt_col="cleanedDuration"):
    """Return (df, trials, tlx) for ALL participants (exclusions are applied separately).

    trials: one row per task trial with columns
            participantId, condition, task, trialId, rt, accuracy (0-100)
    tlx:    one row per participant x task x subscale with `score`

    rt_col: reVISit's `cleanedDuration` subtracts time the tab was hidden; `duration` is raw wall time.
    """
    df = pd.read_csv(data_path, dtype=str, keep_default_na=False)
    df["condition"] = df["condition"].replace(CONDITION_LABELS)
    df["trialOrder"] = pd.to_numeric(df["trialOrder"], errors="coerce")
    completed = df[df["status"] == "completed"]

    edge_truth = pd.read_csv(edge_truth_path)[["graph_file", "n_edges"]]

    t1 = _extract(completed, r"^task1_component_", "graphVis").assign(task="task1")
    t2 = _extract(completed, r"^task2_component_", "graphVis").assign(task="task2")
    for t in (t1, t2):
        t["accuracy"] = 100.0 * t.apply(lambda r: _as_set(r["answer"]) == _as_set(r["correctAnswer"]), axis=1)

    t3 = _extract(completed, r"^task3_component_", "task3-numerical").assign(task="task3")
    t3["graph_file"] = t3["parameters_graphDataPath"].str.extract(r"([^/]+\.json)$")[0]
    t3 = t3.merge(edge_truth, on="graph_file", how="left")
    if t3["n_edges"].isna().any():
        missing = sorted(t3.loc[t3["n_edges"].isna(), "graph_file"].unique())
        raise ValueError(f"No ground truth in {edge_truth_path} for: {missing}")
    estimate = pd.to_numeric(t3["answer"], errors="coerce")
    t3["accuracy"] = (100 - (estimate - t3["n_edges"]).abs() / t3["n_edges"] * 100).clip(lower=0)

    trials = pd.concat([t1, t2, t3], ignore_index=True)
    trials["rt"] = pd.to_numeric(trials[rt_col], errors="coerce")
    trials = trials[["participantId", "condition", "task", "trialId", "rt", "accuracy"]]

    tlx = _tlx_per_task(df, completed)
    return df, trials, tlx


def _tlx_per_task(df, completed):
    """TLX is filled in once per task block; recover which task each block followed."""
    order = df.loc[df["trialOrder"].notna(), ["participantId", "trialOrder", "trialId"]].drop_duplicates()
    order["task_num"] = order["trialId"].str.extract(r"^task([123])_component_")[0]
    order = order.sort_values(["participantId", "trialOrder"])
    # forward-fill the most recent task number onto each TLX row
    order["block_task"] = order.groupby("participantId")["task_num"].ffill()
    labels = order.loc[order["trialId"] == TLX_TRIAL, ["participantId", "trialOrder", "block_task"]]

    tlx = completed[(completed["trialId"] == TLX_TRIAL) & completed["responseId"].isin(NASA_SUBSCALES)].copy()
    tlx["score"] = pd.to_numeric(tlx["answer"], errors="coerce")
    tlx = tlx.merge(labels, on=["participantId", "trialOrder"], how="left")
    tlx["task"] = "task" + tlx["block_task"]
    return tlx[["participantId", "condition", "task", "responseId", "score"]]


# --------------------------------------------------------------------------- #
# Exclusions
# --------------------------------------------------------------------------- #
def attention_check_results(df):
    """One row per participant: number of attention checks seen / failed (exact set match)."""
    att = df[df["trialId"].str.startswith("attention_check") & (df["status"] == "completed")
             & (df["responseId"] == "graphVis")].copy()
    att["failed"] = att.apply(lambda r: _as_set(r["answer"]) != _as_set(r["correctAnswer"]), axis=1)
    return att.groupby("participantId").agg(attn_seen=("failed", "size"), attn_failed=("failed", "sum"))


def _stage(trial_id):
    if trial_id.startswith(("consent", "intro_")):
        return "intro"
    if trial_id.startswith("practice_"):
        return "training"
    if trial_id == "experiment_start":
        return "experiment start"
    return "main tasks"


def session_progress(df):
    """One row per participant: session status and how far they got.

    reVISit writes a row for every PLANNED trial, and `status` / `percentComplete` are
    participant-level values repeated on each row. A trial counts as reached only if it has
    a recorded `duration`. (The shipped results/study_session_progress.csv also has a
    `test_session` column, derived from the original IDs before they were pseudonymised.)
    """
    rows = []
    reached_all = df[(df["duration"] != "") & (df["responseId"] != "windowEvents")]
    for pid, g in df.groupby("participantId"):
        status = next((s for s in g["status"] if s), "never started")
        reached = reached_all[reached_all["participantId"] == pid].drop_duplicates(["trialId", "trialOrder"])
        reached = reached.assign(order=pd.to_numeric(reached["trialOrder"])).sort_values("order")
        tasks = reached["trialId"].str.extract(r"^(task[123])_component_")[0].value_counts()
        last = reached["trialId"].iloc[-1] if len(reached) else ""
        rows.append({
            "participantId": pid,
            "condition": g["condition"].iloc[0],
            "status": status,
            "reject_reason": next((r for r in g["rejectReason"] if r), ""),
            "percent_complete": max((float(p) for p in g["percentComplete"] if p), default=0.0),
            "last_trial": last,
            "stopped_in": _stage(last) if last else "",
            **{f"{t}_trials": int(tasks.get(t, 0)) for t in TASKS},
            "tlx_blocks": int((reached["trialId"] == TLX_TRIAL).sum()),
            "attn_checks": int(reached["trialId"].str.startswith("attention_check").sum()),
        })
    return pd.DataFrame(rows)


def exclude_participants(df, trials, manual=None, min_completed=27, attn_max_fails=0,
                         clickthrough_median_ms=8000):
    """Participant-level exclusions. Returns a table with one row per participant and an
    `exclusion` column ("" = kept; several reasons are joined with "; ").

    Rules (applied in this order, all reasons are recorded):
      1. incomplete session   fewer than `min_completed` completed rows
      2. attention checks     more than `attn_max_fails` failed checks (a missing check counts as failed)
      3. click-through        median task-trial time below `clickthrough_median_ms`
      4. manual               ids in `manual` (dict id -> reason), e.g. technical problems
    Rule 3 deliberately uses speed only, never accuracy: excluding on accuracy would bias H1.
    """
    manual = manual or {}
    p = df.groupby("participantId").agg(
        condition=("condition", "first"),
        n_completed=("status", lambda s: (s == "completed").sum()))
    p = p.join(attention_check_results(df), how="left").fillna({"attn_seen": 0, "attn_failed": 0})
    p = p.join(trials.groupby("participantId")["rt"].median().rename("median_task_rt"), how="left")

    n_checks = int(p["attn_seen"].max()) if len(p) else 0
    reasons = pd.DataFrame(index=p.index)
    reasons["incomplete"] = np.where(p["n_completed"] < min_completed, "incomplete session", "")
    attn_bad = (p["attn_failed"] + (n_checks - p["attn_seen"])) > attn_max_fails
    reasons["attention"] = np.where(attn_bad & (reasons["incomplete"] == ""),
                                    "failed attention check(s)", "")
    reasons["clickthrough"] = np.where(p["median_task_rt"] < clickthrough_median_ms,
                                       "click-through (median trial time too short)", "")
    reasons["manual"] = [f"manual: {manual[i]}" if i in manual else "" for i in p.index]
    p["exclusion"] = reasons.apply(lambda r: "; ".join(x for x in r if x), axis=1)
    return p.reset_index()


def rt_upper_bounds(trials, mad_k=3.0):
    """Per-task 'too slow' bound in ms: exp(median + k * scaled MAD) of log RT."""
    log_rt = np.log(trials["rt"])
    med = log_rt.groupby(trials["task"]).median()
    mad = (log_rt - trials["task"].map(med)).abs().groupby(trials["task"]).median() * 1.4826
    return np.exp(med + mad_k * mad).rename("rt_upper_ms")


def flag_trials(trials, min_rt_ms=3000, mad_k=3.0):
    """Trial-level response-time outliers among the KEPT participants.

    too_fast: rt < min_rt_ms (an "instant" answer; the task was not done) -> whole trial dropped
    too_slow: log(rt) > median + mad_k * MAD of log(rt) for that task, pooled over both
              conditions (idle / distracted with the tab open)        -> rt dropped, accuracy kept
    MAD is scaled (x1.4826) to be SD-consistent; k=3 is the conservative choice
    (Leys et al., 2013). Bounds are computed on the log scale because RTs are right-skewed.
    """
    t = trials.copy()
    t["rt_upper_ms"] = t["task"].map(rt_upper_bounds(t, mad_k))
    t["too_fast"] = t["rt"] < min_rt_ms
    t["too_slow"] = t["rt"] > t["rt_upper_ms"]

    clean = t.copy()
    clean.loc[clean["too_fast"], ["rt", "accuracy"]] = np.nan
    clean.loc[clean["too_slow"], "rt"] = np.nan
    return clean, t[t["too_fast"] | t["too_slow"]]


def apply_exclusions(df, trials, tlx, manual=None, min_completed=27, attn_max_fails=0,
                     clickthrough_median_ms=8000, min_rt_ms=3000, mad_k=3.0):
    """Run all exclusions. Returns (trials_clean, tlx_clean, participants, flagged_trials)."""
    participants = exclude_participants(df, trials, manual, min_completed, attn_max_fails,
                                        clickthrough_median_ms)
    kept = set(participants.loc[participants["exclusion"] == "", "participantId"])
    trials = trials[trials["participantId"].isin(kept)]
    tlx = tlx[tlx["participantId"].isin(kept)]
    trials_clean, flagged = flag_trials(trials, min_rt_ms, mad_k)
    return trials_clean, tlx, participants, flagged


# --------------------------------------------------------------------------- #
# One value per participant
# --------------------------------------------------------------------------- #
def per_participant(frame, value_col, agg="mean"):
    """Participant x task values plus a pooled 'overall' row (mean of the per-task values).

    NaN trials (removed outliers) are skipped. 'overall' is only defined when the participant
    has a value for all three tasks, otherwise tasks with different scales would be mixed unevenly.
    """
    per_task = (frame.groupby(["participantId", "condition", "task"])[value_col]
                .agg(agg).rename("value").reset_index())
    overall = (per_task.groupby(["participantId", "condition"])["value"]
               .agg(lambda s: s.mean() if s.notna().sum() == len(TASKS) else np.nan)
               .reset_index().assign(task="overall"))
    return pd.concat([per_task, overall], ignore_index=True)


def build_dvs(trials, tlx, rt_agg="median"):
    """Long table: participantId, condition, task, dv, value."""
    rtlx = tlx.groupby(["participantId", "condition", "task"])["score"].mean().rename("rtlx").reset_index()
    return pd.concat([
        per_participant(trials, "accuracy").assign(dv="accuracy"),
        per_participant(rtlx, "rtlx").assign(dv="rtlx"),
        per_participant(trials, "rt", agg=rt_agg).assign(dv="rt"),
    ], ignore_index=True)


def split(dvs, dv, task):
    g = dvs[(dvs["dv"] == dv) & (dvs["task"] == task)]
    a = g.loc[g["condition"] == CONDITIONS[0], "value"].dropna().to_numpy(float)
    b = g.loc[g["condition"] == CONDITIONS[1], "value"].dropna().to_numpy(float)
    return a, b


# --------------------------------------------------------------------------- #
# Effect sizes / helpers
# --------------------------------------------------------------------------- #
def hedges_g(a, b):
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    if sp == 0:
        return np.nan
    j = 1 - 3 / (4 * (na + nb) - 9)  # small-sample correction
    return j * (a.mean() - b.mean()) / sp


def welch_ci(a, b, conf):
    """CI of mean(a) - mean(b) with Welch-Satterthwaite df."""
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = np.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    t = stats.t.ppf(0.5 + conf / 2, df)
    d = a.mean() - b.mean()
    return d - t * se, d + t * se


def bootstrap_ci(a, b, stat, conf, n_boot=5000, rng=None):
    rng = rng if rng is not None else np.random.default_rng(42)
    draws = np.array([stat(rng.choice(a, len(a)), rng.choice(b, len(b))) for _ in range(n_boot)])
    half = (1 - conf) / 2 * 100
    return tuple(np.nanpercentile(draws, [half, 100 - half]))


def hodges_lehmann(a, b):
    """Median of all pairwise differences a_i - b_j (the shift estimate matching Mann-Whitney)."""
    return float(np.median(np.subtract.outer(a, b)))


def assumption_checks(a, b):
    sw_a = stats.shapiro(a).pvalue if len(a) >= 3 else np.nan
    sw_b = stats.shapiro(b).pvalue if len(b) >= 3 else np.nan
    return {"shapiro_p_folded": sw_a, "shapiro_p_unfolded": sw_b,
            "levene_p": stats.levene(a, b, center="median").pvalue}


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def _tost_verdict(equivalent, different):
    return {(True, False): "equivalent", (False, True): "different (not equivalent)",
            (True, True): "equivalent but different (trivial difference)",
            (False, False): "inconclusive"}[(bool(equivalent), bool(different))]


def tost(a, b, margin, alpha=0.05, rng=None):
    """Welch TOST for equivalence of mean(a) - mean(b) within [-margin, +margin].

    Equivalence is declared when both one-sided tests reject at alpha, which is
    identical to the (1 - 2*alpha) CI lying inside the margin.
    Also reports the ordinary two-sided Welch t-test so the four Lakens outcomes
    (equivalent / different / both / inconclusive) can be read off.
    """
    p_tost, (t_lower, p_lower, df_tost), (t_upper, p_upper, _) = ttost_ind(a, b, -margin, margin, usevar="unequal")
    ci_lo, ci_hi = welch_ci(a, b, 1 - 2 * alpha)
    boot_lo, boot_hi = bootstrap_ci(a, b, lambda x, y: x.mean() - y.mean(), 1 - 2 * alpha, rng=rng)
    p_diff = stats.ttest_ind(a, b, equal_var=False).pvalue
    equivalent, different = p_tost < alpha, p_diff < alpha
    verdict = _tost_verdict(equivalent, different)
    return {
        "n_folded": len(a), "n_unfolded": len(b),
        "mean_folded": a.mean(), "mean_unfolded": b.mean(),
        "sd_folded": a.std(ddof=1), "sd_unfolded": b.std(ddof=1),
        "diff": a.mean() - b.mean(), "margin": margin,
        "ci90_lo": ci_lo, "ci90_hi": ci_hi,
        "boot_ci90_lo": boot_lo, "boot_ci90_hi": boot_hi,
        "boot_equivalent": (-margin < boot_lo) and (boot_hi < margin),
        "t_lower": t_lower, "t_upper": t_upper, "df_tost": df_tost,
        "p_lower": p_lower, "p_upper": p_upper, "p_tost": p_tost,
        "p_welch": p_diff, "hedges_g": hedges_g(a, b),
        # smallest symmetric margin that would have given equivalence (sensitivity, NOT for choosing the margin)
        "min_equiv_margin": max(abs(ci_lo), abs(ci_hi)),
        "equivalent": equivalent, "verdict": verdict,
        **assumption_checks(a, b),
    }


def mann_whitney(a, b, alpha=0.05, rng=None, alternative="two-sided"):
    """Mann-Whitney U of folded (a) vs unfolded (b).

    alternative="two-sided": any difference; "less": folded tends to have SMALLER values (faster).
    The Hodges-Lehmann shift CI is always a two-sided 95% bootstrap CI (conservative for a
    one-sided test). The log-RT Welch t-test uses the same alternative as a sensitivity check.
    """
    res = stats.mannwhitneyu(a, b, alternative=alternative, method="auto")
    r_rb = 2 * res.statistic / (len(a) * len(b)) - 1  # rank-biserial: <0 means folded tends to be faster
    hl = hodges_lehmann(a, b)
    hl_lo, hl_hi = bootstrap_ci(a, b, hodges_lehmann, 1 - alpha, rng=rng)
    return {
        "n_folded": len(a), "n_unfolded": len(b),
        "median_folded": np.median(a), "median_unfolded": np.median(b),
        "U": res.statistic, "p_mwu": res.pvalue, "alternative": alternative,
        "rank_biserial": r_rb, "hl_shift": hl, "hl_ci95_lo": hl_lo, "hl_ci95_hi": hl_hi,
        # sensitivity: parametric test on log-RT
        "p_welch_log": stats.ttest_ind(np.log(a), np.log(b), equal_var=False, alternative=alternative).pvalue,
        **assumption_checks(a, b),
    }


def run_hypotheses(dvs, margins, alpha=0.05, seed=42, h3_task="task2", h3_alternative="less"):
    """Run H1-H3 for every task + overall.

    H1, H2: `overall` is the primary test; the three per-task tests are exploratory.
    H3 ("folded is faster on the common-neighbors task"): the primary test is a one-sided
        Mann-Whitney U on `h3_task`; the other tasks and `overall` are exploratory (two-sided).
    Non-primary tests are Holm-corrected within each hypothesis.
    """
    rng = np.random.default_rng(seed)
    spec = [("H1", "accuracy", "TOST", "overall"), ("H2", "rtlx", "TOST", "overall"),
            ("H3", "rt", "Mann-Whitney U", h3_task)]
    rows = []
    for hyp, dv, test, primary_task in spec:
        for task in TASK_ORDER:
            a, b = split(dvs, dv, task)
            if len(a) < 2 or len(b) < 2:
                continue
            primary = task == primary_task
            if test == "TOST":
                res = tost(a, b, margins[dv], alpha, rng)
                role = "primary" if primary else "exploratory"
            else:
                res = mann_whitney(a, b, alpha, rng, alternative=h3_alternative if primary else "two-sided")
                role = "primary" if primary else "exploratory"
            rows.append({"hypothesis": hyp, "dv": dv, "task": task, "test": test, "role": role, **res})
    out = pd.DataFrame(rows)

    out["p"] = out["p_tost"].fillna(out["p_mwu"])
    out["p_holm"] = np.nan
    for hyp, idx in out[out["role"] != "primary"].groupby("hypothesis").groups.items():
        out.loc[idx, "p_holm"] = multipletests(out.loc[idx, "p"], alpha=alpha, method="holm")[1]
    out.loc[out["role"] == "primary", "p_holm"] = out.loc[out["role"] == "primary", "p"]
    out["significant"] = out["p_holm"] < alpha

    # TOST verdicts must use the Holm-corrected p (per-task tests); the primary test is unchanged
    is_tost = out["test"] == "TOST"
    out.loc[is_tost, "equivalent"] = out.loc[is_tost, "significant"]
    out.loc[is_tost, "verdict"] = [
        _tost_verdict(eq, pw < alpha)
        for eq, pw in zip(out.loc[is_tost, "equivalent"], out.loc[is_tost, "p_welch"])]
    return out


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def _fmt_p(p):
    return "$<$.001" if p < .001 else f"{p:.3f}".lstrip("0")


def latex_table(results):
    r"""LaTeX table of the three primary tests, as used in the paper (needs booktabs and the paper's
    \hyp and \task macros).

    TOST rows: mean difference with 90% CI and the margin. Mann-Whitney row: Hodges-Lehmann shift in
    seconds with 95% CI. p is uncorrected (one planned test each). The last column states whether the
    null hypothesis H_{0,i} was rejected.
    """
    def num(x):
        return f"${x:.1f}$"

    measure = {"accuracy": "Accuracy", "rtlx": "RTLX"}
    rows = []
    for _, r in results[results["role"] == "primary"].iterrows():
        if r["test"] == "TOST":
            est = (f"{num(r['diff'])} [{num(r['ci90_lo'])}, {num(r['ci90_hi'])}] pts, "
                   f"$\\pm{r['margin']:g}$")
            name = measure[r["dv"]]
        else:
            est = (f"{num(r['hl_shift'] / 1000)} [{num(r['hl_ci95_lo'] / 1000)}, "
                   f"{num(r['hl_ci95_hi'] / 1000)}]\\,s")
            name = f"RT, \\task{{T{r['task'][-1]}}}"
        outcome = "rejected" if r["significant"] else "not rejected"
        rows.append(f"        \\hyp{{{r['hypothesis']}}} & {name} & {est} & {_fmt_p(r['p'])} & {outcome} \\\\")
    return "\n".join([
        r"\begin{table}[t]",
        r"    \centering",
        r"    \caption{Primary test per hypothesis. TOST: mean difference with 90\% CI; equivalence is shown if",
        r"    the CI lies within the margin. Mann-Whitney $U$: Hodges-Lehmann estimate with 95\% CI.}",
        r"    \label{tab:results}",
        r"    \footnotesize",
        r"    \setlength{\tabcolsep}{4pt}",
        r"    \begin{tabular}{@{}lllll@{}}",
        r"        \toprule",
        r"             & Measure & Difference [CI] & $p$ & $H_{0,i}$ \\",
        r"        \midrule",
        *rows,
        r"        \bottomrule",
        r"    \end{tabular}",
        r"\end{table}",
    ])


def results_by_task(results, dvs):
    """One row per measure x task: per-condition summary, difference with CI, test statistic, p and outcome.

    Accuracy and RTLX: mean (SD) per condition; difference of means with 90% CI (TOST); test statistics
    t- and t+ of the two one-sided tests. Response time: median [25th, 75th percentile] per condition,
    in seconds; Hodges-Lehmann shift with 95% CI; Mann-Whitney U. p is uncorrected for the primary test
    of each hypothesis and Holm-corrected otherwise (for TOST: the larger one-sided p).
    """
    rows = []
    for dv in ("accuracy", "rtlx", "rt"):
        for task in TASK_ORDER:
            r = results[(results["dv"] == dv) & (results["task"] == task)].iloc[0]
            a, b = split(dvs, dv, task)
            primary = r["role"] == "primary"
            if dv == "rt":
                fmt = lambda v: (f"{np.median(v) / 1000:.1f} [{np.percentile(v, 25) / 1000:.1f}, "
                                 f"{np.percentile(v, 75) / 1000:.1f}]")
                diff, lo, hi = r["hl_shift"] / 1000, r["hl_ci95_lo"] / 1000, r["hl_ci95_hi"] / 1000
                stat = f"$U = {r['U']:g}$ ({_fmt_p(r['p_mwu'])})"
                if primary:
                    outcome = "folded faster" if r["significant"] else "not supported"
                else:
                    outcome = "different" if r["significant"] else "no difference"
            else:
                fmt = lambda v: f"{v.mean():.1f} ({v.std(ddof=1):.1f})"
                diff, lo, hi = r["diff"], r["ci90_lo"], r["ci90_hi"]
                stat = (f"$t^{{-}} = {r['t_lower']:.2f}$ ({_fmt_p(r['p_lower'])}), "
                        f"$t^{{+}} = {r['t_upper']:.2f}$ ({_fmt_p(r['p_upper'])})")
                outcome = r["verdict"]
            rows.append({"hypothesis": r["hypothesis"], "measure": dv, "task": task, "primary": primary,
                         "folded": fmt(a), "unfolded": fmt(b), "diff": diff, "ci_lo": lo, "ci_hi": hi,
                         "statistic": stat, "p": r["p_holm"], "h0_rejected": bool(r["significant"]),
                         "outcome": outcome})
    return pd.DataFrame(rows)


def latex_results_by_task(table):
    r"""Full-width LaTeX table of all results per measure and task (needs booktabs and the paper's
    \hyp, \task and \cond macros). Primary tests are marked with an asterisk; bold p = H0 rejected."""
    groups = {
        "accuracy": r"\textbf{Accuracy} (\%) \quad \hyp{$H_1$}, TOST~\cite{Lakens2018} $\pm5$",
        "rtlx": r"\textbf{Workload} (RTLX) \quad \hyp{$H_2$}, TOST~\cite{Lakens2018} $\pm10$",
        "rt": r"\textbf{Response time} (s) \quad \hyp{$H_3$}, MWU~\cite{mannwhitney1947}",
    }
    task_name = {"task1": r"\task{T1}", "task2": r"\task{T2}", "task3": r"\task{T3}", "overall": "Overall"}
    lines = [
        r"\begin{table*}[!ht]",
        r"    \centering",
        r"    \footnotesize",
        r"    \begin{tabular}{@{}lllllrl@{}}",
        r"        \toprule",
        r"        Task & \cond{C1} & \cond{C2} & Difference [CI] & Test statistic ($p$) & $p$ & Outcome \\",
    ]
    for dv in ("accuracy", "rtlx", "rt"):
        lines += [r"        \midrule", rf"        \multicolumn{{7}}{{@{{}}l}}{{{groups[dv]}}} \\", r"        \addlinespace[2pt]"]
        for _, r in table[table["measure"] == dv].iterrows():
            label = task_name[r["task"]] + (r"$^{\ast}$" if r["primary"] else "")
            p = _fmt_p(r["p"])
            p = rf"\textbf{{{p}}}" if r["h0_rejected"] else p
            diff = f"${r['diff']:+.1f}$ [${r['ci_lo']:.1f}$, ${r['ci_hi']:.1f}$]"
            lines.append(f"        \\quad {label} & {r['unfolded']} & {r['folded']} & {diff} & {r['statistic']} & {p} & {r['outcome']} \\\\")
    lines += [
        r"        \bottomrule",
        r"    \end{tabular}",
        r"    \caption{Results per measure and task. Accuracy and RTLX: mean ($\sigma$) per condition and difference",
        r"    of means [90\% CI]; response time: median [25th, 75th percentile] and Hodges-Lehmann",
        r"    difference~\cite{hodges1963} [95\% CI]. Differences are \cond{C2} $-$ \cond{C1}. TOST: two one-sided",
        r"    Welch $t$-tests~\cite{welch1947} with the given margin; $t^{-}$ and $t^{+}$ test \hyp{$H_{0,i}^{-}$} and",
        r"    \hyp{$H_{0,i}^{+}$} ($df$ 96--102). MWU: Mann-Whitney $U$. Test statistic ($p$): uncorrected $p$ of each",
        r"    individual test. $p$ column: $p$ of the hypothesis test (for TOST, the larger of the two one-sided $p$).",
        r"    $^{\ast}$Primary test (uncorrected $p$; one-sided for \hyp{$H_3$}); all other rows are exploratory",
        r"    (Holm-corrected~\cite{holm1979}). Bold: $p < .05$, i.e., \hyp{$H_0$} rejected.}",
        r"    \label{tab:results-detail}",
        r"\end{table*}",
    ]
    return "\n".join(lines)
