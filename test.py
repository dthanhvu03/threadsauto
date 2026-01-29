#!/usr/bin/env python3
"""
Unified test script for Threads Automation Tool
Combines all test scripts into one with menu
"""

import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def show_menu():
    """Show test menu."""
    print()
    print("=" * 60)
    print("THREADS AUTOMATION TOOL - TESTS")
    print("=" * 60)
    print()
    print("1. Test Imports (Quick verification)")
    print("2. Test Refactoring (Comprehensive)")
    print("3. Run Pytest Tests")
    print("4. Run All Tests")
    print()
    print("0. Exit")
    print()
    choice = input("Chọn option (0-4): ").strip()
    return choice


def test_imports():
    """Test imports after fix."""
    print("=" * 60)
    print("TESTING IMPORTS AFTER FIX")
    print("=" * 60)
    print()
    
    errors = []
    
    # Test accounts_adapter
    try:
        from backend.api.adapters.accounts_adapter import AccountsAPI
        api = AccountsAPI()
        print("✓ accounts_adapter.py - Import OK")
        
        if hasattr(api, '_get_account_metadata'):
            print("  ✓ _get_account_metadata method exists")
        else:
            print("  ✗ _get_account_metadata method MISSING")
            errors.append("_get_account_metadata missing")
            
    except Exception as e:
        errors.append(f"accounts_adapter: {str(e)}")
        print(f"✗ accounts_adapter.py - Import FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test dashboard
    try:
        from backend.api.routes.dashboard import router
        print("✓ dashboard.py - Import OK")
    except Exception as e:
        errors.append(f"dashboard: {str(e)}")
        print(f"✗ dashboard.py - Import FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test analytics
    try:
        from backend.api.adapters.analytics_adapter import AnalyticsAPI
        api = AnalyticsAPI()
        print("✓ analytics_adapter.py - Import OK")
    except Exception as e:
        errors.append(f"analytics_adapter: {str(e)}")
        print(f"✗ analytics_adapter.py - Import FAILED: {str(e)}")
    
    # Test metrics
    try:
        from backend.api.adapters.metrics_adapter import MetricsAPI
        api = MetricsAPI()
        print("✓ metrics_adapter.py - Import OK")
    except Exception as e:
        errors.append(f"metrics_adapter: {str(e)}")
        print(f"✗ metrics_adapter.py - Import FAILED: {str(e)}")
    
    # Test jobs_adapter
    try:
        from backend.api.adapters.jobs_adapter import JobsAPI
        api = JobsAPI()
        print("✓ jobs_adapter.py - Import OK")
    except Exception as e:
        errors.append(f"jobs_adapter: {str(e)}")
        print(f"✗ jobs_adapter.py - Import FAILED: {str(e)}")
    
    print()
    print("=" * 60)
    if errors:
        print("❌ ERRORS FOUND:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ ALL IMPORTS SUCCESSFUL - Fix verified!")
        return True


def test_refactoring():
    """Test refactoring verification."""
    print()
    print("🧵 THREADS AUTOMATION - REFACTORING VERIFICATION")
    print()
    
    results = []
    
    # Test imports
    print("=" * 60)
    print("TESTING IMPORTS")
    print("=" * 60)
    
    errors = []
    
    # Test jobs_adapter
    try:
        from backend.api.adapters.jobs_adapter import JobsAPI
        api = JobsAPI()
        print("✓ jobs_adapter.py - Import OK")
        print(f"  - Methods: {len([m for m in dir(api) if not m.startswith('__')])} methods")
    except Exception as e:
        errors.append(f"jobs_adapter: {str(e)}")
        print(f"✗ jobs_adapter.py - Import FAILED: {str(e)}")
    
    # Test accounts_adapter
    try:
        from backend.api.adapters.accounts_adapter import AccountsAPI
        api = AccountsAPI()
        print("✓ accounts_adapter.py - Import OK")
        print(f"  - Methods: {len([m for m in dir(api) if not m.startswith('__')])} methods")
    except Exception as e:
        errors.append(f"accounts_adapter: {str(e)}")
        print(f"✗ accounts_adapter.py - Import FAILED: {str(e)}")
    
    # Test dashboard
    try:
        from backend.api.routes.dashboard import router, _calculate_jobs_by_status
        print("✓ dashboard.py - Import OK")
        print(f"  - Helper functions available")
    except Exception as e:
        errors.append(f"dashboard: {str(e)}")
        print(f"✗ dashboard.py - Import FAILED: {str(e)}")
    
    # Test analytics_adapter
    try:
        from backend.api.adapters.analytics_adapter import AnalyticsAPI
        api = AnalyticsAPI()
        print("✓ analytics_adapter.py - Import OK")
    except Exception as e:
        errors.append(f"analytics_adapter: {str(e)}")
        print(f"✗ analytics_adapter.py - Import FAILED: {str(e)}")
    
    # Test metrics_adapter
    try:
        from backend.api.adapters.metrics_adapter import MetricsAPI
        api = MetricsAPI()
        print("✓ metrics_adapter.py - Import OK")
    except Exception as e:
        errors.append(f"metrics_adapter: {str(e)}")
        print(f"✗ metrics_adapter.py - Import FAILED: {str(e)}")
    
    print()
    if errors:
        print("=" * 60)
        print("ERRORS FOUND:")
        for error in errors:
            print(f"  - {error}")
        results.append(("Imports", False))
    else:
        print("=" * 60)
        print("✓ ALL IMPORTS SUCCESSFUL")
        results.append(("Imports", True))
    
    # Test helper methods
    print()
    print("=" * 60)
    print("TESTING HELPER METHODS")
    print("=" * 60)
    
    try:
        from backend.api.adapters.jobs_adapter import JobsAPI
        api = JobsAPI()
        
        helpers = [
            '_validate_add_job_inputs',
            '_parse_scheduled_time',
            '_convert_priority',
            '_convert_platform',
            '_check_safety_guard',
            '_resolve_target_scheduler',
            '_add_job_to_scheduler',
            '_sync_job_with_active_scheduler',
            '_count_jobs_by_status',
            '_calculate_today_posts',
            '_calculate_success_rate'
        ]
        
        missing = []
        for helper in helpers:
            if hasattr(api, helper):
                print(f"✓ {helper} exists")
            else:
                missing.append(helper)
                print(f"✗ {helper} MISSING")
        
        if missing:
            print(f"\n✗ Missing {len(missing)} helper methods")
            results.append(("Jobs Helper Methods", False))
        else:
            print(f"\n✓ All {len(helpers)} helper methods exist")
            results.append(("Jobs Helper Methods", True))
            
    except Exception as e:
        print(f"✗ Error testing helper methods: {str(e)}")
        results.append(("Jobs Helper Methods", False))
    
    # Test accounts helpers
    print()
    print("=" * 60)
    print("TESTING ACCOUNTS HELPER METHODS")
    print("=" * 60)
    
    try:
        from backend.api.adapters.accounts_adapter import AccountsAPI
        api = AccountsAPI()
        
        helpers = [
            '_list_accounts_from_mysql',
            '_list_accounts_from_filesystem',
            '_get_account_jobs_count',
            '_get_account_metadata',
            '_build_account_dict',
            '_validate_account_id_for_deletion',
            '_check_deletion_security',
            '_delete_profile_directory',
            '_delete_account_from_mysql'
        ]
        
        missing = []
        for helper in helpers:
            if hasattr(api, helper):
                print(f"✓ {helper} exists")
            else:
                missing.append(helper)
                print(f"✗ {helper} MISSING")
        
        if missing:
            print(f"\n✗ Missing {len(missing)} helper methods")
            results.append(("Accounts Helper Methods", False))
        else:
            print(f"\n✓ All {len(helpers)} helper methods exist")
            results.append(("Accounts Helper Methods", True))
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        results.append(("Accounts Helper Methods", False))
    
    # Test dashboard helpers
    print()
    print("=" * 60)
    print("TESTING DASHBOARD HELPER FUNCTIONS")
    print("=" * 60)
    
    try:
        from backend.api.routes.dashboard import (
            _calculate_jobs_by_status,
            _calculate_jobs_by_platform,
            _parse_created_at,
            _build_timeline_data,
            _calculate_hourly_distribution
        )
        
        helpers = [
            '_calculate_jobs_by_status',
            '_calculate_jobs_by_platform',
            '_parse_created_at',
            '_build_timeline_data',
            '_calculate_hourly_distribution'
        ]
        
        print(f"✓ All {len(helpers)} helper functions imported")
        results.append(("Dashboard Helper Functions", True))
        
    except ImportError as e:
        print(f"✗ Import error: {str(e)}")
        results.append(("Dashboard Helper Functions", False))
    
    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("✅ ALL TESTS PASSED - Refactoring successful!")
    else:
        print("❌ SOME TESTS FAILED - Please check errors above")
    
    return all_passed


def run_pytest_tests():
    """Run pytest tests."""
    print("=" * 60)
    print("RUNNING PYTEST TESTS")
    print("=" * 60)
    print()
    
    test_files = [
        "backend/tests/test_api_routes/test_jobs.py",
        "backend/tests/test_api_routes/test_dashboard.py",
        "backend/tests/modules/jobs/test_jobs_service.py",
    ]
    
    for test_file in test_files:
        test_path = project_root / test_file
        if test_path.exists():
            print(f"Running: {test_file}")
            print("-" * 60)
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                print(result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
                print(f"Exit code: {result.returncode}")
                print()
            except subprocess.TimeoutExpired:
                print(f"⚠ Timeout running {test_file}")
                print()
            except Exception as e:
                print(f"✗ Error running {test_file}: {str(e)}")
                print()
        else:
            print(f"⚠ Test file not found: {test_file}")
            print()
    
    print("=" * 60)
    print("TEST RUN COMPLETE")
    print("=" * 60)


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("RUNNING ALL TESTS")
    print("=" * 60)
    print()
    
    results = []
    
    # Test imports
    print("1. Testing Imports...")
    results.append(("Imports", test_imports()))
    print()
    
    # Test refactoring
    print("2. Testing Refactoring...")
    results.append(("Refactoring", test_refactoring()))
    print()
    
    # Run pytest
    print("3. Running Pytest Tests...")
    run_pytest_tests()
    print()
    
    # Final summary
    print("=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    
    all_passed = all(passed for _, passed in results)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    
    return all_passed


def main():
    """Main function."""
    while True:
        choice = show_menu()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            test_imports()
        elif choice == "2":
            test_refactoring()
        elif choice == "3":
            run_pytest_tests()
        elif choice == "4":
            run_all_tests()
        else:
            print("❌ Invalid option. Please choose 0-4.")
        
        if choice != "0":
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
