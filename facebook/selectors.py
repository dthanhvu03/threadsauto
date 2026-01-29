"""
Module: facebook/selectors.py

Selector definitions cho Facebook automation.
"""

# Constants
XPATH_PREFIX = "xpath="

# Các phiên bản selector
SELECTORS = {
    "v1": {
        "compose_button": [
            # Selector từ user - Full XPath (ưu tiên cao nhất)
            f"{XPATH_PREFIX}/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[2]/div/div[2]/div/div/div/div/div[1]",
            # XPath từ user
            f"{XPATH_PREFIX}//*[@id='mount_0_0_SA']/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[2]/div/div[2]/div/div/div/div/div[1]",
            # Selector dựa trên text "Review ơi, bạn đang nghĩ gì thế?" hoặc tương tự
            "div[role='button']:has-text('Review ơi, bạn đang nghĩ gì thế?')",
            "div[role='button']:has-text('bạn đang nghĩ gì')",
            "div[role='button']:has-text('What')",
            "div[role='button']:has-text('Tạo')",
            # Selector cho nút "Tạo bài viết" hoặc "What's on your mind?"
            "div[role='button'][aria-label*='What']",
            "div[role='button'][aria-label*='Tạo']",
            "div[role='button'][aria-label*='nghĩ gì']",
            # XPath fallback
            f"{XPATH_PREFIX}//div[@role='button' and (contains(@aria-label, 'What') or contains(@aria-label, 'Tạo') or contains(@aria-label, 'nghĩ gì'))]",
            # Selector cho textarea placeholder
            "div[data-pagelet='FeedComposer'] div[role='button']",
            "div[data-pagelet='FeedComposer'] textarea",
        ],
        "compose_input": [
            # Selector từ user - Full XPath (ưu tiên cao nhất)
            f"{XPATH_PREFIX}/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/form/div/div[1]/div/div/div/div[2]/div[1]/div[1]/div[1]",
            # XPath từ user
            f"{XPATH_PREFIX}//*[@id='mount_0_0_SA']/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/form/div/div[1]/div/div/div/div[2]/div[1]/div[1]/div[1]",
            # Selector dựa trên aria-placeholder "Review ơi, bạn đang nghĩ gì thế?"
            "div[contenteditable='true'][role='textbox'][data-lexical-editor='true'][aria-placeholder*='Review ơi, bạn đang nghĩ gì thế?']",
            "div[contenteditable='true'][role='textbox'][aria-placeholder*='Review ơi, bạn đang nghĩ gì thế?']",
            "div[contenteditable='true'][aria-placeholder*='nghĩ gì']",
            # Selector cho textarea hoặc contenteditable trong modal/compose form
            # Ưu tiên: Tìm trong modal/dialog trước
            "div[role='dialog'] div[contenteditable='true'][role='textbox'][data-lexical-editor='true']",
            "div[role='dialog'] div[contenteditable='true'][role='textbox']",
            "div[role='dialog'] div[contenteditable='true']",
            "div[aria-modal='true'] div[contenteditable='true'][role='textbox'][data-lexical-editor='true']",
            "div[aria-modal='true'] div[contenteditable='true'][role='textbox']",
            "div[aria-modal='true'] div[contenteditable='true']",
            # Selector cho textarea hoặc contenteditable (general)
            "div[contenteditable='true'][role='textbox'][data-lexical-editor='true']",
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
            "textarea[placeholder*='What']",
            "textarea[placeholder*='Tạo']",
            "textarea[placeholder*='nghĩ gì']",
            "textarea",
            # XPath fallback - tìm trong modal trước
            f"{XPATH_PREFIX}//div[@role='dialog']//div[@contenteditable='true' and @role='textbox' and @data-lexical-editor='true']",
            f"{XPATH_PREFIX}//div[@role='dialog']//div[@contenteditable='true' and @role='textbox']",
            f"{XPATH_PREFIX}//div[@aria-modal='true']//div[@contenteditable='true' and @role='textbox']",
            f"{XPATH_PREFIX}//div[@contenteditable='true' and @role='textbox' and @data-lexical-editor='true']",
            f"{XPATH_PREFIX}//div[@contenteditable='true' and @role='textbox']",
            f"{XPATH_PREFIX}//textarea",
        ],
        "next_button": [
            # ✅ ƯU TIÊN CAO NHẤT: Dùng getByRole trong code (không cần selector ở đây)
            # Code sẽ dùng: page.get_by_role("button", name="Tiếp")
            # → Selector bền nhất, Facebook đổi class cũng không gãy
            
            # Fallback selectors (chỉ dùng khi getByRole fail):
            # Selector dựa trên aria-label "Tiếp" (chính xác nhất, tránh file input)
            "div[role='button'][aria-label='Tiếp']",
            "div[role=\"button\"][aria-label=\"Tiếp\"]",  # Double quotes variant
            # Selector với wildcard (aria-label chứa "Tiếp")
            "div[role='button'][aria-label*='Tiếp']",
            "div[role=\"button\"][aria-label*=\"Tiếp\"]",  # Double quotes variant
            # Button tag với aria-label
            "button[aria-label='Tiếp']",
            "button[aria-label=\"Tiếp\"]",  # Double quotes variant
            "button[aria-label*='Tiếp']",
            "button[aria-label*=\"Tiếp\"]",  # Double quotes variant
            # Selector dựa trên text "Tiếp" (không phải input)
            "div[role='button']:has-text('Tiếp')",
            "button:has-text('Tiếp')",
            # XPath fallback - tìm button có aria-label hoặc text "Tiếp"
            f"{XPATH_PREFIX}//div[@role='button' and (@aria-label='Tiếp' or contains(text(), 'Tiếp'))]",
            f"{XPATH_PREFIX}//button[@aria-label='Tiếp' or contains(text(), 'Tiếp')]",
            # XPath mới từ user (2024) - Full XPath
            f"{XPATH_PREFIX}/html/body/div/div/div/div/div[4]/div/div/div/div/div[2]/div/div/div/form/div/div/div/div/div/div[3]/div[2]",
            # XPath mới từ user (2024) - XPath với ID mount_0_0_uz
            f"{XPATH_PREFIX}//*[@id='mount_0_0_uz']/div[1]/div[1]/div[1]/div[4]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/form[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[3]/div[2]",
            # XPath từ user cũ - nhưng sẽ tìm button con bên trong
            # (XPath này có thể trỏ đến container, cần tìm button con)
            f"{XPATH_PREFIX}/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/form/div/div[1]/div/div/div/div[3]/div[2]//div[@role='button' and (@aria-label='Tiếp' or contains(text(), 'Tiếp'))]",
            f"{XPATH_PREFIX}//*[@id='mount_0_0_Eb']/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/form/div/div[1]/div/div/div/div[3]/div[2]//div[@role='button' and (@aria-label='Tiếp' or contains(text(), 'Tiếp'))]",
            # XPath gốc từ user cũ (fallback - sẽ tìm button con trong code)
            f"{XPATH_PREFIX}/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/form/div/div[1]/div/div/div/div[3]/div[2]",
            f"{XPATH_PREFIX}//*[@id='mount_0_0_Eb']/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/form/div/div[1]/div/div/div/div[3]/div[2]",
        ],
        "post_button": [
            # Ưu tiên tuyệt đối
            "div[role='button'][aria-label='Post']:not([aria-disabled='true'])",
            "div[role='button'][aria-label='Post']",
            # ================================
            # 1. Full XPath tuyệt đối (chỉ dùng khi thật sự cần)
            # ================================
            "xpath=/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/form/div/div[2]/div/div/div[2]/div/div/div[3]/div/div[2]",

            # ================================
            # 2. Ưu tiên aria-label (ổn định nhất)
            # ================================
            "div[role='button'][aria-label='Đăng']:not([aria-disabled='true'])",
            "div[role='button'][aria-label='Post']:not([aria-disabled='true'])",

            # ================================
            # 3. Playwright has-text (UI ngôn ngữ VN / EN)
            # ================================
            "div[role='button']:has-text('Đăng'):not([aria-disabled='true'])",
            "div[role='button']:has-text('Post'):not([aria-disabled='true'])",
            "button:has-text('Đăng'):not([disabled])",
            "button:has-text('Post'):not([disabled])",

            # ================================
            # 4. XPath fallback – dò text CON (Facebook-safe)
            # ================================
            "xpath=//div[@role='button' and not(@aria-disabled='true') and ("
            "contains(., 'Đăng') or contains(., 'Post') or "
            "@aria-label='Đăng' or @aria-label='Post'"
            ")]",

            "xpath=//button[not(@disabled) and (contains(., 'Đăng') or contains(., 'Post'))]",
        ],

        "success_indicator": [
            # Selector để verify post thành công
            "div[role='article']",
            "div[data-pagelet='FeedUnit']",
            "a[href*='/posts/']",
        ],
        "error_message": [
            # Selector cho error message
            "div[role='alert']",
            "div[class*='error']",
            "div:has-text('error')",
        ]
    }
}

