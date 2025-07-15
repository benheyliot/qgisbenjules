import geopandas as gpd
import os
from flask import Blueprint, jsonify, send_from_directory

vector_bp = Blueprint('vector_bp', __name__)

VECTOR_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'vector')

@vector_bp.route('/vector_layers')
def list_vector_layers():
    files = [f for f in os.listdir(VECTOR_DIR) if f.endswith(('.kml', '.kmz', '.gpkg', '.shp'))]
    return jsonify(files)

@vector_bp.route('/vector_layer/<filename>')
def serve_vector_layer(filename):
    fpath = os.path.join(VECTOR_DIR, filename)
    gdf = gpd.read_file(fpath)
    return jsonify(gdf.__geo_interface__)

RASTER_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raster')

@server.route('/raster/<filename>')
def serve_raster(filename):
    return send_from_directory(RASTER_DIR, filename) 