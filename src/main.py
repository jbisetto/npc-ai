#!/usr/bin/env python
"""
NPC AI - Application Entry Point
"""

import os
import sys
import logging
import logging.config

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Define log file path in src directory
log_file_path = os.path.join(current_dir, "npc_ai.log")

# Configure logging
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "detailed",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": log_file_path,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "src": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}

# Apply the logging configuration
logging.config.dictConfig(logging_config)

def main():
    """
    Main entry point for the NPC AI application
    """
    logging.info("Starting NPC AI application")
    # Add your application initialization code here

if __name__ == "__main__":
    main()
