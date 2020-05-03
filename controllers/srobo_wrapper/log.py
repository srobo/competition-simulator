import logging

# Python 2.6's logging doesn't have NullHandler
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

# Default to sending our log messages nowhere
logger = logging.getLogger( "sr" )
logger.addHandler( NullHandler() )
