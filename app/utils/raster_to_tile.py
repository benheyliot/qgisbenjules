import rasterio
import numpy as np
import tempfile
import os

def tiff_to_image_overlay(file_bytes, filename):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
        tmp.write(file_bytes)
        tmp.flush()
        with rasterio.open(tmp.name) as src:
            bounds = src.bounds
            # For MVP, we assume the raster is RGB or single-band
            arr = src.read()
            # You could save as PNG and serve as base64, but for now, return bounds for overlay
            # Advanced: Use rio-tiler for tile serving
        os.unlink(tmp.name)
    # Return bounds as [[south, west], [north, east]]
    return [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
