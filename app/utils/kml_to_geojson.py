import zipfile
import os
import tempfile
import geopandas as gpd

def kml_or_kmz_to_gdf(file_bytes, filename):
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        # If KMZ, extract KML
        if filename.lower().endswith(".kmz"):
            with zipfile.ZipFile(file_path, 'r') as z:
                kml_files = [f for f in z.namelist() if f.endswith('.kml')]
                if not kml_files:
                    raise Exception("No KML file found in KMZ.")
                kml_filename = kml_files[0]
                z.extract(kml_filename, tmpdir)
                kml_path = os.path.join(tmpdir, kml_filename)
        else:
            kml_path = file_path
        gdf = gpd.read_file(kml_path, driver='KML')
        return gdf
