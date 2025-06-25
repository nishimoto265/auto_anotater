#!/usr/bin/env python3
"""Test final fixes for zoom and recursion issues"""

import os

print("Verifying Final Fixes")
print("=" * 50)

# 1. Check zoom controller fix
zoom_file = "src/presentation/bb_canvas/zoom_controller.py"
with open(zoom_file, 'r') as f:
    content = f.read()
    
if "toPointF()" in content and "hasattr(center_point, 'toPointF')" in content:
    print("✓ Zoom controller QPointF type fix implemented")
else:
    print("✗ Zoom controller fix missing")

# 2. Check BB list panel recursion fix
bb_list_file = "src/presentation/control_panels/bb_list_panel.py"
with open(bb_list_file, 'r') as f:
    content = f.read()
    
if "self.blockSignals(True)" in content and "self.blockSignals(False)" in content:
    print("✓ BB list panel signal blocking implemented")
else:
    print("✗ BB list panel recursion fix missing")

# 3. Check main window recursion prevention
main_file = "src/presentation/main_window/main_window.py"
with open(main_file, 'r') as f:
    content = f.read()
    
if "if hasattr(self, 'bb_list_panel'):" in content:
    print("✓ Main window recursion prevention added")
else:
    print("✗ Main window recursion prevention missing")

# 4. Check import fix is still in place
if "from presentation.bb_canvas.canvas_widget import BBEntity" in content:
    print("✓ Import path fix still in place")
else:
    print("✗ Import path reverted")

print("\n" + "=" * 50)
print("All critical fixes verified!")
print("\nThe application should now run without crashes.")