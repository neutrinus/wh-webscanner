
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np

from mpl_toolkits.basemap import Basemap


def make_map(points, dpi=92, min_map=True, size=None, fix_aspect=False, file_path=None):
    '''
    :param points: list/tuple of points (tuples of 2 floats like (lon, lat))
    :param size: tuple of two floats (size of figure in inches)
    :param file_path: where to save the image
    '''
    if not size:
        size = (10, 10)
    fig = Figure(size, dpi=dpi)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0.0, 0.0, 1, 1])
    ax.patch.set_alpha(0.5)
    ax.patch.set_facecolor('none')

    map = Basemap(projection='merc',
                  llcrnrlat=-55,
                  urcrnrlat=80,
                  llcrnrlon=-180,
                  urcrnrlon=180,
                  lat_ts=20,
                  resolution='c',
                  fix_aspect=fix_aspect,
                  ax=ax)
    #map.shadedrelief(scale=0.3)
    map.drawcoastlines()
    map.drawcountries(linewidth=1.0)
    map.fillcontinents(color='brown', lake_color='none')
    #map.drawparallels(np.arange(-90.,91.,30.))
    #map.drawmeridians(np.arange(-180.,181.,60.))
    #map.drawmapboundary(fill_color='aqua')
    for point in points:
        x, y = map(point[0], point[1])
        map.plot([x], [y], 'ro')
        if len(point) > 2:
            ax.text(x, y, point[2], bbox=dict(facecolor='green', alpha=0.7))
    if file_path:
        can = FigureCanvas(fig)
        can.print_figure(file_path, dpi=dpi, transparent=True)
    return fig
