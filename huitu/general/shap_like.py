"""SHAP-style explainability plots without the ``shap`` dependency.

Accepts pre-computed SHAP values (any Python array backend) and renders bar,
beeswarm, or dependence summaries matching the aesthetic of
``shap.summary_plot`` but using huitu's house style.

Example
-------
>>> import numpy as np
>>> from huitu import plot_shap
>>> rng = np.random.default_rng(0)
>>> sv = rng.normal(0, 1, (200, 6))
>>> fv = rng.normal(0, 1, (200, 6))
>>> names = [f"feat{i}" for i in range(6)]
>>> fig, ax = plot_shap(sv, names, feature_values=fv, kind="beeswarm")
"""

from __future__ import annotations

import numpy as np

from huitu._common import finalize, prepare_axes
from huitu.style import PALETTES, _GRADIENT_PALETTES, get_cmap


def _resolve_cmap(cmap):
    if isinstance(cmap, str):
        key = cmap.lower()
        if key in PALETTES and key in _GRADIENT_PALETTES:
            return get_cmap(key)
        if key in PALETTES:
            from matplotlib.colors import LinearSegmentedColormap

            return LinearSegmentedColormap.from_list(f"huitu-{key}", PALETTES[key])
    return cmap


def _feature_index(name_or_idx, feature_names):
    if isinstance(name_or_idx, (int, np.integer)):
        return int(name_or_idx)
    if name_or_idx in feature_names:
        return feature_names.index(name_or_idx)
    raise ValueError(f"feature '{name_or_idx}' not in feature_names")


def plot_shap(
    shap_values,
    feature_names,
    feature_values=None,
    ax=None,
    journal: str = "default",
    save=None,
    kind: str = "beeswarm",
    max_features: int = 10,
    dependence_feature=None,
    dependence_interaction=None,
    cmap="crameri-roma",
    **kwargs,
):
    """SHAP-style explainability plot (bar / beeswarm / dependence).

    Does **not** import the ``shap`` package — supply pre-computed values.

    Parameters
    ----------
    shap_values
        ``(n_samples, n_features)`` ndarray of SHAP contributions.
    feature_names
        Length-``n_features`` list of feature labels.
    feature_values
        ``(n_samples, n_features)`` ndarray of the actual feature values
        (required for ``beeswarm`` color coding and ``dependence``).
    kind
        ``"bar"`` (mean |SHAP|), ``"beeswarm"`` (per-sample scatter with
        vertical jitter), or ``"dependence"`` (single-feature scatter colored
        by an interaction feature).
    max_features
        Number of top features by mean |SHAP| to show (bar / beeswarm).
    dependence_feature, dependence_interaction
        Feature index or name. ``dependence_feature`` is required for
        ``kind="dependence"``; ``dependence_interaction`` is optional and
        drives the color.
    cmap
        Diverging colormap for beeswarm / dependence colors.

    Returns
    -------
    (fig, ax)
    """
    sv = np.asarray(shap_values, dtype=float)
    if sv.ndim != 2:
        raise ValueError("shap_values must be 2-D (n_samples, n_features)")
    n_samples, n_features = sv.shape
    feature_names = list(feature_names)
    if len(feature_names) != n_features:
        raise ValueError("feature_names length must match shap_values.shape[1]")

    fv = None
    if feature_values is not None:
        fv = np.asarray(feature_values, dtype=float)
        if fv.shape != sv.shape:
            raise ValueError("feature_values must have same shape as shap_values")

    cmap_obj = _resolve_cmap(cmap)
    fig, ax = prepare_axes(ax, journal)

    if kind == "bar":
        importance = np.abs(sv).mean(axis=0)
        order = np.argsort(importance)[::-1][:max_features]
        # Reverse so highest-importance ends up at the top of the horizontal bar.
        order = order[::-1]
        labels = [feature_names[i] for i in order]
        values = importance[order]
        bar_color = PALETTES["nature-cat"][0]
        ax.barh(np.arange(len(order)), values, color=bar_color,
                edgecolor="black", linewidth=0.4)
        ax.set_yticks(np.arange(len(order)))
        ax.set_yticklabels(labels)
        ax.set_xlabel("mean(|SHAP value|)")
        ax.xaxis.grid(True, linestyle="-", linewidth=0.3, alpha=0.35, color="#CCCCCC")
        ax.set_axisbelow(True)
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.tick_params(top=False, right=False, which="both")

    elif kind == "beeswarm":
        importance = np.abs(sv).mean(axis=0)
        order = np.argsort(importance)[::-1][:max_features]
        order = order[::-1]  # top of plot = most important
        rng = np.random.default_rng(0)
        for row_idx, feat_idx in enumerate(order):
            xs = sv[:, feat_idx]
            jitter = rng.uniform(-0.32, 0.32, size=xs.size)
            ys = np.full_like(xs, row_idx, dtype=float) + jitter
            if fv is not None:
                raw = fv[:, feat_idx]
                # z-score normalize per row so the diverging cmap reads as
                # "low feature value <-> high feature value".
                mu = float(np.nanmean(raw))
                sd = float(np.nanstd(raw))
                if sd > 0:
                    c = (raw - mu) / sd
                else:
                    c = np.zeros_like(raw)
                c = np.clip(c, -2.5, 2.5)
                ax.scatter(
                    xs, ys, c=c, cmap=cmap_obj, s=10, alpha=0.8,
                    linewidths=0, vmin=-2.5, vmax=2.5,
                )
            else:
                ax.scatter(xs, ys, color=PALETTES["nature-cat"][0],
                           s=10, alpha=0.6, linewidths=0)
        ax.axvline(0, color="#888888", linewidth=0.6, zorder=0)
        ax.set_yticks(np.arange(len(order)))
        ax.set_yticklabels([feature_names[i] for i in order])
        ax.set_xlabel("SHAP value")
        ax.xaxis.grid(True, linestyle="-", linewidth=0.3, alpha=0.35, color="#CCCCCC")
        ax.set_axisbelow(True)
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.tick_params(top=False, right=False, which="both")
        if fv is not None:
            import matplotlib as mpl

            sm = mpl.cm.ScalarMappable(
                cmap=cmap_obj, norm=mpl.colors.Normalize(vmin=-2.5, vmax=2.5)
            )
            sm.set_array([])
            import matplotlib as _mpl_mod
            _lbl_sz = _mpl_mod.rcParams.get("axes.labelsize", 8)
            cbar = fig.colorbar(sm, ax=ax, pad=0.02, shrink=0.85, aspect=25)
            cbar.set_label("feature value (z-score)", fontsize=_lbl_sz)
            cbar.outline.set_linewidth(0.5)
            cbar.ax.tick_params(width=0.5, length=2, labelsize=max(_lbl_sz - 1, 6))

    elif kind == "dependence":
        if dependence_feature is None:
            raise ValueError("dependence_feature is required for kind='dependence'")
        if fv is None:
            raise ValueError("feature_values is required for kind='dependence'")
        dep = _feature_index(dependence_feature, feature_names)
        inter = (
            _feature_index(dependence_interaction, feature_names)
            if dependence_interaction is not None
            else None
        )
        xs = fv[:, dep]
        ys = sv[:, dep]
        if inter is not None:
            c = fv[:, inter]
            sc = ax.scatter(
                xs, ys, c=c, cmap=cmap_obj, s=14, alpha=0.85, linewidths=0,
            )
            import matplotlib as _mpl_mod
            _lbl_sz = _mpl_mod.rcParams.get("axes.labelsize", 8)
            cbar = fig.colorbar(sc, ax=ax, pad=0.02, shrink=0.85, aspect=25)
            _inter_name = feature_names[inter]
            _cbar_lbl = (
                _inter_name if "(" in _inter_name else f"{_inter_name} (value)"
            )
            cbar.set_label(_cbar_lbl, fontsize=_lbl_sz)
            cbar.outline.set_linewidth(0.5)
            cbar.ax.tick_params(width=0.5, length=2, labelsize=max(_lbl_sz - 1, 6))
        else:
            ax.scatter(xs, ys, color=PALETTES["nature-cat"][0], s=14, alpha=0.7)
        # Degree-2 polynomial trend, if enough samples.
        if xs.size >= 5:
            try:
                coef = np.polyfit(xs, ys, 2)
                xt = np.linspace(np.min(xs), np.max(xs), 100)
                ax.plot(xt, np.polyval(coef, xt),
                        color="#3F3F3F", linewidth=0.9, linestyle="--")
            except Exception:
                pass
        ax.axhline(0, color="#888888", linewidth=0.6, zorder=0)
        ax.set_xlabel(feature_names[dep])
        ax.set_ylabel(f"SHAP value ({feature_names[dep]})")
        ax.yaxis.grid(True, linestyle="-", linewidth=0.3, alpha=0.35, color="#CCCCCC")
        ax.set_axisbelow(True)
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.tick_params(top=False, right=False, which="both")

    else:
        raise ValueError("kind must be 'bar', 'beeswarm', or 'dependence'")

    finalize(fig, save)
    return fig, ax
