from pyexpat.model import XML_CQUANT_REP
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
#import geopandas as gpd
import pandas as pd
from urllib import request as urlrequest
import os
import sys
import json
import utm
from PIL import Image
from datetime import datetime
import pathlib

# bounding boxes using CGAL
from CGAL.CGAL_Kernel import Point_2
from CGAL.CGAL_Triangulation_2 import Constrained_Delaunay_triangulation_2


def main():
    fig = plt.figure(figsize=(16,16))

    # boston
    bounding_box = {"lat0": 42.25,
            "lat1": 42.4,
            "lon0": -71.,
            "lon1": -70.85,
            "lat_ref": 42.36,
            "lon_ref": -71.03}


    m = Basemap(projection='tmerc',
            #resolution='h',
            llcrnrlon=bounding_box['lon0'],
            urcrnrlon=bounding_box['lon1'],
            llcrnrlat=bounding_box['lat0'],
            urcrnrlat=bounding_box['lat1'],
            lat_0=bounding_box['lat_ref'],
            lon_0=bounding_box['lon_ref'],
            #width=1e5,
            #height=1e5,
            epsg=4326)

    m.arcgisimage(service="NatGeo_World_Map", #"ESRI_Imagery_World_2D",
            xpixels=1500,
            transparent=False,
            verbose=True)
    plt.show(block=False)


if __name__=="__main__":
    main()
