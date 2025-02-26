import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
# Create a logger instance
LOGGER = logging.getLogger("Topology_Generator")
LOGGER.setLevel(logging.DEBUG)


