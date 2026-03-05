"""Unit tests for checkpoint management."""

import pytest

from labelme_augmentor.utils import CheckpointManager


class TestCheckpointManager:
    """Test CheckpointManager class."""
    
    def test_init_new_checkpoint(self, temp_dir):
        """Test initializing new checkpoint."""
        checkpoint_file = temp_dir / "checkpoint.json"
        manager = CheckpointManager(str(checkpoint_file))
        
        assert len(manager.processed_files) == 0
        assert not checkpoint_file.exists()
    
    def test_mark_and_save(self, temp_dir):
        """Test marking files as processed and saving."""
        checkpoint_file = temp_dir / "checkpoint.json"
        manager = CheckpointManager(str(checkpoint_file))
        
        # Mark files
        manager.mark_processed("file1.json")
        manager.mark_processed("file2.json")
        
        # Save checkpoint
        manager.save_checkpoint()
        
        assert checkpoint_file.exists()
        assert len(manager.processed_files) == 2
    
    def test_load_existing_checkpoint(self, temp_dir):
        """Test loading existing checkpoint."""
        checkpoint_file = temp_dir / "checkpoint.json"
        
        # Create and save checkpoint
        manager1 = CheckpointManager(str(checkpoint_file))
        manager1.mark_processed("file1.json")
        manager1.mark_processed("file2.json")
        manager1.save_checkpoint()
        
        # Load in new instance
        manager2 = CheckpointManager(str(checkpoint_file))
        assert len(manager2.processed_files) == 2
        assert manager2.is_processed("file1.json")
        assert manager2.is_processed("file2.json")
    
    def test_is_processed(self, temp_dir):
        """Test checking if file is processed."""
        checkpoint_file = temp_dir / "checkpoint.json"
        manager = CheckpointManager(str(checkpoint_file))
        
        manager.mark_processed("file1.json")
        
        assert manager.is_processed("file1.json")
        assert not manager.is_processed("file2.json")
    
    def test_clear(self, temp_dir):
        """Test clearing checkpoint."""
        checkpoint_file = temp_dir / "checkpoint.json"
        manager = CheckpointManager(str(checkpoint_file))
        
        manager.mark_processed("file1.json")
        manager.save_checkpoint()
        assert checkpoint_file.exists()
        
        # Clear
        manager.clear()
        assert not checkpoint_file.exists()
        assert len(manager.processed_files) == 0
