#!/bin/bash
# Run the annotation application with proper environment setup

# Activate virtual environment
source venv/bin/activate

# Set OpenCV environment variables to prevent deprecated function warnings
export OPENCV_VIDEOIO_PRIORITY_GSTREAMER=0
export OPENCV_LOG_LEVEL=ERROR

# Ensure we're using the correct Python path
export PYTHONPATH=$PWD/src:$PYTHONPATH

# Run the application
echo "Starting Fast Auto-Annotation System..."
python src/main.py "$@"