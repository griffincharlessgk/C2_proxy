#!/usr/bin/env python3
"""
Test runner for C2 system.
"""

import unittest
import sys
import os
import argparse

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_unit_tests():
    """Run unit tests."""
    print("🧪 Running Unit Tests...")
    loader = unittest.TestLoader()
    suite = loader.discover('tests/unit', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_integration_tests():
    """Run integration tests."""
    print("🔗 Running Integration Tests...")
    loader = unittest.TestLoader()
    suite = loader.discover('tests/integration', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_e2e_tests():
    """Run end-to-end tests."""
    print("🌐 Running End-to-End Tests...")
    loader = unittest.TestLoader()
    suite = loader.discover('tests/e2e', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_all_tests():
    """Run all tests."""
    print("🚀 Running All Tests...")
    
    success = True
    
    # Unit tests
    if not run_unit_tests():
        success = False
    
    # Integration tests
    if not run_integration_tests():
        success = False
    
    # E2E tests
    if not run_e2e_tests():
        success = False
    
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return success

def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="C2 System Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true", help="Run e2e tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    if args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.e2e:
        success = run_e2e_tests()
    elif args.all:
        success = run_all_tests()
    else:
        # Default: run all tests
        success = run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
