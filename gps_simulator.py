import time
import pynmea2
from motonav_logger import MOTONAV_LOGGER
from motonav_exceptions import GPSCommunicationError

# Define a simulated starting location (use coordinates near your test_route.gpx center)
SIM_LAT = 21.121556
SIM_LON = 79.056389
SIM_SAT_COUNT = 8

def generate_simulated_nmea():
    """Generates a continuous stream of simulated NMEA GPGGA sentences."""
    global SIM_LAT, SIM_LON
    
    # We will simulate movement by slightly changing coordinates each iteration
    # Small changes simulating movement (e.g., 0.00005 degrees is ~5.5 meters)
    LAT_STEP = 0.00005
    LON_STEP = 0.00003
    
    while True:
        # 1. Update simulated position
        SIM_LAT += LAT_STEP 
        SIM_LON += LON_STEP
        
        # 2. Get current time (required for NMEA timestamp)
        now = time.time()
        timestamp = time.strftime("%H%M%S.00", time.gmtime(now))
        
        # 3. Create a valid GPGGA message object
        # The fields are: timestamp, lat, lat_dir, lon, lon_dir, fix_quality, 
        # num_sats, hdop, alt, alt_unit, geoid_sep, geoid_unit, dgps_age, dgps_id
        msg = pynmea2.types.talker.GGA(
            'GP', 
            'GGA',
            (timestamp, 
            str(SIM_LAT), 'N', 
            str(SIM_LON), 'W', 
            '1', # Fix Quality (1 = GPS fix)
            str(SIM_SAT_COUNT), 
            '1.0', # HDOP
            '100.0', 'M', # Altitude
            '0.0', 'M', # Geoid Separation
            '', '') # DGPS fields
        )
        
        # Convert the message object back to the standard NMEA string with checksum
        nmea_string = str(msg)
        
        # 4. Yield the simulated string, just like the serial port would
        yield nmea_string
        
        # 5. Wait for a short time to simulate the GPS module's update rate
        time.sleep(0.5)

# --- Class to emulate the serial connection for the main app ---
class MockSerialPort:
    """A class that mimics the pyserial object but uses the generator."""
    def __init__(self):
        self.generator = generate_simulated_nmea()
        
    def readline(self):
        # The main app will call readline(), so we return the next NMEA string
        # We need to simulate the byte object that pyserial returns
        nmea_string = next(self.generator) + '\r\n'
        return nmea_string.encode('utf-8')
        
    # Add dummy methods so the main app doesn't crash when calling .close()
    def close(self):
        pass
    def is_open(self):
        return True

# --- Main function to be used by the Kivy App ---
def get_gps_data_source(use_mock=True):
    """Returns the actual serial port or the mock port based on the environment."""
    if use_mock:
        MOTONAV_LOGGER.info("Using Mock GPS Data Source")
        return MockSerialPort()
    else:
        # This is the code that will run on the Raspberry Pi:
        import serial
        try:
            # Assuming /dev/ttyS0 is the correct port on the RPi
            ser = serial.Serial('/dev/ttyS0', 9600, timeout=1) 
            MOTONAV_LOGGER.info("Connected to hardware serial port: /dev/ttyS0")
            return ser
        except serial.SerialException as e:
            MOTONAV_LOGGER.error(f"Error opening serial port on RPi: {e}")
            raise GPSCommunicationError(f"Failed to connect to GPS module: {e}")
            return None

if __name__ == '__main__':
    # Simple test to see the simulated stream
    MOTONAV_LOGGER.info("--- Starting GPS Simulation Test ---")
    mock_port = get_gps_data_source(use_mock=True)
    for i in range(10):
        raw_data = mock_port.readline()
        MOTONAV_LOGGER.debug(f"Simulated NMEA: {raw_data.decode().strip()}")