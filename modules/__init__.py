# __init__.py (basic initialization)

import logging

# Configure the logger for the 'modules' package
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log a message indicating that the 'modules' package has been successfully loaded
logger.info("The 'modules' package has been successfully loaded.")

