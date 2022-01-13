"""Logging utility"""

# External import
import logging
logger = logging.getLogger("netcontrol")

def init_logger():
    """Initialize the general logger."""
    # Configure the logger

    # Creates a handler for proper formatting
    # it takes any message that arrives to the main Astatine logger
    # and formats them
    # FIXME this is all hardcoded
    globalfilehandler = logging.FileHandler("/tmp/netcontrol.log")
    globalstreamhandler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s][%(name)-10s][%(levelname)-8s]"
        +"(%(filename)s::%(funcName)s::%(lineno)s) %(message)s")
    globalstreamhandler.setFormatter(formatter)
    globalfilehandler.setFormatter(formatter)
    logger.addHandler(globalfilehandler)
    logger.addHandler(globalstreamhandler)

    logger.debug("Initialized logger")
