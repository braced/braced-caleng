from matplotlib import pyplot as plt
from shapely.geometry.polygon import LinearRing, Polygon
from braced.settings import DEBUG

print(DEBUG)


def plot(polygon):
    if not DEBUG:
        print("Dont plot in development")
    else:
        x, y = polygon.exterior.xy
        fig = plt.figure(1, figsize=(5, 5), dpi=90)
        ax = fig.add_subplot(111)
        ax.plot(x, y)
        ax.set_title('Polygon Edges')
        xrange = [-1, 3]
        yrange = [-1, 3]
        ax.set_xlim(*xrange)
        ax.set_xticks(list(range(*xrange)) + [xrange[-1]])
        ax.set_ylim(*yrange)
        ax.set_yticks(list(range(*yrange)) + [yrange[-1]])
        ax.set_aspect(1)
        plt.savefig('last_plot.png')
