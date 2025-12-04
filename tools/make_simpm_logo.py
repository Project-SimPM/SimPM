import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle


def make_simpm_logo(path="simpm_logo.png"):
    # Square canvas, high resolution
    fig = plt.figure(figsize=(5, 5), dpi=500)
    ax = fig.add_axes([0, 0, 1, 1])

    # Coordinate system 0–1
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")

    # Transparent background
    fig.patch.set_alpha(0.0)
    ax.set_facecolor((0, 0, 0, 0))

    # --- TEXT: "Sim" over "PM" ---
    text_color = "#0f7b1c"  # main green
    ax.text(
        0.14,
        0.64,
        "Sim",
        fontfamily="DejaVu Sans",
        fontsize=72,
        fontweight="bold",
        color=text_color,
        ha="left",
        va="center",
    )
    ax.text(
        0.14,
        0.34,
        "PM",
        fontfamily="DejaVu Sans",
        fontsize=72,
        fontweight="bold",
        color=text_color,
        ha="left",
        va="center",
    )

    # --- TRIANGLE OUTLINE ---
    tri_coords = [(0.55, 0.22), (0.88, 0.50), (0.55, 0.78)]
    tri = Polygon(
        tri_coords,
        closed=True,
        edgecolor=text_color,
        linewidth=3,
        fill=False,
        joinstyle="round",
    )
    ax.add_patch(tri)

    # --- STRIPED FILL INSIDE TRIANGLE ---
    colors = ["#0f7b1c", "#1c8430", "#2e8b57", "#56a970", "#a1d99b"]
    n = len(colors)

    x_start, x_end = 0.55, 0.88
    total_width = x_end - x_start
    bar_width = total_width / (n + 1)  # small gap at ends

    for i, c in enumerate(colors):
        x = x_start + (i + 0.5) * bar_width
        bar = Rectangle(
            (x, 0.22),
            bar_width * 0.9,  # a bit of gap between bars
            0.56,
            facecolor=c,
            edgecolor="none",
        )
        # Clip bars to triangle shape
        bar.set_clip_path(tri)
        ax.add_patch(bar)

    # Save with transparent background (good for Sphinx / RTD)
    plt.savefig(path, dpi=500, transparent=True)
    plt.close(fig)


if __name__ == "__main__":
    make_simpm_logo("docs/_static/simpm_logo.png")
