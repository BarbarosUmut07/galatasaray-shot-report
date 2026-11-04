"""
GALATASARAY 2-0 VfB STUTTGART  ·  UEFA Champions League, League Phase MD4
3 November 2026  ·  Post-match shot report (Galatasaray)

Sources
- ESPN shot map: xG, xGOT, shot distance (yards), goal-mouth zone
- Sky Sports live commentary (Opta): outcome + where each shot was taken from
  ("centre of the box", "right side of the box", "difficult angle on the left" ...)

Exact x/y coordinates were not available. Each shot is placed at its real
distance from goal, on the side of the pitch the commentary describes.
To use exact positions, edit the "side_m" values in SHOTS.

Usage:
    pip install -r requirements.txt
    python shot_report.py

Author: Barbaros Umut
"""

import math

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Arc, FancyBboxPatch, Rectangle

# =============================================================================
# 1. DATA
# =============================================================================
# side_m : metres from the centre of the goal, seen from the shooter
#          (negative = left, positive = right). Based on the commentary zone.
# end    : where the ball went (seen from the shooter). None = blocked.
SHOTS = [
    # min    sort  player      xG    xGOT  yd  body          outcome      side_m  end
    ("12'",   12, "Batrakov", 0.26, 0.57, 14, "Right foot", "Goal",        1,  "High Right"),
    ("15'",   15, "Batrakov", 0.14, 0.12, 16, "Right foot", "Goal",        9,  "Low Centre"),
    ("22'",   22, "Batrakov", 0.11, 0.05, 16, "Right foot", "Saved",      -9,  "Low Centre"),
    ("24'",   24, "Osimhen",  0.01, 0.00, 33, "Left foot",  "Off target",  2,  "High Wide Left"),
    ("33'",   33, "Osimhen",  0.15, 0.00,  8, "Header",     "Off target", -5,  "Wide Left"),
    ("44'",   44, "Osimhen",  0.07, 0.00, 16, "Right foot", "Blocked",    -3,  None),
    ("45+1'", 46, "Yilmaz",   0.02, 0.00, 33, "Right foot", "Blocked",    -3,  None),
    ("50'",   50, "Torreira", 0.02, 0.00, 18, "Right foot", "Blocked",    10,  None),
    ("51'",   51, "Osimhen",  0.02, 0.00, 12, "Header",     "Blocked",    -1,  None),
    ("56'",   56, "Osimhen",  0.06, 0.02, 20, "Right foot", "Saved",       0,  "Low Centre"),
    ("57'",   57, "Osimhen",  0.07, 0.00, 16, "Right foot", "Off target", 13,  "Close Right"),
    ("71'",   71, "Leão",     0.03, 0.00, 21, "Left foot",  "Off target",-11,  "Wide Right"),
    ("90+3'", 93, "Osimhen",  0.04, 0.00, 17, "Right foot", "Off target",-13,  "Wide Left"),
]
COLS = ["minute", "sort", "player", "xg", "xgot", "yards", "body", "outcome", "side_m", "end"]
shots = [dict(zip(COLS, row)) for row in SHOTS]

# =============================================================================
# 2. STYLE
# =============================================================================
BG, PANEL = "#111418", "#1B1F26"
TEXT, MUTED, GRID = "#F4F4F4", "#9AA0A9", "#3A404A"
GRASS_DARK, GRASS_LIGHT, PITCH_LINE = "#3B7A3B", "#438A43", "#FFFFFF"
GS_RED, GS_YELLOW = "#C8102E", "#FDB912"

OUTCOME_STYLE = {
    "Goal":       dict(face=GS_YELLOW, edge="#1A1A1A", arrow=GS_YELLOW, ls="-"),
    "Saved":      dict(face="#FFFFFF", edge="#1A1A1A", arrow="#FFFFFF", ls="-"),
    "Off target": dict(face=GS_RED,    edge="#FFFFFF", arrow=GS_RED,    ls=(0, (4, 3))),
    "Blocked":    dict(face="#5A5F66", edge="#FFFFFF", arrow="#2B2F33", ls="-"),
}
OUTLINE = [pe.withStroke(linewidth=3, foreground="#1A1A1A")]   # makes text readable on grass
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TEXT})

# =============================================================================
# 3. GEOMETRY
# =============================================================================
LENGTH, WIDTH = 105.0, 68.0
GOAL_Y = WIDTH / 2
POST = 7.32 / 2

END_SIDE = {"High Right": 2.6, "Low Centre": 0.0, "High Wide Left": -5.5,
            "Wide Left": -5.0, "Close Right": 4.3, "Wide Right": 5.0}
GOALMOUTH = {"High Right": (2.6, 1.95), "Low Centre": (0.0, 0.35),
             "High Wide Left": (-4.9, 2.9), "Wide Left": (-4.4, 0.9),
             "Close Right": (4.1, 0.6), "Wide Right": (4.7, 0.9)}


# Label position for shots in crowded spots: (x, y, alignment) on the pitch.
# Every other shot gets its label directly under the circle.
LABEL_POS = {
    "12'":   (37.2, 91.6, "left"),
    "15'":   (44.8, 95.3, "left"),
    "50'":   (45.2, 91.3, "left"),
    "57'":   (48.5, 99.2, "left"),
    "51'":   (32.0, 95.6, "right"),
    "44'":   (29.7, 91.4, "right"),
    "22'":   (23.6, 94.4, "right"),
    "90+3'": (19.9, 98.9, "right"),
    "33'":   (26.4, 101.6, "right"),
}


def shot_xy(shot):
    """Real distance + commentary side -> plot coordinates (across, up-field)."""
    d = shot["yards"] * 0.9144
    side = max(-d, min(d, shot["side_m"]))
    return GOAL_Y + side, LENGTH - math.sqrt(d ** 2 - side ** 2)


# =============================================================================
# 4. PANELS
# =============================================================================
def draw_pitch(ax, bottom=68):
    # mowing stripes, like a real stadium pitch
    stripe = 5.25
    y, i = bottom - 2, 0
    while y < LENGTH:
        ax.add_patch(Rectangle((-3, y), WIDTH + 6, stripe, zorder=0,
                               color=GRASS_LIGHT if i % 2 else GRASS_DARK))
        y += stripe
        i += 1
    ax.add_patch(Rectangle((-3, LENGTH), WIDTH + 6, 5, color=GRASS_DARK, zorder=0))

    lw = dict(color=PITCH_LINE, linewidth=2, zorder=1)
    ax.plot([0, 0, WIDTH, WIDTH], [bottom - 2, LENGTH, LENGTH, bottom - 2], **lw)
    ax.add_patch(Rectangle((GOAL_Y - 20.15, LENGTH - 16.5), 40.3, 16.5, fill=False, **lw))
    ax.add_patch(Rectangle((GOAL_Y - 9.15, LENGTH - 5.5), 18.3, 5.5, fill=False, **lw))
    ax.add_patch(Rectangle((GOAL_Y - POST, LENGTH), 2 * POST, 1.8, fill=False, **lw))
    ax.add_patch(Arc((GOAL_Y, LENGTH - 11), 18.3, 18.3, theta1=217, theta2=323, **lw))
    ax.scatter(GOAL_Y, LENGTH - 11, s=12, color=PITCH_LINE, zorder=1)
    ax.set_xlim(-3, WIDTH + 3)
    ax.set_ylim(bottom, LENGTH + 4)
    ax.set_aspect("equal")
    ax.axis("off")


def shot_map(ax):
    draw_pitch(ax)
    for s in sorted(shots, key=lambda s: s["xg"]):          # small shots drawn first
        st = OUTCOME_STYLE[s["outcome"]]
        x, y = shot_xy(s)

        if s["outcome"] == "Blocked":                         # short line + X
            dx, dy = GOAL_Y - x, LENGTH - y
            k = 2.4 / math.hypot(dx, dy)
            ex, ey = x + dx * k, y + dy * k
            ax.plot([x, ex], [y, ey], color=st["arrow"], lw=2, zorder=2)
            ax.scatter(ex, ey, marker="x", s=55, color=st["arrow"], lw=2.2, zorder=2)
        else:                                                 # arrow to where the ball went
            ex, ey = GOAL_Y + END_SIDE[s["end"]], LENGTH + 0.3
            ax.annotate("", xy=(ex, ey), xytext=(x, y), zorder=2,
                        arrowprops=dict(arrowstyle="-|>", color=st["arrow"], lw=2,
                                        ls=st["ls"], shrinkA=7, shrinkB=0,
                                        mutation_scale=13,
                                        path_effects=[pe.withStroke(linewidth=3.5,
                                                                    foreground="#1A1A1A")]))

        ax.scatter(x, y, s=2600 * s["xg"] + 90, facecolor=st["face"], edgecolor=st["edge"],
                   linewidth=1.6, zorder=3, marker="s" if s["body"] == "Header" else "o")
        # label: minute, and the player's name below it
        lx, ly, ha = LABEL_POS.get(s["minute"], (x, y - 2.1, "center"))
        ax.text(lx, ly, s["minute"], ha=ha, va="top", fontsize=8,
                color=TEXT, zorder=4, path_effects=OUTLINE)
        ax.text(lx, ly - 1.9, s["player"], ha=ha, va="top", fontsize=7,
                color="#E0E0E0", zorder=4, path_effects=OUTLINE)

    handles = [Line2D([], [], marker="o", ls="", ms=10, mfc=OUTCOME_STYLE[k]["face"],
                      mec=OUTCOME_STYLE[k]["edge"], label=k) for k in OUTCOME_STYLE]
    handles.append(Line2D([], [], marker="s", ls="", ms=9, mfc="none", mec=TEXT, label="Header"))
    ax.legend(handles=handles, loc="upper center", ncol=5, frameon=False, fontsize=10,
              labelcolor=TEXT, bbox_to_anchor=(0.5, -0.01), columnspacing=1.4)
    ax.set_title("Where the shots came from, and where they went  ·  circle size = xG",
                 loc="left", fontsize=11, color=MUTED, pad=8)


def goal_mouth(ax):
    ax.set_facecolor(BG)
    ax.add_patch(Rectangle((-POST, 0), 2 * POST, 2.44, color="#20252C", zorder=0))
    for gx in [-POST + i * (2 * POST / 8) for i in range(1, 8)]:
        ax.plot([gx, gx], [0, 2.44], color=GRID, lw=0.6)
    for gy in [0.61, 1.22, 1.83]:
        ax.plot([-POST, POST], [gy, gy], color=GRID, lw=0.6)
    ax.plot([-POST, -POST, POST, POST], [0, 2.44, 2.44, 0], color=TEXT, lw=4,
            solid_capstyle="round")
    ax.plot([-6.5, 6.5], [0, 0], color=GRASS_LIGHT, lw=3)

    seen = {}
    for s in shots:
        if s["end"] is None:
            continue
        gx, gy = GOALMOUTH[s["end"]]
        n = seen.get(s["end"], 0)
        seen[s["end"]] = n + 1
        gx += n * (1.0 if s["outcome"] == "Off target" else 0.6) * (-1 if n % 2 else 1)
        st = OUTCOME_STYLE[s["outcome"]]
        size = 2400 * max(s["xgot"], 0.03) + 80 if s["outcome"] in ("Goal", "Saved") else 90
        ax.scatter(gx, gy, s=size, facecolor=st["face"], edgecolor=st["edge"], lw=1.6, zorder=3)
        above = s["outcome"] == "Goal" and gy > 1
        ax.text(gx, gy + (0.45 if above else -0.3), s["minute"], ha="center",
                va="bottom" if above else "top", fontsize=8.5, color=TEXT)

    ax.set_xlim(-6.5, 6.5)
    ax.set_ylim(-0.5, 3.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Goal view  ·  circle size = xGOT", loc="left", fontsize=11, color=MUTED, pad=6)


def player_table(ax):
    """A simple, readable table: one row per player."""
    ax.axis("off")
    ax.set_title("Players", loc="left", fontsize=11, color=MUTED, pad=6)

    players = {}
    for s in shots:
        p = players.setdefault(s["player"], dict(shots=0, on=0, xg=0.0, goals=0))
        p["shots"] += 1
        p["on"] += s["outcome"] in ("Goal", "Saved")
        p["xg"] += s["xg"]
        p["goals"] += s["outcome"] == "Goal"
    order = sorted(players, key=lambda k: (-players[k]["xg"], k))

    cols = [("Player", 0.00, "left"), ("Shots", 0.48, "right"), ("On target", 0.68, "right"),
            ("xG", 0.83, "right"), ("Goals", 0.99, "right")]
    row_h = 1 / (len(order) + 1.3)
    for label, x, ha in cols:
        ax.text(x, 1 - row_h * 0.6, label.upper(), ha=ha, va="center", fontsize=8.5,
                color=MUTED, fontweight="bold", transform=ax.transAxes)
    ax.plot([0, 1], [1 - row_h * 1.1] * 2, color=GRID, lw=1, transform=ax.transAxes)

    for i, name in enumerate(order):
        p = players[name]
        y = 1 - row_h * (i + 1.7)
        hi = p["goals"] > 0
        color = GS_YELLOW if hi else TEXT
        values = [name, str(p["shots"]), str(p["on"]), f'{p["xg"]:.2f}', str(p["goals"])]
        for (label, x, ha), v in zip(cols, values):
            ax.text(x, y, v, ha=ha, va="center", fontsize=11.5, color=color,
                    fontweight="bold" if hi else "normal", transform=ax.transAxes)


def xg_timeline(ax):
    ax.set_facecolor(BG)
    xs, ys, total = [0], [0], 0.0
    for s in sorted(shots, key=lambda s: s["sort"]):
        xs += [s["sort"], s["sort"]]
        ys += [total, total + s["xg"]]
        total += s["xg"]
    xs.append(95)
    ys.append(total)
    ax.fill_between(xs, ys, color=GS_RED, alpha=0.18, step=None)
    ax.plot(xs, ys, color=GS_RED, lw=2.6)

    for s in shots:
        if s["outcome"] == "Goal":
            yv = sum(t["xg"] for t in shots if t["sort"] <= s["sort"])
            ax.scatter(s["sort"], yv, s=90, color=GS_YELLOW, edgecolor="#1A1A1A", zorder=4)
    ax.text(16, 0.62, "Batrakov 12', 15'", color=GS_YELLOW, fontsize=9.5)
    ax.text(94, total + 0.05, f"{total:.2f} xG", ha="right", color=TEXT, fontsize=10,
            fontweight="bold")

    ax.axvline(45, color=GRID, lw=1)
    ax.text(45.8, 1.12, "HT", color=MUTED, fontsize=8)
    ax.set_xlim(0, 95)
    ax.set_ylim(0, 1.25)
    ax.set_xticks([0, 15, 30, 45, 60, 75, 90])
    ax.set_xticklabels(["0'", "15'", "30'", "45'", "60'", "75'", "90'"])
    ax.set_yticks([0, 0.5, 1.0])
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.grid(axis="y", color=GRID, lw=0.5)
    ax.set_title("xG during the match  ·  ● = goal", loc="left", fontsize=11, color=MUTED, pad=6)


def kpi_row(fig, top):
    n = len(shots)
    kpis = [("Goals", str(sum(s["outcome"] == "Goal" for s in shots)), GS_YELLOW),
            ("xG", f'{sum(s["xg"] for s in shots):.2f}', GS_YELLOW),
            ("Shots", str(n), TEXT),
            ("On target", str(sum(s["outcome"] in ("Goal", "Saved") for s in shots)), TEXT),
            ("xGOT", f'{sum(s["xgot"] for s in shots):.2f}', TEXT)]
    w, gap, left = 0.176, 0.01, 0.035
    for i, (label, value, color) in enumerate(kpis):
        x0 = left + i * (w + gap)
        fig.patches.append(FancyBboxPatch((x0, top), w, 0.085,
                                          boxstyle="round,pad=0,rounding_size=0.01",
                                          transform=fig.transFigure, facecolor=PANEL,
                                          edgecolor="none"))
        fig.text(x0 + 0.015, top + 0.042, value, fontsize=24, fontweight="bold", color=color)
        fig.text(x0 + 0.015, top + 0.016, label, fontsize=10.5, color=MUTED)


# =============================================================================
# 5. BUILD THE REPORT
# =============================================================================
fig = plt.figure(figsize=(16, 10.5), facecolor=BG)

fig.text(0.035, 0.952, "GALATASARAY  2–0  VfB STUTTGART", fontsize=26, fontweight="bold")
fig.text(0.035, 0.918, "UEFA Champions League · League phase, matchday 4 · 3 November 2026",
         fontsize=11.5, color=MUTED)
fig.text(0.965, 0.952, "SHOT REPORT", fontsize=15, fontweight="bold", color=GS_RED, ha="right")
fig.text(0.965, 0.922, "Galatasaray", fontsize=11.5, color=MUTED, ha="right")

kpi_row(fig, 0.80)

shot_map(fig.add_axes([0.02, 0.07, 0.55, 0.69]))
goal_mouth(fig.add_axes([0.61, 0.53, 0.36, 0.23]))
player_table(fig.add_axes([0.62, 0.30, 0.34, 0.19]))
xg_timeline(fig.add_axes([0.63, 0.07, 0.33, 0.16]))

fig.text(0.035, 0.018,
         "Data: ESPN (xG, xGOT, distance, goal zone) · Sky Sports / Opta commentary (outcome, "
         "shot zone). Distance from goal is exact; position across the pitch is approximate.",
         fontsize=8, color=MUTED)

plt.savefig("galatasaray_shot_report.png", dpi=150, facecolor=BG)
plt.show()
