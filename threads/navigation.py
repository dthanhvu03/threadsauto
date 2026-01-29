"""
Module: threads/navigation.py

Navigation helpers cho Threads automation.
"""

# Standard library
import asyncio

# Third-party
from playwright.async_api import Page

# Local
from services.logger import StructuredLogger
from threads.behavior import BehaviorHelper
from threads.constants import THREADS_BASE_URL, THREADS_COMPOSE_URL


async def navigate_to_threads(
    page: Page,
    behavior: BehaviorHelper,
    logger: StructuredLogger
) -> None:
    """
    Navigate đến Threads với human-like delay.
    
    Args:
        page: Playwright page instance
        behavior: Behavior helper
        logger: Structured logger
    """
    logger.log_step(
        step="NAVIGATE_TO_THREADS",
        result="IN_PROGRESS"
    )
    
    await page.goto(THREADS_BASE_URL, wait_until="domcontentloaded", timeout=30000)
    await behavior.human_like_delay(1.0, 2.0)
    
    logger.log_step(
        step="NAVIGATE_TO_THREADS",
        result="SUCCESS"
    )


async def navigate_to_compose(
    page: Page,
    logger: StructuredLogger
) -> None:
    """
    Navigate trực tiếp đến compose page.
    
    Args:
        page: Playwright page instance
        logger: Structured logger
    """
    logger.log_step(
        step="NAVIGATE_TO_COMPOSE",
        result="IN_PROGRESS"
    )
    
    try:
        await page.goto(THREADS_COMPOSE_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(1.0)  # Chờ form render
        
        logger.log_step(
            step="NAVIGATE_TO_COMPOSE",
            result="SUCCESS"
        )
    except Exception as e:
        logger.log_step(
            step="NAVIGATE_TO_COMPOSE",
            result="WARNING",
            error=str(e),
            note="Continue with current page"
        )

