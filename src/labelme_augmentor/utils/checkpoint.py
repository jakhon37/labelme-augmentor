"""Checkpoint management for resume functionality."""

import json
import logging
import os
from typing import Set

from .exceptions import CheckpointError


class CheckpointManager:
    """Manage checkpoint for resume functionality."""

    def __init__(self, checkpoint_file: str) -> None:
        """Initialize checkpoint manager.
        
        Args:
            checkpoint_file: Path to checkpoint file
        """
        self.checkpoint_file = checkpoint_file
        self.processed_files: Set[str] = set()
        self.load_checkpoint()

    def load_checkpoint(self) -> None:
        """Load checkpoint if exists."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    self.processed_files = set(data.get('processed_files', []))
                logging.info(
                    f"Loaded checkpoint: {len(self.processed_files)} files already processed"
                )
            except Exception as e:
                logging.warning(f"Failed to load checkpoint: {e}")
                self.processed_files = set()

    def save_checkpoint(self) -> None:
        """Save current checkpoint."""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump({'processed_files': list(self.processed_files)}, f, indent=2)
        except Exception as e:
            raise CheckpointError(f"Failed to save checkpoint: {e}")

    def mark_processed(self, file_path: str) -> None:
        """Mark file as processed.
        
        Args:
            file_path: Path to mark as processed
        """
        self.processed_files.add(file_path)

    def is_processed(self, file_path: str) -> bool:
        """Check if file was already processed.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file was processed, False otherwise
        """
        return file_path in self.processed_files

    def clear(self) -> None:
        """Clear checkpoint file."""
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
        self.processed_files = set()
