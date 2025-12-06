import logging
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = datetime.now().strftime("motonav_%Y%m%d_%H%M%S.log")

def setup_logger(log_level=logging.DEBUG):
    """
    Sets up a logger that outputs to console and a date-stamped file.
    """
    # 1. Ensure the log directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # 2. Get the root logger instance
    logger = logging.getLogger('MotoNav')
    logger.setLevel(log_level)
    
    # Prevents log messages from being sent to the root logger's handlers 
    # (prevents duplicate output if another library is logging)
    logger.propagate = False 

    # 3. Define the formatting
    # Format: Timestamp | Level | Module:LineNumber | Message
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 4. File Handler: Writes all messages (DEBUG level and higher) to a file
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, LOG_FILE))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # 5. Console Handler: Writes messages (INFO level and higher) to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # 6. Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log a startup message
    logger.info("--- MotoNav Logger Initialized ---")
    logger.info(f"Log file created: {os.path.join(LOG_DIR, LOG_FILE)}")
    
    return logger

# Create the main logger instance when imported
MOTONAV_LOGGER = setup_logger()

# Example usage (run this file directly to test logging)
if __name__ == '__main__':
    log = setup_logger(logging.DEBUG)
    log.debug("This is a DEBUG message (only in file, not default console)")
    log.info("This is an INFO message (in file and console)")
    log.warning("Warning: Loose breadboard connection suspected!")
    try:
        raise ValueError("Invalid GPX data structure")
    except ValueError as e:
        log.error(f"Critical error during parsing: {e}")
        log.exception("Full traceback logged for debugging:")