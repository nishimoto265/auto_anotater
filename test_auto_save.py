#!/usr/bin/env python3
"""
Test script for auto-save functionality
"""
import os
import time
import tempfile
from pathlib import Path
from core.annotation_manager import AnnotationManager, BoundingBox, SaveStatus

def test_auto_save():
    print("Testing auto-save functionality...")
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test annotation files
        frame_dir = Path(tmpdir) / "frames"
        frame_dir.mkdir()
        
        # Create a dummy annotation file
        test_file = frame_dir / "000001.txt"
        test_file.write_text("0 0.5 0.5 0.1 0.1 1 0.95\n")
        
        # Initialize annotation manager
        config_path = "config/app_config.json"
        if not os.path.exists(config_path):
            print(f"Config file not found at {config_path}")
            return
            
        manager = AnnotationManager(config_path)
        
        # Set up callbacks
        save_statuses = []
        def on_status_change(status):
            save_statuses.append(status)
            print(f"Save status changed: {status.value}")
        
        def on_error(msg):
            print(f"Save error: {msg}")
        
        manager.set_save_status_callback(on_status_change)
        manager.set_save_error_callback(on_error)
        
        # Load annotations
        manager.load_annotations(str(frame_dir))
        print(f"Loaded annotations from {frame_dir}")
        
        # Add a new bbox to trigger modified flag
        new_bbox = BoundingBox(
            individual_id=1,
            x=0.3,
            y=0.3,
            w=0.15,
            h=0.15,
            action_id=2,
            confidence=0.88
        )
        manager.add_bbox(1, new_bbox)
        print("Added new bounding box")
        
        # Wait for auto-save (should happen after 30 seconds by default)
        print(f"Waiting for auto-save (interval: {manager.auto_save_interval}s)...")
        
        # For testing, reduce interval
        manager.set_auto_save_interval(3)
        print("Set auto-save interval to 3 seconds for testing")
        
        # Wait and check status
        time.sleep(5)
        
        # Force save to test immediate save
        print("Testing force save...")
        manager.force_save()
        
        # Wait for save to complete
        time.sleep(1)
        
        # Check if file was saved
        if test_file.exists():
            content = test_file.read_text()
            print(f"Saved file content:\n{content}")
        
        # Check save statuses
        print(f"\nSave status history: {[s.value for s in save_statuses]}")
        
        # Stop auto-save
        manager.stop_auto_save()
        print("Auto-save stopped")
        
        print("\nTest completed successfully!")

if __name__ == "__main__":
    test_auto_save()