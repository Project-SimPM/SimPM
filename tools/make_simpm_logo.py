import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
import numpy as np

def make_simpm_logo(path="simpm_logo.png"):
    # Square canvas, high resolution
    fig = plt.figure(figsize=(5, 5), dpi=500)
    ax = fig.add_axes([0, 0, 1, 1])
    stretch = 0
    xlim = (-1.3,.7)
    w = 2
    ax.set_xlim([xlim[0]-stretch*w, xlim[1]+stretch*w])
    ylim = (-1,1)
    h = 2
    ax.set_ylim([ylim[0]-stretch*h, ylim[1]+stretch*h])
    ax.fill([0,0,.7],[-.55,.45,0],color="green",alpha=1)  
    for i in np.linspace(0,.8,5):
        ax.fill([0+i/2,0+i/2,.7],[-.55,.45,0],color="white",alpha=.2) 
    ax.text(-1.25,0.05,"Sim",fontsize=80,color="green",fontweight="bold")
    ax.text(-1.1,-.5,"PM",fontsize=80,color="green",fontweight="bold") 
    plt.axis("off")

    # Save with transparent background (good for Sphinx / RTD)
    plt.savefig(path, dpi=500, transparent=False)
    plt.close(fig)


if __name__ == "__main__":
    make_simpm_logo("docs/_static/simpm_logo.png")
