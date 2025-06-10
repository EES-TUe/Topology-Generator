import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"), 
        logging.StreamHandler()
    ]
)

# Create a logger instance
LOGGER = logging.getLogger("Topology-Logger")
