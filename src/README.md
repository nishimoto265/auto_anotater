pip install -r requirements.txt

python main.py --video path/to/video.mp4

python main.py --frames path/to/frames

python main.py --resume path/to/project

UI Layer
 ├── MainWindow
 ├── FrameViewer
 ├── IDPanel
 └── NavigationPanel

Core Layer
 ├── AnnotationManager
 ├── VideoProcessor
 ├── ImageCache
 └── TrackingSystem

Utils Layer
 ├── CoordinateConverter
 ├── ColorManager
 └── FileManager

<object-id> <x> <y> <width> <height> <action-id> <confidence>

0 0.716797 0.395833 0.216406 0.202778 1 0.98
1 0.287109 0.600694 0.158594 0.184722 2 0.95

{
  "individual_ids": [0-15],
  "action_ids": ["sit", "stand", "milk", "water", "food"],
  "colors": {"0": "#FF0000", ...},
  "performance": {
    "cache_size_gb": 20,
    "preload_frames": 100
  }
};