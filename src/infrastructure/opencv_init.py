"""
OpenCV initialization module
Handles OpenCV initialization and version compatibility
"""

import cv2
import warnings

def init_opencv():
    """
    Initialize OpenCV with optimal settings
    Handles version compatibility issues
    """
    # Check OpenCV version
    opencv_version = cv2.__version__
    major_version = int(opencv_version.split('.')[0])
    
    # Configure OpenCV for optimal performance
    cv2.setUseOptimized(True)
    cv2.setNumThreads(-1)  # Use all available cores
    
    # Handle deprecated functions based on version
    if major_version < 4:
        # For OpenCV 3.x, setBufferAreaMaxSize might exist
        if hasattr(cv2, 'setBufferAreaMaxSize'):
            try:
                cv2.setBufferAreaMaxSize(1024 * 1024 * 100)  # 100MB buffer
            except Exception as e:
                warnings.warn(f"Failed to set buffer area max size: {e}")
    else:
        # For OpenCV 4.x and later, this function is deprecated
        # Buffer sizes are managed automatically
        pass
    
    return opencv_version

# Initialize OpenCV when this module is imported
_opencv_version = None

def get_opencv_version():
    """Get initialized OpenCV version"""
    global _opencv_version
    if _opencv_version is None:
        _opencv_version = init_opencv()
    return _opencv_version