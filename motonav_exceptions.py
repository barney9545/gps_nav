# --- motonav_exceptions.py ---

class MotoNavError(Exception):
    """Base class for all custom MotoNav errors."""
    def __init__(self, message="An unexpected MotoNav error occurred."):
        super().__init__(message)

class ConfigurationError(MotoNavError):
    """Raised when critical configuration files (like GPX or MBTiles) are missing or invalid."""
    pass

class GPSCommunicationError(MotoNavError):
    """Raised when the serial port fails to open or consistently returns bad data."""
    pass

class RouteCalculationError(MotoNavError):
    """Raised when the offline routing engine fails to find a valid path or a turn."""
    pass

# Example of using the custom logger with an exception
if __name__ == '__main__':
    from motonav_logger import MOTONAV_LOGGER as log
    
    try:
        # Simulate an error condition
        raise ConfigurationError("MBTiles file not found at the expected path.")
    except ConfigurationError as e:
        log.critical(f"FATAL SETUP ERROR: {e}")
        # In a real app, you would stop the program here or revert to a safe mode.