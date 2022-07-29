import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
#import cartopy
#import cartopy.io.img_tiles as cimgt
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
import requests


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
            #lat_0=bounding_box['lat_ref'],
            #lon_0=bounding_box['lon_ref'],
            #width=1e5,
            #height=1e5,
            #epsg=4326)
            epsg=2805)

    m.arcgisimage(server='https://server.arcgisonline.com/arcgis/', service="NatGeo_World_Map", #"ESRI_Imagery_World_2D",
            xpixels=1500,
            transparent=False,
            verbose=True)
   # url = 'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}.jpg'
   # image = cimgt.GoogleTiles(url=url)
   # m.add_image(image,1)
   # m.arcgisimage(server='https://server.arcgisonline.com/ArcGIS/rest/services', service="NatGeo_World_Map", #"ESRI_Imagery_World_2D",
   #         verbose=True)

#https://server.arcgisonline.com/arcgis/rest/services/NatGeo_World_Map/MapServer/export?bbox=-4.928494022432936E7,-3.583813558334303E7,4.928494022432936E7,3.583813558334303E7
    
    #img_data = requests.get('https://server.arcgisonline.com/arcgis/rest/services/NatGeo_World_Map/MapServer/export?bbox=-4.928494022432936E7,-3.583813558334303E7,4.928494022432936E7,3.583813558334303E7&bboxSR=4326&layers=&layerDefs=&size=&imageSR=&historicMoment=&format=jpg&transparent=false&dpi=&time=&timeRelation=esriTimeRelationOverlaps&layerTimeOptions=&dynamicLayers=&gdbVersion=&mapScale=&rotation=&datumTransformations=&layerParameterValues=&mapRangeValues=&layerRangeValues=&clipping=&spatialFilter=&f=image')
  #  img_data=requests.get('https://server.arcgisonline.com/ArcGIS/rest/services/rest/services/NatGeo_World_Map/MapServer/export?bbox=-1.239183768915974,0.7374016089676042,-1.2365657750379824,0.7400196028455958&bboxSR=4326&imageSR=4326&size=400,399&dpi=96&format=png32&transparent=true&f=image')
    plt.show(block=False)


if __name__=="__main__":
    main()
