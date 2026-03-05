"""Logging configuration and management."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class LogManager:
    """Manage logging configuration with file and console outputs."""
    
    _initialized = False
    
    @staticmethod
    def setup_logging(
        log_level: str = "INFO",
        output_dir: Optional[str] = None,
        log_to_file: bool = True,
        log_to_console: bool = True,
        console_level: Optional[str] = None,
        log_filename: Optional[str] = None
    ) -> None:
        """Setup logging with file and console handlers.
        
        Args:
            log_level: Default logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            output_dir: Directory to save log files
            log_to_file: Whether to log to file
            log_to_console: Whether to log to console
            console_level: Console logging level (if different from log_level)
            log_filename: Custom log filename (default: augmentation_YYYYMMDD_HHMMSS.log)
        """
        if LogManager._initialized:
            return
        
        # Get root logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)  # Capture all levels, filter in handlers
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create formatter
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        # File handler
        if log_to_file and output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            if log_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_filename = f"augmentation_{timestamp}.log"
            
            log_file = output_path / log_filename
            file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
            
            print(f"📄 Logging to file: {log_file}")
        
        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_log_level = console_level if console_level else log_level
            console_handler.setLevel(getattr(logging, console_log_level.upper()))
            console_handler.setFormatter(simple_formatter)
            logger.addHandler(console_handler)
        
        LogManager._initialized = True
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger instance.
        
        Args:
            name: Logger name (usually __name__)
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
    
    @staticmethod
    def reset():
        """Reset logging initialization state (mainly for testing)."""
        LogManager._initialized = False


def setup_logging_from_config(config: dict, output_dir: str) -> None:
    """Setup logging based on configuration.
    
    Args:
        config: Configuration dictionary
        output_dir: Output directory for log files
    """
    general = config.get('general', {})
    logging_config = config.get('logging', {})
    
    # Get settings with defaults
    log_level = general.get('log_level', 'INFO')
    log_to_file = logging_config.get('log_to_file', True)
    log_to_console = logging_config.get('log_to_console', True)
    console_level = logging_config.get('console_level', 'WARNING')  # Less verbose on console
    log_filename = logging_config.get('log_filename', None)
    
    LogManager.setup_logging(
        log_level=log_level,
        output_dir=output_dir,
        log_to_file=log_to_file,
        log_to_console=log_to_console,
        console_level=console_level,
        log_filename=log_filename
    )
