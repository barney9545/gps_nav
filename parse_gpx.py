import gpxpy
from motonav_logger import MOTONAV_LOGGER
from motonav_exceptions import ConfigurationError

def get_route_data(gpx_file_path):
    """
    Parses a GPX file to extract coordinates and calculate the center point.
    Returns: center_lat, center_lon, route_coords list
    """
    
    # 1. Open and Parse the GPX file
    try:
        with open(gpx_file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
    except FileNotFoundError:
        MOTONAV_LOGGER.error(f"GPX file not found at {gpx_file_path}")
        raise ConfigurationError(f"GPX file not found at {gpx_file_path}")
    except Exception as e:
        MOTONAV_LOGGER.error(f"Error parsing GPX file: {e}")
        raise ConfigurationError(f"Error parsing GPX file: {e}")

    # 2. Extract all coordinates
    route_coords = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                route_coords.append((point.latitude, point.longitude))

    if not route_coords:
        MOTONAV_LOGGER.warning("GPX file contains no coordinates.")
        return 0, 0, []

    # 3. Calculate Bounding Box and Center
    bounds = gpx.get_bounds()
    
    # Calculate the center point for MapView starting location
    center_lat = (bounds.min_latitude + bounds.max_latitude) / 2
    center_lon = (bounds.min_longitude + bounds.max_longitude) / 2
    
    return center_lat, center_lon, route_coords

# Test the function (optional, but good for debugging)
if __name__ == "__main__":
    GPX_FILE = "test_route.gpx"
    try:
        lat, lon, coords = get_route_data(GPX_FILE)
        
        MOTONAV_LOGGER.info(f"Route Loaded. Total Points: {len(coords)}")
        MOTONAV_LOGGER.info(f"Map Center: ({lat:.4f}, {lon:.4f})")
        MOTONAV_LOGGER.info(f"First Point: {coords[0]}")
        MOTONAV_LOGGER.info(f"Last Point: {coords[-1]}")
    except ConfigurationError as e:
        MOTONAV_LOGGER.critical(f"Failed to load route: {e}")