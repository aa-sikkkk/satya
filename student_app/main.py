"""
Main entry point for the Satya learning system CLI application.

This module provides the command-line interface for students to interact with
the Satya learning system.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

from student_app.interface.cli_interface import CLIInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('satya.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Satya Learning System - Grade 10 AI Learning Companion"
    )
    
    parser.add_argument(
        "--content-dir",
        type=str,
        default="data/content",
        help="Path to content directory (default: data/content)"
    )
    
    parser.add_argument(
        "--model-path",
        type=str,
        default="models/albert",
        help="Path to model directory (default: models/albert)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the CLI application."""
    # Parse command line arguments
    args = parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    try:
        # Ensure content directory exists
        content_dir = Path(args.content_dir)
        if not content_dir.exists():
            logger.error(f"Content directory not found: {content_dir}")
            sys.exit(1)
            
        # Ensure model directory exists
        model_path = Path(args.model_path)
        if not model_path.exists():
            logger.error(f"Model directory not found: {model_path}")
            sys.exit(1)
            
        # Initialize and start CLI interface
        logger.info("Starting Satya Learning System...")
        cli = CLIInterface(str(content_dir), str(model_path))
        cli.start()
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 