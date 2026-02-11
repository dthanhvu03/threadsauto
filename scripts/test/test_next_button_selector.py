"""
Script test nhanh selector div[role="button"][aria-label="Tiếp"]

Cách sử dụng:
1. Mở Facebook compose (đã nhập content)
2. Chạy script này
3. Script sẽ test selector và in kết quả
"""

import asyncio
from playwright.async_api import async_playwright


async def test_next_button_selector():
    """Test selector div[role="button"][aria-label="Tiếp"]"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500,
            devtools=True
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        
        page = await context.new_page()
        
        # Import print utilities if needed
        import sys
        # Setup path using common utility
        from scripts.common import setup_path
        
        # Add parent directory to path (must be after importing common)
        setup_path()
        from scripts.common import print_header
        
        print_header("")
        print("TEST SELECTOR: div[role='button'][aria-label='Tiếp']")
        # Import print utilities if needed
        import sys
        # Setup path using common utility
        from scripts.common import setup_path
        
        # Add parent directory to path (must be after importing common)
        setup_path()
        from scripts.common import print_header
        
        print_header("")
        print("\n📋 HƯỚNG DẪN:")
        print("1. Điều hướng đến Facebook compose (đã nhập content)")
        print("2. Đợi button 'Tiếp' xuất hiện")
        print("3. Nhấn ENTER trong terminal này để test selector")
        print("\n" + "=" * 80)
        
        input("\n⏸️  Nhấn ENTER khi đã sẵn sàng (button 'Tiếp' đã xuất hiện)...")
        
        # Test các biến thể selector
        selectors_to_test = [
            "div[role='button'][aria-label='Tiếp']",
            "div[role=\"button\"][aria-label=\"Tiếp\"]",
            "div[role='button'][aria-label*='Tiếp']",
            "div[role=\"button\"][aria-label*=\"Tiếp\"]",
        ]
        
        print("\n🔍 Đang test các selector...\n")
        
        for selector in selectors_to_test:
            print_header(f"Testing: {selector}", width=80)
            
            try:
                # Test query_selector (tìm 1 element)
                element = await page.query_selector(selector)
                
                if element:
                    print(f"✅ Tìm thấy element với query_selector")
                    
                    # Lấy thông tin element
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    aria_label = await element.get_attribute("aria-label") or ""
                    text_content = await element.evaluate("el => el.textContent || el.innerText || ''")
                    role = await element.get_attribute("role") or ""
                    input_type = await element.get_attribute("type") or ""
                    is_visible = await element.is_visible()
                    
                    print(f"   Tag: {tag_name}")
                    print(f"   Role: {role}")
                    print(f"   Type: {input_type or 'N/A'}")
                    print(f"   Aria-label: {aria_label}")
                    print(f"   Text: {text_content[:50]}")
                    print(f"   Visible: {is_visible}")
                    
                    # Validate
                    is_file_input = (tag_name == "input" and input_type == "file")
                    is_button = (tag_name == "button" or role == "button")
                    
                    if is_file_input:
                        print(f"   ❌ WARNING: Element là file input!")
                    elif not is_button:
                        print(f"   ❌ WARNING: Element không phải button!")
                    elif not is_visible:
                        print(f"   ❌ WARNING: Element không visible!")
                    else:
                        print(f"   ✅ Element hợp lệ - có thể click!")
                        
                        # Test click (không thực sự click, chỉ check)
                        try:
                            # Check nếu có thể click
                            bounding_box = await element.bounding_box()
                            if bounding_box:
                                print(f"   ✅ Element có bounding box: {bounding_box}")
                            else:
                                print(f"   ⚠️  Element không có bounding box")
                        except Exception as e:
                            print(f"   ⚠️  Lỗi khi lấy bounding box: {str(e)}")
                else:
                    print(f"❌ Không tìm thấy element với query_selector")
                    
                    # Test query_selector_all (tìm tất cả)
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"   ⚠️  Nhưng query_selector_all tìm thấy {len(elements)} element(s)")
                    else:
                        print(f"   ❌ query_selector_all cũng không tìm thấy")
                        
            except Exception as e:
                print(f"❌ Lỗi khi test selector: {str(e)}")
        
        print("\n" + "=" * 80)
        print("✅ HOÀN TẤT TEST")
        # Import print utilities if needed
        import sys
        # Setup path using common utility
        from scripts.common import setup_path
        
        # Add parent directory to path (must be after importing common)
        setup_path()
        from scripts.common import print_header
        
        print_header("")
        print("\n💡 KẾT LUẬN:")
        print("- Nếu selector tìm thấy element và element hợp lệ → Selector đúng!")
        print("- Nếu không tìm thấy → Cần kiểm tra lại selector hoặc đợi element xuất hiện")
        print("- Nếu tìm thấy nhưng là file input → Cần selector chính xác hơn")
        print("\n" + "=" * 80)
        
        input("\n⏸️  Nhấn ENTER để đóng browser...")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_next_button_selector())

