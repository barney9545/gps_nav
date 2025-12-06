import os
import time
import pynmea2
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock # CRITICAL for scheduling GPS updates
from kivy.graphics import Line, Color, Scale, Translate
from kivy_garden.mapview import MapView
from kivy_garden.mapview.view import MapLayer
from kivy_garden.mapview import MapMarker

# Import your custom modules
from motonav_logger import MOTONAV_LOGGER as log
from motonav_exceptions import ConfigurationError, GPSCommunicationError
from parse_gpx import get_route_data
from gps_simulator import get_gps_data_source
from mbtiles_source import MBTilesMapSource


# --- Constants ---
GPX_FILE = "test_route.gpx"
MBTILES_FILE_PATH = "motonav_offline_map.mbtiles"
DEFAULT_ZOOM = 14

# --- 1. Custom Map Layer to Draw the Route (from previous plan) ---
class GPXRouteLayer(MapLayer):
    """Draws the fixed GPX route trace on the map."""
    def __init__(self, coordinates, **kwargs):
        super().__init__(**kwargs)
        self.coordinates = coordinates
        self.zoom = 0
        
    def reposition(self):
        # Trigger redraw only when zoom changes significantly
        if self.zoom != self.parent.zoom:
            self.draw_route()
        
    def draw_route(self, *args):
        mapview = self.parent
        self.zoom = mapview.zoom
        
        self.canvas.clear()
        
        # Check if mapview is ready
        if mapview.width == 0 or mapview.height == 0:
             return
             
        scatter = mapview._scatter
        # Use safe check for scatter scale
        ss = scatter.scale if scatter.scale != 0 else 1 
        
        line_points = []
        for lat, lon in self.coordinates:
            # Convert Lat/Lon to screen X/Y using MapView helper
            x, y = mapview.get_window_xy_from(lat, lon, mapview.zoom)
            line_points.extend((x, y))
            
        with self.canvas:
            # Apply reverse transformations
            Scale(1/ss, 1/ss, 1)
            Translate(-scatter.x, -scatter.y) 
            
            # Draw the route line
            Color(1, 0, 0, 0.8)  # Bright Red
            Line(points=line_points, width=4, joint='round', cap='round')

# --- 2. Main MotoNav Application ---
class MotoNavApp(App):
    def build(self):
        log.info("Starting MotoNav App build process.")

        # --- A. Setup Validation and Data Load ---
        try:
            # File existence check
            if not os.path.exists(GPX_FILE):
                raise ConfigurationError(f"Required GPX route file not found: {GPX_FILE}")
            if not os.path.exists(MBTILES_FILE_PATH):
                raise ConfigurationError(f"Required MBTiles file not found: {MBTILES_FILE_PATH}")
                
            center_lat, center_lon, self.route_coords = get_route_data(GPX_FILE)
            log.info(f"GPX route loaded. Center: ({center_lat:.4f}, {center_lon:.4f})")

            # GPS setup (use mock for local development)
            self.gps_serial = get_gps_data_source(use_mock=True)
            if not self.gps_serial or not self.gps_serial.is_open():
                 raise GPSCommunicationError("Could not initialize GPS data source.")

        except (ConfigurationError, GPSCommunicationError) as e:
            log.critical(f"FATAL SETUP FAILURE: {e}")
            # Display simple error screen if critical files are missing
            return Label(text=f"SETUP ERROR: {e}\nCheck logs for details.", color=(1,0,0,1))

        # --- B. UI Layout ---
        main_layout = BoxLayout(orientation='vertical')
        
        self.map_view = MapView(
            zoom=DEFAULT_ZOOM,
            lat=center_lat,
            lon=center_lon,
            map_source=MBTilesMapSource(MBTILES_FILE_PATH)
        )

        
        # 2. Add GPX Route Trace
        route_layer = GPXRouteLayer(coordinates=self.route_coords)
        self.map_view.add_layer(route_layer)
        
        # 3. Add GPS Position Marker (Initialized at the center)
        self.rider_marker = MapMarker(lat=center_lat, lon=center_lon, source='dot.png') # Use a simple image
        self.map_view.add_marker(self.rider_marker)
        
        # 4. Dashboard (F-07)
        self.lbl_speed = Label(text="Speed: --", color=(1,1,1,1))
        self.lbl_dist = Label(text="Dist: --", color=(1,1,1,1))
        self.lbl_eta = Label(text="ETA: --", color=(1,1,1,1))
        
        dashboard = BoxLayout(size_hint_y=None, height=50, padding=5, spacing=10)
        dashboard.add_widget(self.lbl_speed)
        dashboard.add_widget(self.lbl_dist)
        dashboard.add_widget(self.lbl_eta)
        
        # 5. Assemble
        main_layout.add_widget(self.map_view)
        main_layout.add_widget(dashboard)
        
        # --- C. Start GPS Update Loop ---
        # Schedule the update_gps function to run every 0.5 seconds
        Clock.schedule_interval(self.update_gps, 0.5) 
        log.info("Kivy update loop scheduled.")
        
        return main_layout

    def update_gps(self, dt):
        """Reads a line from the serial port (or mock) and updates the map."""
        try:
            raw_data = self.gps_serial.readline()
            
            # Check for valid NMEA header ($GP)
            if raw_data.startswith(b'$GP'):
                data_string = raw_data.decode('utf-8', errors='ignore').strip()
                
                # Use pynmea2 to parse the message
                msg = pynmea2.parse(data_string)
                
                # We only care about GPGGA messages for location/fix quality
                if msg.sentence_type == 'GGA':
                    if msg.latitude and msg.longitude:
                        log.debug(f"New GPS Fix: ({msg.latitude:.4f}, {msg.longitude:.4f})")
                        
                        # 1. Update the marker position on the map
                        self.rider_marker.lat = msg.latitude
                        self.rider_marker.lon = msg.longitude
                        
                        # 2. Center the map on the new position (optional, but good for nav)
                        self.map_view.center_on(msg.latitude, msg.longitude)
                        
                        # 3. Update dashboard labels (using placeholders for now)
                        self.lbl_speed.text = f"Speed: 50 km/h" # Placeholder for future RMC data
                        self.lbl_dist.text = f"Dist: 10.5 km"
                        self.lbl_eta.text = f"ETA: 30 min"
                        
                    elif msg.gps_qual == 0:
                        log.warning("GPS has no fix (Quality 0).")
            
        except StopIteration:
            # Occurs when the mock generator runs out (shouldn't happen in the infinite loop)
            log.warning("GPS simulator stopped running.")
        except Exception as e:
            # Catch all unexpected errors during reading/parsing
            log.exception(f"Error during GPS update loop: {e}")

    def on_stop(self):
        """Called when the application is closed."""
        if self.gps_serial:
            self.gps_serial.close()
        log.info("MotoNav Application closed.")

if __name__ == '__main__':
    # Ensure a basic image file exists for the marker
    # You can use a small image named 'dot.png' or any placeholder.
    # Otherwise, delete the 'source' argument in MapMarker to use the default circle.
    
    # Run the application
    MotoNavApp().run()