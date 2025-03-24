import logging

def setup_logger():
    logger = logging.getLogger('zencontrol')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# Call this setup when you initialize the project to set up logging
logger = setup_logger()
