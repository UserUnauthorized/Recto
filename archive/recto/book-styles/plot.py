"""Generate the shared, vector-only mathematical figure for all editions."""
from pathlib import Path
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).parent
(root / "assets").mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Serif", "mathtext.fontset": "stix", "font.size": 10,
                     "svg.fonttype": "path", "axes.linewidth": .6})
x = [-1.5 + 3 * i / 400 for i in range(401)]
fig, ax = plt.subplots(figsize=(5.6, 2.25))
ax.plot(x, [math.sin(t) for t in x], color="#151515", lw=1.3, label=r"$\sin x$")
ax.plot(x, [t - t**3 / 6 for t in x], color="#777777", lw=1.2,
        linestyle=(0, (4, 2)), label=r"$x-x^3/6$")
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["bottom", "left"]].set_color("#777777")
ax.axhline(0, color="#dddddd", lw=.55, zorder=0)
ax.axvline(0, color="#dddddd", lw=.55, zorder=0)
ax.set(xlim=(-1.5,1.5), ylim=(-1.08,1.08), xticks=[-1.5,-1,-.5,0,.5,1,1.5], yticks=[-1,0,1])
ax.set_xlabel("x", loc="right", labelpad=-3)
ax.tick_params(length=3, width=.6, labelsize=8)
ax.legend(frameon=False, loc="upper left", fontsize=9, handlelength=2.3)
fig.tight_layout(pad=.5)
fig.savefig(root / "assets/approximation.svg", transparent=True)
plt.close(fig)
