import logging
import os
from logging.handlers import RotatingFileHandler

# Define a custom formatter
class AnsiColorFormatter(logging.Formatter):
    """
    A logging formatter that adds ANSI escape codes for colors.
    Errors and critical messages will be in bold red.
    """
    # ANSI escape codes
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    def format(self, record):
        # Original formatted message
        message = super().format(record)

        # Add color for ERROR and CRITICAL levels
        if record.levelno >= logging.ERROR:
            # Wrap the entire log message in red and bold
            return f"{self.BOLD}{self.RED}{message.upper()}{self.RESET}"
        return message

def setup_logging():
    """
    Sets up the logging configuration for the application.
    """
    log_dir = "LOG"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file_path = os.path.join(log_dir, "app.log")

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Create a rotating file handler
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.INFO)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatters
    # File formatter with color
    file_formatter = AnsiColorFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Console formatter without color codes
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Set formatters for handlers
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Add handlers to the root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("Logging configured successfully.")

# You can also set up a specific logger for the app if you don't want to configure the root
def get_logger(name):
    """
    Utility function to get a logger.
    It's better to call setup_logging() once at the app's entry point.
    """
    return logging.getLogger(name)
