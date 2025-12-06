import gpxpy
from landez import MBTilesBuilder

# --- 1. Get Bounding Box from GPX (from your parse_gpx.py logic) ---
def get_gpx_bbox(gpx_file_path):
    with open(gpx_file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
    
    # gpxpy returns the overall bounds object
    bounds = gpx.get_bounds()
    if not bounds:
        raise ValueError("GPX file is empty or has no bounds.")

    # Landez requires a standard bbox tuple: (min_lon, min_lat, max_lon, max_lat)
    bbox = (
        bounds.min_longitude,
        bounds.min_latitude,
        bounds.max_longitude,
        bounds.max_latitude,
    )
    return bbox

# --- 2. Download and Package Tiles ---
def build_mbtiles(gpx_path, output_filepath, zoomlevels):
    # Get the bounding box of your route
    bbox = get_gpx_bbox(gpx_path)
    
    print(f"Route Bounding Box: {bbox}")
    print(f"Starting tile download for ZL {zoomlevels[0]} to {zoomlevels[-1]}...")
    
    # Initialize the MBTiles Builder
    # Using the standard OpenStreetMap tile server. 
    # NOTE: Be respectful of their usage policy (don't abuse for bulk download)
    mb = MBTilesBuilder(
        tiles_url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        filepath=output_filepath
    )
    
    # Download coverage based on BBox and Zoom Levels
    mb.add_coverage(
        bbox=bbox, 
        zoomlevels=zoomlevels
    )
    
    # Run the download and packaging process
    mb.run()
    print(f"\n✅ MBTiles file created successfully at: {output_filepath}")

# --- 3. Execution ---
if __name__ == "__main__":
    GPX_FILE = "test_route.gpx" # Ensure you have this file
    MBTILES_FILE = "motonav_offline_map.mbtiles"
    ZOOM_LEVELS = [12, 13, 14, 15, 16] 
    
    # You may need to create a dummy test_route.gpx file with a short path here
    # E.g., a path between two major cities for a good BBox
    
    build_mbtiles(GPX_FILE, MBTILES_FILE, ZOOM_LEVELS)