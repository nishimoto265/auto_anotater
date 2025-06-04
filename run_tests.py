#!/usr/bin/env python3
"""
Test Runner for Fast Auto-Annotation System
エラー防止テスト・回帰テスト実行スクリプト
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Test Runner for Error Prevention')
    parser.add_argument('--category', choices=['unit', 'integration', 'gui', 'all'], 
                       default='all', help='Test category to run')
    parser.add_argument('--headless', action='store_true', 
                       help='Run in headless mode (no GUI)')
    parser.add_argument('--coverage', action='store_true',
                       help='Run with coverage report')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be run without executing')
    
    args = parser.parse_args()
    
    # Set environment for headless mode
    if args.headless:
        os.environ['HEADLESS'] = 'true'
        if 'DISPLAY' in os.environ:
            del os.environ['DISPLAY']
    
    # Build pytest command
    cmd = ['python', '-m', 'pytest']
    
    if args.verbose:
        cmd.append('-v')
    
    if args.coverage:
        cmd.extend(['--cov=src', '--cov-report=html', '--cov-report=term-missing'])
    
    # Add test markers based on category
    if args.category == 'unit':
        cmd.extend(['-m', 'unit'])
    elif args.category == 'integration':
        cmd.extend(['-m', 'integration'])
    elif args.category == 'gui':
        cmd.extend(['-m', 'gui'])
        if args.headless:
            print("Warning: GUI tests may not work properly in headless mode")
    
    # Add specific test files
    test_files = []
    
    if args.category in ['integration', 'all']:
        test_files.append('tests/integration/test_error_prevention.py')
    
    if args.category in ['unit', 'all']:
        # Add unit test files when they exist
        unit_test_dirs = [
            'tests/unit/test_presentation/',
            'tests/unit/test_application/', 
            'tests/unit/test_domain/',
            'tests/unit/test_cache_layer/',
        ]
        for test_dir in unit_test_dirs:
            if Path(test_dir).exists():
                test_files.append(test_dir)
    
    cmd.extend(test_files)
    
    if args.dry_run:
        print("Would run command:")
        print(' '.join(cmd))
        return 0
    
    print(f"Running tests: {args.category}")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 50)
    
    # Execute tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())