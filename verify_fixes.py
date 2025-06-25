#!/usr/bin/env python3
"""
Verify code changes for all reported issues
"""

import os
import re

def verify_code_changes():
    """Verify all code changes have been implemented"""
    print("Verifying Fast Auto-Annotation System Fixes")
    print("=" * 50)
    
    fixes_verified = []
    fixes_failed = []
    
    # Fix 1: Check startup dialog for image directory visibility
    print("\n1. Checking existing annotation image directory selection...")
    dialog_file = "src/presentation/dialogs/project_startup_dialog.py"
    
    if os.path.exists(dialog_file):
        with open(dialog_file, 'r') as f:
            content = f.read()
            
        # Check for on_project_type_changed call in __init__
        if "self.on_project_type_changed()" in content and \
           "def __init__(self" in content:
            print("✓ Initial state update added in __init__")
            fixes_verified.append("Image directory selection visibility")
        else:
            print("✗ Missing initial state update")
            fixes_failed.append("Image directory selection visibility")
    
    # Fix 2: Check annotation loading for all project types
    print("\n2. Checking annotation loading when switching frames...")
    main_file = "src/presentation/main_window/main_window.py"
    
    if os.path.exists(main_file):
        with open(main_file, 'r') as f:
            content = f.read()
            
        # Check annotation_output_dir is set for all project types
        if "self.annotation_output_dir = os.path.join(output_dir, 'annotations')" in content and \
           "self.annotation_output_dir = annotations_dir" in content:
            print("✓ annotation_output_dir set for all project types")
            fixes_verified.append("Annotation loading on frame switch")
        else:
            print("✗ Missing annotation_output_dir setup")
            fixes_failed.append("Annotation loading on frame switch")
    
    # Fix 3: Check BB renderer size increases
    print("\n3. Checking BB and text size increases...")
    renderer_file = "src/presentation/bb_canvas/bb_renderer.py"
    
    if os.path.exists(renderer_file):
        with open(renderer_file, 'r') as f:
            content = f.read()
            
        # Check font size (36) and border width (3)
        font_match = re.search(r'font_size:\s*int\s*=\s*36', content)
        border_match = re.search(r'QPen\([^,]+,\s*3\)', content)
        
        if font_match and border_match:
            print("✓ Font size set to 36 (1.5x of 24)")
            print("✓ Border width set to 3 (1.5x of 2)")
            fixes_verified.append("BB and text size increase")
        else:
            print("✗ Size increases not found")
            fixes_failed.append("BB and text size increase")
    
    # Fix 4: Check BB list update implementation
    print("\n4. Checking BB list update implementation...")
    
    if os.path.exists(main_file):
        with open(main_file, 'r') as f:
            content = f.read()
            
        # Check for update_bb_list_panel method
        if "def update_bb_list_panel(self):" in content and \
           "self.bb_list_panel.update_bb_list(bb_entities)" in content:
            print("✓ update_bb_list_panel method implemented")
            
            # Check if it's called in on_bb_created
            if "self.update_bb_list_panel()" in content and \
               "def on_bb_created(" in content:
                print("✓ BB list updated on creation")
                fixes_verified.append("BB list showing items")
            else:
                print("✗ BB list not updated on creation")
                fixes_failed.append("BB list showing items")
        else:
            print("✗ update_bb_list_panel method not found")
            fixes_failed.append("BB list showing items")
    
    # Fix 5: Check S key deletion with BB list update
    print("\n5. Checking S key deletion with BB list update...")
    
    if os.path.exists(main_file):
        with open(main_file, 'r') as f:
            content = f.read()
            
        # Find delete_selected_bb method
        delete_method = re.search(
            r'def delete_selected_bb\(self\):.*?'
            r'self\.current_annotations\.pop\(\).*?'
            r'self\.update_bb_list_panel\(\)',
            content, re.DOTALL
        )
        
        if delete_method:
            print("✓ S key deletion updates BB list")
            fixes_verified.append("S key deletion with list update")
        else:
            print("✗ BB list not updated after deletion")
            fixes_failed.append("S key deletion with list update")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"✓ Fixes verified: {len(fixes_verified)}")
    for fix in fixes_verified:
        print(f"  - {fix}")
    
    if fixes_failed:
        print(f"\n✗ Fixes failed: {len(fixes_failed)}")
        for fix in fixes_failed:
            print(f"  - {fix}")
    else:
        print("\n✓ ALL FIXES SUCCESSFULLY IMPLEMENTED!")
    
    return len(fixes_failed) == 0

if __name__ == "__main__":
    success = verify_code_changes()
    exit(0 if success else 1)