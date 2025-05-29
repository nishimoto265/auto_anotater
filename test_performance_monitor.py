#!/usr/bin/env python3
"""Test script for performance monitor functionality"""

import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from utils.performance_monitor import PerformanceMonitor
    print("✓ Successfully imported PerformanceMonitor")
    
    # Create instance
    pm = PerformanceMonitor()
    print("✓ Successfully created PerformanceMonitor instance")
    
    # Start monitoring
    pm.start_monitoring()
    print("✓ Successfully started monitoring")
    
    # Test frame switching
    pm.start_frame_switch(0)
    time.sleep(0.1)  # Simulate frame switch delay
    pm.end_frame_switch(1)
    print("✓ Successfully recorded frame switch")
    
    # Get metrics
    metrics = pm.get_current_metrics()
    if metrics:
        print(f"✓ Current metrics: Memory={metrics.process_memory_mb:.1f}MB, CPU={metrics.cpu_percent:.1f}%")
    
    # Get summary
    summary = pm.get_metrics_summary(60)
    print(f"✓ Got metrics summary with {summary.get('sample_count', 0)} samples")
    
    # Test export
    pm.export_performance_report("test_report.json")
    print("✓ Successfully exported performance report")
    
    # Stop monitoring
    pm.stop_monitoring()
    print("✓ Successfully stopped monitoring")
    
    print("\n✅ All tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure to install required packages: pip install psutil gputil")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()