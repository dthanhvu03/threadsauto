"""
Module: facebook/navigation.py

Navigation helpers cho Facebook automation.
"""

# Standard library
import asyncio

# Third-party
from playwright.async_api import Page

# Local
from services.logger import StructuredLogger
from threads.behavior import BehaviorHelper

# Constants
FACEBOOK_URL = "https://www.facebook.com"


async def navigate_to_facebook(
    page: Page,
    behavior: BehaviorHelper,
    logger: StructuredLogger
) -> None:
    """
    Navigate đến Facebook với human-like delay.
    
    Args:
        page: Playwright page instance
        behavior: Behavior helper
        logger: Structured logger
    """
    logger.log_step(
        step="NAVIGATE_TO_FACEBOOK",
        result="IN_PROGRESS"
    )
    
    await page.goto(FACEBOOK_URL, wait_until="domcontentloaded", timeout=30000)
    await behavior.human_like_delay(1.0, 2.0)
    
    logger.log_step(
        step="NAVIGATE_TO_FACEBOOK",
        result="SUCCESS"
    )

