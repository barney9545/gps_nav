import time
import pynmea2
from motonav_logger import MOTONAV_LOGGER
from motonav_exceptions import GPSCommunicationError

# Define a simulated starting location (use coordinates near your test_route.gpx center)
SIM_LAT = 21.121556
SIM_LON = 79.056389
SIM_SAT_COUNT = 8

def to_ddm_format(dd):
    """Converts Decimal Degrees (DD) to NMEA Degrees Decimal Minutes (DDM) format."""
    # Ensure latitude/longitude are positive for calculation
    abs_dd = abs(dd)
    
    # Extract Degrees (DDD or DD)
    degrees = int(abs_dd)
    
    # Calculate Minutes and Decimal Minutes (MM.MMMM)
    minutes = (abs_dd - degrees) * 60
    
    # Format as string: e.g., '4043.8000' for Lat or '07400.9000' for Lon
    # Longitude is often 3 digits for degrees
    if abs_dd >= 100:
        ddm_format = "{:03d}{:.4f}".format(degrees, minutes)
    else:
        ddm_format = "{:02d}{:.4f}".format(degrees, minutes)
        
    return ddm_format.replace('.', '') # NMEA standard often omits the decimal in DDM 
                                      # but pynmea2 sometimes expects it, let's keep it clean
                                      # and check the error again if it fails.
                                      # For now, let's include the decimal point for pynmea2's parsing logic.
    return "{:03d}{:.4f}".format(degrees, minutes)


def generate_simulated_nmea():
    """Generates a continuous stream of simulated NMEA GPGGA sentences."""
    global SIM_LAT, SIM_LON
    
    LAT_STEP = 0.00005
    LON_STEP = 0.00003
    
    while True:
        SIM_LAT += LAT_STEP 
        SIM_LON += LON_STEP
        
        now = time.time()
        timestamp = time.strftime("%H%M%S.00", time.gmtime(now))
        
        # --- CRITICAL CHANGE: Format to DDM ---
        lat_ddm = to_ddm_format(SIM_LAT)
        lon_ddm = to_ddm_format(SIM_LON)
        
        # Determine N/S and E/W indicators
        lat_dir = 'N' if SIM_LAT >= 0 else 'S'
        lon_dir = 'E' if SIM_LON >= 0 else 'W'
        
        # The fields are separated by commas
        fields = [
            'GGA',                      
            timestamp,                  
            lat_ddm, lat_dir,           # Latitude in DDM format
            lon_ddm, lon_dir,           # Longitude in DDM format
            '1',                        
            str(SIM_SAT_COUNT),         
            '1.0',                      
            '100.0', 'M',               
            '0.0', 'M',                 
            '', ''                      
        ]
        
        message_body = ",".join(fields)
        raw_nmea = f"$GP{message_body}"
        full_nmea_string = pynmea2.Sentence.checksum(raw_nmea) 
        
        yield full_nmea_string
        
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
        print(f"Simulated NMEA: {raw_data.decode().strip()}")