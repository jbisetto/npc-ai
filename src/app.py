"""
Basic application configuration
"""

import logging

# Configure logging with proper Unicode handling
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),  # Console handler
        logging.FileHandler('npc_ai.log', encoding='utf-8')  # File handler with UTF-8 encoding
    ]
) 