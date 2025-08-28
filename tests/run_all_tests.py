#!/usr/bin/env python3
"""
Test runner cho toàn bộ C2 system
Chạy tất cả test cases và generate report
"""

import unittest
import sys
import os
import time
from io import StringIO

def run_all_tests():
    """Chạy tất cả test cases"""
    print("🧪 Bắt đầu chạy test suite cho C2 Hybrid Botnet Management System")
    print("=" * 80)
    
    # Discover and load all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Create test runner với detailed output
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        descriptions=True,
        failfast=False
    )
    
    # Run tests
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print results
    output = stream.getvalue()
    print(output)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 KẾT QUẢ TEST SUMMARY")
    print("=" * 80)
    print(f"⏱️  Thời gian chạy: {end_time - start_time:.2f} giây")
    print(f"🧪 Tổng số tests: {result.testsRun}")
    print(f"✅ Thành công: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Thất bại: {len(result.failures)}")
    print(f"🔥 Lỗi: {len(result.errors)}")
    print(f"⏭️  Bỏ qua: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    # Detailed failure/error reports
    if result.failures:
        print("\n❌ CHI TIẾT FAILURES:")
        for test, traceback in result.failures:
            print(f"\n🔸 {test}:")
            print(traceback)
    
    if result.errors:
        print("\n🔥 CHI TIẾT ERRORS:")
        for test, traceback in result.errors:
            print(f"\n🔸 {test}:")
            print(traceback)
    
    # Return success status
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 TẤT CẢ TESTS ĐÃ PASS! System sẵn sàng để deploy.")
    else:
        print("⚠️  CÓ TESTS FAILED! Cần fix trước khi deploy.")
    print("=" * 80)
    
    return success

def check_dependencies():
    """Kiểm tra dependencies cần thiết cho testing"""
    print("🔍 Kiểm tra dependencies...")
    
    required_modules = [
        'unittest',
        'tempfile',
        'hashlib',
        'json'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Thiếu modules: {', '.join(missing)}")
        return False
    
    print("✅ Tất cả dependencies đã có sẵn\n")
    return True

def main():
    """Main function"""
    print("🚀 C2 HYBRID BOTNET MANAGEMENT SYSTEM - TEST SUITE")
    print("📝 Educational/Research purposes only")
    print("⚠️  Use responsibly and with explicit permission only!")
    print("")
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Không thể chạy tests do thiếu dependencies")
        sys.exit(1)
    
    # Run tests
    success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
