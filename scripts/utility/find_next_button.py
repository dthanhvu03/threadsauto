"""
Script helper để tìm chính xác button "Tiếp" trên Facebook.

Cách sử dụng:
1. Chạy script này khi đang ở bước cần click "Tiếp"
2. Script sẽ tìm tất cả các button có thể và in ra thông tin chi tiết
3. Copy selector chính xác vào facebook/selectors.py
"""

import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.common import setup_path, print_header
setup_path()

import asyncio
from playwright.async_api import async_playwright


async def find_next_button():
    """Tìm và in ra tất cả button 'Tiếp' có thể."""
    
    async with async_playwright() as p:
        # Mở browser với DevTools để inspect
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000,  # Chậm lại để quan sát
            devtools=True  # Mở DevTools
        )
        
        # Sử dụng profile hiện tại (nếu có)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        
        page = await context.new_page()
        
        print_header("")
        print("SCRIPT TÌM BUTTON 'TIẾP' TRÊN FACEBOOK")
        print_header("")
        print("\n📋 HƯỚNG DẪN:")
        print("1. Điều hướng đến trang Facebook compose (đã nhập content)")
        print("2. Đợi đến khi button 'Tiếp' xuất hiện")
        print("3. Nhấn ENTER trong terminal này để bắt đầu tìm kiếm")
        print("\n" + "=" * 80)
        
        input("\n⏸️  Nhấn ENTER khi đã sẵn sàng (button 'Tiếp' đã xuất hiện)...")
        
        print("\n🔍 Đang tìm kiếm button 'Tiếp'...\n")
        
        # 1. Tìm bằng aria-label
        print_header("")
        print("1️⃣  TÌM BẰNG ARIA-LABEL")
        print_header("")
        
        aria_selectors = [
            "div[role='button'][aria-label='Tiếp']",
            "div[role='button'][aria-label*='Tiếp']",
            "button[aria-label='Tiếp']",
            "button[aria-label*='Tiếp']",
        ]
        
        for selector in aria_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"\n✅ Tìm thấy {len(elements)} element(s) với selector: {selector}")
                    for i, el in enumerate(elements, 1):
                        info = await get_element_info(el, page)
                        print(f"\n   Element {i}:")
                        print_element_info(info)
                else:
                    print(f"❌ Không tìm thấy: {selector}")
            except Exception as e:
                print(f"⚠️  Lỗi với selector {selector}: {str(e)}")
        
        # 2. Tìm bằng text content
        print("\n" + "=" * 80)
        print("2️⃣  TÌM BẰNG TEXT CONTENT")
        print_header("")
        
        # Tìm tất cả button/div có role="button"
        all_buttons = await page.query_selector_all(
            "div[role='button'], button"
        )
        
        print(f"\n🔍 Tìm thấy {len(all_buttons)} button(s) trên trang")
        
        matching_buttons = []
        for i, btn in enumerate(all_buttons):
            try:
                text = await btn.evaluate("el => el.textContent || el.innerText || ''")
                aria_label = await btn.get_attribute("aria-label") or ""
                
                if "Tiếp" in text or "Tiếp" in aria_label or "Next" in text or "Next" in aria_label:
                    matching_buttons.append((i, btn, text, aria_label))
            except Exception:
                continue
        
        if matching_buttons:
            print(f"\n✅ Tìm thấy {len(matching_buttons)} button(s) có text/aria-label chứa 'Tiếp' hoặc 'Next':")
            for idx, (orig_idx, btn, text, aria_label) in enumerate(matching_buttons, 1):
                print(f"\n   Button {idx} (index {orig_idx}):")
                info = await get_element_info(btn, page)
                print_element_info(info)
        else:
            print("\n❌ Không tìm thấy button nào có text/aria-label chứa 'Tiếp' hoặc 'Next'")
        
        # 3. Tìm bằng XPath
        print("\n" + "=" * 80)
        print("3️⃣  TÌM BẰNG XPath")
        print_header("")
        
        xpath_selectors = [
            "//div[@role='button' and (@aria-label='Tiếp' or contains(text(), 'Tiếp'))]",
            "//button[@aria-label='Tiếp' or contains(text(), 'Tiếp')]",
            "//div[@role='button' and contains(@aria-label, 'Tiếp')]",
            "//button[contains(text(), 'Tiếp')]",
        ]
        
        for xpath in xpath_selectors:
            try:
                elements = await page.query_selector_all(f"xpath={xpath}")
                if elements:
                    print(f"\n✅ Tìm thấy {len(elements)} element(s) với XPath: {xpath}")
                    for i, el in enumerate(elements, 1):
                        info = await get_element_info(el, page)
                        print(f"\n   Element {i}:")
                        print_element_info(info)
                else:
                    print(f"❌ Không tìm thấy: {xpath}")
            except Exception as e:
                print(f"⚠️  Lỗi với XPath {xpath}: {str(e)}")
        
        # 4. Lấy full XPath của tất cả button có thể
        print("\n" + "=" * 80)
        print("4️⃣  FULL XPATH CỦA CÁC BUTTON CÓ THỂ")
        print_header("")
        
        if matching_buttons:
            for idx, (orig_idx, btn, text, aria_label) in enumerate(matching_buttons, 1):
                try:
                    full_xpath = await btn.evaluate("""
                        (el) => {
                            let path = '';
                            while (el && el.nodeType === Node.ELEMENT_NODE) {
                                let selector = el.nodeName.toLowerCase();
                                if (el.id) {
                                    selector += `[@id='${el.id}']`;
                                    path = '/' + selector + path;
                                    break;
                                } else {
                                    let sibling = el;
                                    let nth = 1;
                                    while (sibling.previousElementSibling) {
                                        sibling = sibling.previousElementSibling;
                                        nth++;
                                    }
                                    selector += `[${nth}]`;
                                    path = '/' + selector + path;
                                }
                                el = el.parentElement;
                            }
                            return path;
                        }
                    """)
                    print(f"\n   Button {idx} Full XPath: /html{full_xpath}")
                except Exception as e:
                    print(f"\n   Button {idx}: Không thể lấy XPath - {str(e)}")
        
        # 5. Test click
        print("\n" + "=" * 80)
        print("5️⃣  TEST CLICK (KHÔNG THỰC SỰ CLICK)")
        print_header("")
        
        if matching_buttons:
            print("\n⚠️  Các button có thể click được (kiểm tra không phải file input):")
            for idx, (orig_idx, btn, text, aria_label) in enumerate(matching_buttons, 1):
                try:
                    tag_name = await btn.evaluate("el => el.tagName.toLowerCase()")
                    input_type = await btn.get_attribute("type")
                    role = await btn.get_attribute("role")
                    is_visible = await btn.is_visible()
                    is_enabled = await btn.is_enabled() if hasattr(btn, 'is_enabled') else True
                    
                    is_file_input = (tag_name == "input" and input_type == "file")
                    is_button = (tag_name == "button" or role == "button")
                    
                    status = "✅" if (is_button and not is_file_input and is_visible) else "❌"
                    print(f"\n   {status} Button {idx}:")
                    print(f"      - Tag: {tag_name}")
                    print(f"      - Role: {role}")
                    print(f"      - Type: {input_type or 'N/A'}")
                    print(f"      - Visible: {is_visible}")
                    print(f"      - Is Button: {is_button}")
                    print(f"      - Is File Input: {is_file_input}")
                    print(f"      - Safe to Click: {is_button and not is_file_input and is_visible}")
                except Exception as e:
                    print(f"\n   ⚠️  Button {idx}: Lỗi kiểm tra - {str(e)}")
        
        print("\n" + "=" * 80)
        print("✅ HOÀN TẤT")
        print_header("")
        print("\n💡 GỢI Ý:")
        print("1. Copy selector/XPath chính xác nhất vào facebook/selectors.py")
        print("2. Đặt selector chính xác nhất lên đầu danh sách")
        print("3. Test lại với FacebookComposer")
        print("\n" + "=" * 80)
        
        # Giữ browser mở để inspect thủ công
        input("\n⏸️  Nhấn ENTER để đóng browser...")
        await browser.close()


async def get_element_info(element, _page=None):
    """Lấy thông tin chi tiết của element."""
    try:
        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
        text_content = await element.evaluate("el => el.textContent || el.innerText || ''")
        aria_label = await element.get_attribute("aria-label") or ""
        role = await element.get_attribute("role") or ""
        input_type = await element.get_attribute("type") or ""
        class_name = await element.get_attribute("class") or ""
        id_attr = await element.get_attribute("id") or ""
        is_visible = await element.is_visible()
        
        # Lấy bounding box
        box = await element.bounding_box()
        position = f"({box['x']:.0f}, {box['y']:.0f})" if box else "N/A"
        
        return {
            "tag_name": tag_name,
            "text_content": text_content.strip()[:100],  # Limit text
            "aria_label": aria_label,
            "role": role,
            "input_type": input_type,
            "class": class_name[:100] if class_name else "",  # Limit class
            "id": id_attr,
            "is_visible": is_visible,
            "position": position,
        }
    except Exception as e:
        return {"error": str(e)}


def print_element_info(info):
    """In thông tin element."""
    if "error" in info:
        print(f"      ❌ Lỗi: {info['error']}")
        return
    
    print(f"      Tag: {info.get('tag_name', 'N/A')}")
    print(f"      Role: {info.get('role', 'N/A')}")
    print(f"      Type: {info.get('input_type', 'N/A')}")
    print(f"      ID: {info.get('id', 'N/A')}")
    print(f"      Class: {info.get('class', 'N/A')[:50]}...")
    print(f"      Text: {info.get('text_content', 'N/A')[:50]}")
    print(f"      Aria-label: {info.get('aria_label', 'N/A')}")
    print(f"      Visible: {info.get('is_visible', 'N/A')}")
    print(f"      Position: {info.get('position', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(find_next_button())

