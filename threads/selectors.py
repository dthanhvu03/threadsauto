"""
Module: threads/selectors.py

Selector definitions cho Threads automation.
"""

# Constants
XPATH_PREFIX = "xpath="

# Các phiên bản selector
SELECTORS = {
    "v1": {
        "compose_button": [
            # Selector thành công nhất từ log (5 lần thành công)
            "div[role='button']:has(svg[aria-label='Create'])",
            # XPath từ user (fallback)
            f"{XPATH_PREFIX}/html/body/div[1]/div/div/div[2]/div[2]/div[3]",
            # Selector dựa trên aria-label "Tạo" (tiếng Việt)
            "div[role='button']:has(svg[aria-label='Tạo'])",
            # Fallback selectors
            "a[href*='/post']",
            "a[href*='/compose']"
        ],
        "compose_input": [
            # Full XPath từ element thực tế (ưu tiên CAO NHẤT - từ user)
            f"{XPATH_PREFIX}/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div[2]/div/div/div/div/div[2]/div/div/div[1]/div[2]/div[2]",
            # XPath với ID từ element thực tế
            f"{XPATH_PREFIX}//*[@id='mount_0_0_cZ']/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div[2]/div/div/div/div/div[2]/div/div/div[1]/div[2]/div[2]",
            # Selector ưu tiên: Tìm bằng aria-label (tiếng Việt) - từ element thực tế
            "div[aria-label*='Trường văn bản trống'][contenteditable='true'][role='textbox'][data-lexical-editor='true']",
            "div[aria-label*='Trường văn bản trống'][contenteditable='true'][role='textbox']",
            # Selector từ modal mới (tiếng Anh)
            "div[aria-label='Empty text field. Type to compose a new post.'][contenteditable='true'][role='textbox'][data-lexical-editor='true']",
            "div[aria-label='Empty text field. Type to compose a new post.'][contenteditable='true'][role='textbox']",
            "div[aria-label='Empty text field. Type to compose a new post.'][contenteditable='true']",
            # Full XPath từ modal mới (fallback)
            f"{XPATH_PREFIX}/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div[2]",
            # XPath từ modal mới với ID (fallback)
            f"{XPATH_PREFIX}//*[@id='mount_0_0_OC']/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div[2]",
            # Full XPath thành công nhất từ log cũ (fallback)
            f"{XPATH_PREFIX}/html/body/div[2]/div/div/div[2]/div[2]/div/div/div/div[1]/div[1]/div[1]/div/div/div[2]/div[1]/div[2]/div/div[1]",
            # XPath với ID (fallback)
            f"{XPATH_PREFIX}//*[@id='barcelona-page-layout']/div/div/div[2]/div[1]/div[2]/div/div[1]",
            # Contenteditable với role textbox
            "div[contenteditable='true'][role='textbox'][data-lexical-editor='true']",
            "div[contenteditable='true'][role='textbox']",
            # Contenteditable đơn giản (fallback)
            "div[contenteditable='true']"
        ],
        "post_button": [
            # Full XPath từ element thực tế (ưu tiên CAO NHẤT - từ user)
            f"{XPATH_PREFIX}/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div[2]/div/div/div/div/div[3]/div/div[1]",
            # XPath với ID từ element thực tế
            f"{XPATH_PREFIX}//*[@id='mount_0_0_cZ']/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div[2]/div/div/div/div/div[3]/div/div[1]",
            # Selector không dựa vào class names cụ thể (Meta thay đổi thường xuyên)
            # Ưu tiên: Tìm button có text "Đăng" (tiếng Việt) và không disabled
            "div[role='button']:has-text('Đăng'):not([aria-disabled='true']):not([disabled])",
            "button:has-text('Đăng'):not([aria-disabled='true']):not([disabled])",
            # Fallback: Tìm button có text "Đăng" (bất kể disabled hay không)
            "div[role='button']:has-text('Đăng')",
            "button:has-text('Đăng')",
            # Ưu tiên: Tìm button có text "Post" và không disabled
            "div[role='button']:has-text('Post'):not([aria-disabled='true']):not([disabled])",
            "button:has-text('Post'):not([aria-disabled='true']):not([disabled])",
            # Fallback: Tìm button có text "Post" (bất kể disabled hay không)
            "div[role='button']:has-text('Post')",
            "button:has-text('Post')",
            # Tìm bằng aria-label
            "div[role='button'][aria-label*='Post']:not([aria-disabled='true'])",
            "div[role='button'][aria-label*='Đăng']:not([aria-disabled='true'])",
            "button[aria-label*='Post']:not([aria-disabled='true'])",
            "button[aria-label*='Đăng']:not([aria-disabled='true'])",
            # XPath fallbacks (ít thay đổi hơn class names)
            f"{XPATH_PREFIX}//div[@role='button' and (contains(text(), 'Post') or contains(text(), 'Đăng'))]",
            f"{XPATH_PREFIX}//button[contains(text(), 'Post') or contains(text(), 'Đăng')]",
            # XPath từ modal compose (fallback)
            f"{XPATH_PREFIX}//div[@role='dialog']//div[@role='button'][contains(text(), 'Post') or contains(text(), 'Đăng')]",
            f"{XPATH_PREFIX}//div[@role='dialog']//button[contains(text(), 'Post') or contains(text(), 'Đăng')]"
        ],
        "success_indicator": [
            "div[aria-label*='Your thread']",
            "a[href*='/post/']"
        ],
        "error_message": [
            "div[role='alert']",
            "div[class*='error']",
            "div:has-text('error')"
        ],
        "add_to_thread_button": [
            # Full XPath từ element thực tế (ưu tiên CAO NHẤT - từ user)
            f"{XPATH_PREFIX}/html/body/div[5]/div[1]/div/div[2]/div/div/div/div[2]/div/div/div/div/div[2]/div/div/div[2]/div[2]",
            # Selector dựa trên text "Thêm vào thread" (tiếng Việt)
            "div[role='button']:has-text('Thêm vào thread')",
            "div[role='button']:has(span:has-text('Thêm vào thread'))",
            "button:has-text('Thêm vào thread')",
            # Selector dựa trên text "Add to thread" (tiếng Anh)
            "div[role='button']:has-text('Add to thread')",
            "div[role='button']:has(span:has-text('Add to thread'))",
            "button:has-text('Add to thread')",
            # XPath fallback
            f"{XPATH_PREFIX}//div[@role='button' and (contains(text(), 'Thêm vào thread') or contains(text(), 'Add to thread'))]",
            f"{XPATH_PREFIX}//button[contains(text(), 'Thêm vào thread') or contains(text(), 'Add to thread')]"
        ],
        "comment_input": [
            # Full XPath từ element thực tế (ưu tiên CAO NHẤT - từ user)
            f"{XPATH_PREFIX}/html/body/div[5]/div[1]/div/div[2]/div/div/div/div[2]/div/div/div/div/div[2]/div[2]/div/div[1]/div[2]/div[2]",
            # Selector dựa trên aria-label (tiếng Việt)
            "div[aria-label*='Trường văn bản trống'][aria-placeholder*='Bạn nói gì thêm đi'][contenteditable='true'][role='textbox'][data-lexical-editor='true']",
            "div[aria-label*='Trường văn bản trống'][contenteditable='true'][role='textbox'][data-lexical-editor='true']",
            "div[aria-label*='Trường văn bản trống'][contenteditable='true'][role='textbox']",
            # Selector dựa trên aria-placeholder
            "div[aria-placeholder*='Bạn nói gì thêm đi'][contenteditable='true'][role='textbox'][data-lexical-editor='true']",
            "div[aria-placeholder*='Bạn nói gì thêm đi'][contenteditable='true'][role='textbox']",
            # Contenteditable với role textbox
            "div[contenteditable='true'][role='textbox'][data-lexical-editor='true']",
            "div[contenteditable='true'][role='textbox']",
            # Contenteditable đơn giản (fallback)
            "div[contenteditable='true']"
        ]
    }
}

