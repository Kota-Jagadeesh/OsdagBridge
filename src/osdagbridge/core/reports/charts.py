"""Dynamic report charts. Uses only computed design/quantity values."""
import math
import re
from pathlib import Path
from matplotlib.figure import Figure
from osdagbridge.core.reports.styles import UR_PASS_COLOR, UR_FAIL_COLOR, CHART_BAR_COLOR


def _numeric(value):
    """Parse a displayed number, refusing missing or nonnumeric fields."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        result = float(value)
    else:
        raw = str(value).strip()
        color_match = re.fullmatch(r"\\textcolor\{[^{}]+\}\{([^{}]+)\}", raw)
        if color_match:
            raw = color_match.group(1)
        match = re.match(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))(?=\s|$)", raw)
        if not match:
            return None
        result = float(match.group(1))
    return result if math.isfinite(result) else None


def _save_bar(title, labels, values, path, ylabel, threshold=False):
    if not labels:
        return False
    fig = Figure(figsize=(max(7.6, 1.2 * len(labels) + 2), 4.8), dpi=145)
    ax = fig.subplots()
    indexes = list(range(len(labels)))
    colors = [(UR_FAIL_COLOR if v > 1.0 else UR_PASS_COLOR) if threshold else CHART_BAR_COLOR
              for v in values]
    ax.bar(indexes, values, color=colors, width=.65)
    ax.set_xticks(indexes, labels, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis="y", alpha=.22)
    ax.set_axisbelow(True)
    if threshold:
        ax.axhline(1.0, color="red", ls="--", lw=1.5, label="UR = 1.0 limit")
        ax.legend(loc="upper right", fontsize=8)
    for i, v in enumerate(values):
        ax.text(i, v + max([*values, 1]) * .012, f"{v:.2f}", ha="center", fontsize=8)
    ax.set_ylim(0, max(max(values) * 1.18, 1.1 if threshold else .1))
    fig.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=145)
    return True


def figure_latex(path, caption, width="0.90"):
    path = str(Path(path).resolve()).replace("\\", "/")
    return ("\\begin{figure}[H]\n\\centering\n"
            + "\\includegraphics[width=" + width + "\\textwidth]{\\detokenize{" + path + "}}\n"
            + "\\caption{" + caption + "}\n\\end{figure}\n")


def utilization_figures(rows, image_dir):
    """rows: (label, UR); values come from the same summary as Table 5.29."""
    sections = {"Steel Plate Girders": [], "Concrete Deck Slab": [],
                "Cross Bracing": [], "End Diaphragms": []}
    for label, ur in rows:
        value = _numeric(ur)
        if value is None or value < 0:
            continue
        if label.startswith("Girder"):
            group = "Steel Plate Girders"
        elif label.startswith("Deck") or "slab" in label.lower():
            group = "Concrete Deck Slab"
        elif label.startswith("Cross Bracing"):
            group = "Cross Bracing"
        elif label.startswith("End Diaphragm"):
            group = "End Diaphragms"
        else:
            continue
        sections[group].append((label, value))
    tex = "\n\\subsection*{Utilization Ratio Visual Summary}\n"
    any_fig = False
    for index, (group, entries) in enumerate(sections.items(), 1):
        if not entries:
            continue
        path = Path(image_dir) / f"ur_component_{index}.png"
        labels, values = zip(*entries)
        if _save_bar(group, labels, values, path, "Utilization Ratio (Demand / Capacity)", True):
            tex += figure_latex(path, group + " --- Demand/Capacity Checks")
            any_fig = True
    return tex if any_fig else ""


def quantity_figures(values, image_dir):
    """Report quantity plots, keeping incompatible units on separate axes."""
    steel = [("Girders", _numeric(values.get("steel_girders_wt_total"))),
             ("Cross Bracing (top)", _numeric(values.get("bracing_top_wt_total"))),
             ("Cross Bracing (bottom)", _numeric(values.get("bracing_bot_wt_total"))),
             ("Cross Bracing (diagonal)", _numeric(values.get("bracing_diag_wt_total"))),
             ("End Diaphragms", _numeric(values.get("end_diaphragm_wt_total")))]
    # Optional end-diaphragm weight is included only when supplied by the backend.
    tex = "\n\\section*{Material Quantity Visual Summary}\n"
    steel = [(n, v) for n, v in steel if v is not None and v >= 0]
    if steel:
        path = Path(image_dir) / "material_structural_steel.png"
        _save_bar("Structural Steel", [x[0] for x in steel], [x[1] for x in steel], path, "Mass (MT)")
        tex += figure_latex(path, "Structural Steel Quantity by Component")
    if _numeric(values.get("end_diaphragm_wt_total")) is None:
        tex += (r"\noindent{\small\itshape End-diaphragm tonnage is not shown "
                "because no verified material quantity was supplied by the report data.}"
                r"\par" + "\n")
    concrete = _numeric(values.get("concrete_deck_vol_total"))
    rebar = _numeric(values.get("rebar_deck_wt_total"))
    if concrete is not None and concrete >= 0:
        path = Path(image_dir) / "material_concrete.png"
        _save_bar("Concrete", ["Deck Slab"], [concrete], path, "Volume (m\u00b3)")
        tex += figure_latex(path, "Concrete Volume")
    if rebar is not None and rebar >= 0:
        path = Path(image_dir) / "material_rebar.png"
        _save_bar("Reinforcement Steel", ["Deck Reinforcement"], [rebar], path, "Mass (MT)")
        tex += figure_latex(path, "Reinforcement Steel Quantity")
    return tex
