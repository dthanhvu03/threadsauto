#!/usr/bin/env python3
"""
Test callback factory để kiểm tra có hoạt động không.

Usage:
    python scripts/test_callback_factory.py
"""

import sys
from pathlib import Path
import inspect

# Setup path using common utility
from scripts.common import setup_path, print_header, print_section

# Add parent directory to path (must be after importing common)
setup_path()

# Mock streamlit
sys.modules['streamlit'] = type(sys)('streamlit')

try:
    from ui.utils import get_platform_callback
    from services.scheduler.models import Platform
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def test_callback_factory():
    """Test callback factory."""
    print_header("🔍 TEST CALLBACK FACTORY")
    print()
    
    try:
        # Test Threads callback
        print_section("📋 1. TEST THREADS CALLBACK")
        threads_callback = get_platform_callback(Platform.THREADS)
        
        if threads_callback is None:
            print("❌ get_platform_callback returned None!")
            return
        
        print(f"✅ Threads callback: {threads_callback}")
        print(f"   Function name: {threads_callback.__name__}")
        
        # Check signature
        sig = inspect.signature(threads_callback)
        print(f"   Signature: {sig}")
        params = list(sig.parameters.keys())
        print(f"   Parameters: {params}")
        
        if len(params) < 3:
            print("   ❌ Callback chỉ có 2 parameters, cần 3 (account_id, content, status_updater)")
        else:
            print("   ✅ Callback có đủ 3 parameters")
        
        print()
        
        # Test Facebook callback
        print_section("📋 2. TEST FACEBOOK CALLBACK")
        try:
            facebook_callback = get_platform_callback(Platform.FACEBOOK)
            if facebook_callback is None:
                print("❌ get_platform_callback returned None for FACEBOOK!")
            else:
                print(f"✅ Facebook callback: {facebook_callback}")
                sig = inspect.signature(facebook_callback)
                params = list(sig.parameters.keys())
                print(f"   Parameters: {params}")
        except Exception as e:
            print(f"⚠️  Facebook callback error: {e}")
        
        print()
        print_header("💡 KẾT QUẢ")
        if threads_callback and len(list(inspect.signature(threads_callback).parameters.keys())) >= 3:
            print("✅ Callback factory hoạt động bình thường")
        else:
            print("❌ Callback factory có vấn đề!")
            print("   → Cần kiểm tra lại get_platform_callback() trong ui/utils.py")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_callback_factory()
