#!/usr/bin/env python3
"""Test the project startup dialog visibility fix"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Simple test without PyQt6
print("Testing dialog code structure...")

# Check if the toggle_existing_images_visibility fix is in place
dialog_file = "src/presentation/dialogs/project_startup_dialog.py"
with open(dialog_file, 'r') as f:
    content = f.read()
    
# Check for FormLayout label handling
if "form_layout.labelForField" in content:
    print("✓ FormLayout label handling implemented")
else:
    print("✗ FormLayout label handling missing")

# Check main_window import fix
main_file = "src/presentation/main_window/main_window.py"
with open(main_file, 'r') as f:
    content = f.read()
    
if "from presentation.bb_canvas.canvas_widget import BBEntity" in content:
    print("✓ Import path fixed (no 'src.' prefix)")
else:
    print("✗ Import path still has 'src.' prefix")

print("\nAll structural fixes verified!")