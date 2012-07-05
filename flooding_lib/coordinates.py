"""Functions to transform coordinates.

Mostly copied from lizard-map. Didn't want to require the whole of lizard-map
into flooding just for these functions."""

from pyproj import Proj
from pyproj import transform

RD = ("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 "
      "+k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel "
      "+towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 "
      "+units=m +no_defs")
GOOGLE = ('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 '
          '+lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m '
          '+nadgrids=@null +no_defs +over')
WGS84 = ('+proj=latlong +datum=WGS84')

rd_projection = Proj(RD)
google_projection = Proj(GOOGLE)
wgs84_projection = Proj(WGS84)


def wgs84_to_rd(x, y):
    """Return WGS84 coordinates from RD coordinates."""
    return transform(wgs84_projection, rd_projection, x, y)
