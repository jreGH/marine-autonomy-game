"""
map_utils.py — coordinate conversion and tile download for the BWSI mission builder
====================================================================================

Provides:
  latlon_to_xy(lat, lon, origin_lat, origin_lon) → (x_m, y_m)
  xy_to_latlon(x, y, origin_lat, origin_lon)     → (lat, lon)
  bbox_from_origin_and_radius(lat, lon, radius_m) → dict
  download_tiles(...)                             → dict with output path + world file
"""

import math
import os
import struct
import urllib.request
import urllib.error
from pathlib import Path
from typing import NamedTuple

# WGS-84 mean Earth radius (m)
R_EARTH = 6_371_000.0


# ---------------------------------------------------------------------------
# Flat-earth projection (same formula used by MOOS-IvP internally)
# ---------------------------------------------------------------------------

def latlon_to_xy(lat: float, lon: float,
                 origin_lat: float, origin_lon: float) -> tuple[float, float]:
    """
    Convert geodetic (lat, lon) to MOOS local XY metres.

    Uses the equirectangular (flat-earth) projection centred on origin.
    Accurate to < 1% error for distances up to ~100 km.

    Returns:
        (x, y) where x = east metres, y = north metres
    """
    dlat = math.radians(lat - origin_lat)
    dlon = math.radians(lon - origin_lon)
    x = dlon * R_EARTH * math.cos(math.radians(origin_lat))
    y = dlat * R_EARTH
    return x, y


def xy_to_latlon(x: float, y: float,
                 origin_lat: float, origin_lon: float) -> tuple[float, float]:
    """
    Convert MOOS local XY metres back to geodetic (lat, lon).

    Inverse of latlon_to_xy.
    """
    dlat = y / R_EARTH
    dlon = x / (R_EARTH * math.cos(math.radians(origin_lat)))
    lat = origin_lat + math.degrees(dlat)
    lon = origin_lon + math.degrees(dlon)
    return lat, lon


# ---------------------------------------------------------------------------
# Bounding-box helpers
# ---------------------------------------------------------------------------

class BBox(NamedTuple):
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


def bbox_from_origin_and_radius(origin_lat: float, origin_lon: float,
                                 radius_m: float) -> BBox:
    """
    Return a lat/lon bounding box centred on origin with a given half-width.

    Useful for querying tile servers — always request a bbox slightly larger
    than your mission area.
    """
    dlat = math.degrees(radius_m / R_EARTH)
    dlon = math.degrees(radius_m / (R_EARTH * math.cos(math.radians(origin_lat))))
    return BBox(
        min_lat=origin_lat - dlat,
        max_lat=origin_lat + dlat,
        min_lon=origin_lon - dlon,
        max_lon=origin_lon + dlon,
    )


def bbox_from_vertices_latlon(vertices_latlon: list[tuple[float, float]]) -> BBox:
    """Return bounding box for a list of (lat, lon) pairs."""
    lats = [v[0] for v in vertices_latlon]
    lons = [v[1] for v in vertices_latlon]
    return BBox(min(lats), max(lats), min(lons), max(lons))


# ---------------------------------------------------------------------------
# Slippy-map tile arithmetic
# ---------------------------------------------------------------------------

def _deg2tile(lat_deg: float, lon_deg: float, zoom: int) -> tuple[int, int]:
    """Convert lat/lon to OSM tile (x, y) at the given zoom level."""
    lat_r = math.radians(lat_deg)
    n = 2 ** zoom
    x = int((lon_deg + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n)
    return x, y


def _tile2deg(x: int, y: int, zoom: int) -> tuple[float, float]:
    """Convert tile (x, y) at zoom to the NW corner lat/lon."""
    n = 2 ** zoom
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


def _tile_url(source: str, x: int, y: int, zoom: int) -> str:
    """Build the tile URL for the requested tile source."""
    sources = {
        # OpenStreetMap (general)
        "osm": f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png",
        # Stamen Terrain (good for coastal/nautical)
        "stamen_terrain": f"https://stamen-tiles.a.ssl.fastly.net/terrain/{zoom}/{x}/{y}.png",
        # ESRI World Imagery (satellite)
        "esri_satellite": (
            f"https://server.arcgisonline.com/ArcGIS/rest/services/"
            f"World_Imagery/MapServer/tile/{zoom}/{y}/{x}"
        ),
        # CartoDB Positron (clean, light)
        "carto_light": f"https://a.basemaps.cartocdn.com/light_all/{zoom}/{x}/{y}.png",
        # NOAA nautical chart (raster) — uses Web Mercator tile scheme
        "noaa_chart": (
            f"https://tileservice.charts.noaa.gov/tiles/50000_1/{zoom}/{x}/{y}.png"
        ),
    }
    if source not in sources:
        raise ValueError(f"Unknown tile source '{source}'. "
                         f"Available: {list(sources)}")
    return sources[source]


# ---------------------------------------------------------------------------
# Tile stitching
# ---------------------------------------------------------------------------

def download_tiles(
    bbox: BBox,
    zoom: int,
    output_path: str,
    tile_source: str = "osm",
    tfw_path: str | None = None,
) -> dict:
    """
    Download and stitch slippy-map tiles covering the bbox into a single PNG.

    Writes:
        <output_path>        — stitched PNG
        <output_path>.tfw    — ESRI world file (georeferencing for pMarineViewer)

    Returns a dict with:
        {
            "png_path":     str,   # absolute path to the PNG
            "tfw_path":     str,   # absolute path to the world file
            "origin_lat":   float, # lat of image origin (NW corner)
            "origin_lon":   float, # lon of image origin (NW corner)
            "pixel_size_m": float, # approximate metres per pixel
            "tile_count":   int,
        }

    Requires Pillow (pip install pillow).  For real GeoTIFF output (rasterio),
    convert the PNG + .tfw with:
        gdal_translate -of GTiff -a_srs EPSG:4326 output.png output.tif
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError(
            "Pillow is required for tile stitching.  "
            "Run: pip install pillow"
        )

    # Tile range covering the bbox
    x0, y0 = _deg2tile(bbox.max_lat, bbox.min_lon, zoom)  # NW tile
    x1, y1 = _deg2tile(bbox.min_lat, bbox.max_lon, zoom)  # SE tile
    # Clamp to valid tile range
    n_tiles = 2 ** zoom
    x0 = max(0, x0);  x1 = min(n_tiles - 1, x1)
    y0 = max(0, y0);  y1 = min(n_tiles - 1, y1)

    tile_cols = x1 - x0 + 1
    tile_rows = y1 - y0 + 1
    tile_px   = 256  # standard slippy-map tile size
    img_w     = tile_cols * tile_px
    img_h     = tile_rows * tile_px

    stitched = Image.new("RGB", (img_w, img_h))

    total = tile_cols * tile_rows
    count = 0
    print(f"Downloading {total} tiles ({tile_cols}×{tile_rows}) from '{tile_source}'...")

    headers = {"User-Agent": "BWSI-MissionBuilder/1.0"}
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            url = _tile_url(tile_source, tx, ty, zoom)
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    import io
                    tile_img = Image.open(io.BytesIO(resp.read())).convert("RGB")
            except (urllib.error.URLError, Exception) as e:
                print(f"  WARNING: failed to fetch tile {tx},{ty}: {e}")
                tile_img = Image.new("RGB", (tile_px, tile_px), color=(200, 200, 200))

            px = (tx - x0) * tile_px
            py = (ty - y0) * tile_px
            stitched.paste(tile_img, (px, py))
            count += 1
            if count % 10 == 0 or count == total:
                print(f"  {count}/{total} tiles", end="\r", flush=True)

    print()  # newline after progress
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    stitched.save(output_path)

    # ---- World file (.tfw) ----
    # NW corner of the stitched image in lat/lon
    nw_lat, nw_lon = _tile2deg(x0, y0, zoom)
    # SE corner
    se_lat, se_lon = _tile2deg(x1 + 1, y1 + 1, zoom)

    lon_span = se_lon - nw_lon
    lat_span = nw_lat - se_lat   # positive (lat decreases going south)
    pixel_lon = lon_span / img_w
    pixel_lat = lat_span / img_h  # degrees per pixel (positive)

    # Approximate pixel size in metres at the image centre latitude
    centre_lat = (nw_lat + se_lat) / 2
    pixel_size_m = (
        pixel_lat * (math.pi / 180) * R_EARTH * 0.5
        + abs(pixel_lon) * (math.pi / 180) * R_EARTH
          * math.cos(math.radians(centre_lat)) * 0.5
    )

    if tfw_path is None:
        tfw_path = output_path + ".tfw"

    # World file format (6 lines):
    #   pixel_size_x (degrees per pixel, E direction)
    #   rotation_x   (always 0)
    #   rotation_y   (always 0)
    #   pixel_size_y (degrees per pixel, S direction — negative)
    #   x_centre_of_upper_left_pixel (lon)
    #   y_centre_of_upper_left_pixel (lat)
    with open(tfw_path, "w") as f:
        f.write(f"{pixel_lon:.10f}\n")
        f.write(f"0.0\n")
        f.write(f"0.0\n")
        f.write(f"{-pixel_lat:.10f}\n")
        f.write(f"{nw_lon + pixel_lon * 0.5:.10f}\n")
        f.write(f"{nw_lat - pixel_lat * 0.5:.10f}\n")

    return {
        "png_path":     os.path.abspath(output_path),
        "tfw_path":     os.path.abspath(tfw_path),
        "origin_lat":   nw_lat,
        "origin_lon":   nw_lon,
        "pixel_size_m": pixel_size_m,
        "tile_count":   count,
    }


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Test coordinate round-trip
    ORIGIN_LAT, ORIGIN_LON = 43.8253, -70.3304
    test_pairs = [
        (43.8253, -70.3304),   # origin → (0, 0)
        (43.8300, -70.3200),   # north-east
        (43.8150, -70.3500),   # south-west
    ]
    print("Coordinate round-trip test:")
    for lat, lon in test_pairs:
        x, y   = latlon_to_xy(lat, lon, ORIGIN_LAT, ORIGIN_LON)
        lat2, lon2 = xy_to_latlon(x, y, ORIGIN_LAT, ORIGIN_LON)
        err = math.sqrt((lat2 - lat)**2 + (lon2 - lon)**2) * 111_000
        print(f"  ({lat:.4f}, {lon:.4f}) → ({x:+.1f}m, {y:+.1f}m) → "
              f"({lat2:.4f}, {lon2:.4f})  err={err:.3f}m")

    bb = bbox_from_origin_and_radius(ORIGIN_LAT, ORIGIN_LON, 500)
    print(f"\nbbox ±500m: lat {bb.min_lat:.5f}…{bb.max_lat:.5f}, "
          f"lon {bb.min_lon:.5f}…{bb.max_lon:.5f}")
