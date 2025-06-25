#!/usr/bin/env python3
"""Test dialog visibility for existing annotations"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PyQt6.QtWidgets import QApplication
from presentation.dialogs.project_startup_dialog import ProjectStartupDialog

app = QApplication(sys.argv)

# Create dialog
dialog = ProjectStartupDialog()

# Test existing annotation selection
print("Testing existing annotation visibility...")
print("1. Initial state (video selected):")
print(f"   - existing_images_container visible: {dialog.existing_images_container.isVisible()}")
print(f"   - existing_images_label visible: {dialog.existing_images_label.isVisible()}")

# Select existing annotation
dialog.existing_radio.setChecked(True)
print("\n2. After selecting existing annotation:")
print(f"   - existing_radio checked: {dialog.existing_radio.isChecked()}")
print(f"   - existing_images_container visible: {dialog.existing_images_container.isVisible()}")
print(f"   - existing_images_label visible: {dialog.existing_images_label.isVisible()}")

# Show dialog
dialog.show()

# Print dialog structure
print("\n3. Dialog structure:")
print(f"   - existing_images_edit exists: {hasattr(dialog, 'existing_images_edit')}")
print(f"   - existing_images_browse_btn exists: {hasattr(dialog, 'existing_images_browse_btn')}")
print(f"   - existing_images_container parent: {dialog.existing_images_container.parent()}")

sys.exit(app.exec())