#!/usr/bin/env python3
"""Test the two remaining issues"""

import os
import sys

print("Testing annotation loading and dialog visibility")
print("=" * 50)

# Test 1: Check if annotation_output_dir is set for image projects
print("\n1. Checking annotation_output_dir setup:")
main_file = "src/presentation/main_window/main_window.py"
with open(main_file, 'r') as f:
    content = f.read()
    
# Check image project initialization
if "self.annotation_output_dir = os.path.join(output_dir, 'annotations')" in content:
    print("✓ annotation_output_dir set for video projects")
else:
    print("✗ annotation_output_dir not set for video projects")

# Check if annotation_output_dir is set in image project init
image_init_start = content.find("def initialize_image_project(self):")
image_init_end = content.find("def initialize_existing_project(self):")
image_init_section = content[image_init_start:image_init_end]

if "self.annotation_output_dir =" in image_init_section:
    print("✓ annotation_output_dir set for image projects")
else:
    print("✗ annotation_output_dir not set for image projects")

# Test 2: Check dialog structure
print("\n2. Checking dialog visibility implementation:")
dialog_file = "src/presentation/dialogs/project_startup_dialog.py"
with open(dialog_file, 'r') as f:
    content = f.read()
    
if "self.existing_images_container = QWidget()" in content:
    print("✓ Using QWidget container for image directory")
else:
    print("✗ Not using QWidget container")

if "self.existing_images_label = QLabel" in content:
    print("✓ Using QLabel for label")
else:
    print("✗ Not using QLabel")

if "self.existing_images_container.setVisible(visible)" in content:
    print("✓ Container visibility control implemented")
else:
    print("✗ Container visibility control missing")

# Test 3: Check debug output
print("\n3. Debug statements added:")
if 'print(f"Loading annotations for frame {self.current_frame}")' in open(main_file).read():
    print("✓ Debug for frame loading added")
else:
    print("✗ Debug for frame loading missing")

if 'print(f"toggle_existing_images_visibility: visible = {visible}")' in open(dialog_file).read():
    print("✓ Debug for visibility toggle added")
else:
    print("✗ Debug for visibility toggle missing")

print("\n" + "=" * 50)
print("Please run the application and check the console output to debug the issues.")
print("\nFor issue 2 (A/D frame switching):")
print("- Check if 'No annotation_output_dir set' appears")
print("- Check what annotation file path it's looking for")
print("\nFor issue 3 (existing annotation dialog):")
print("- Check if 'toggle_existing_images_visibility' is called with visible=True")
print("- Check if the container actually becomes visible")