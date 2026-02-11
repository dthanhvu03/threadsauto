#!/usr/bin/env python3
"""
Test script for Like functionality.

Usage:
    python scripts/test/test_like.py --account account_01 --hashtags tech,ai --max-likes 5
    python scripts/test/test_like.py --account account_01 --keywords python,javascript --max-likes 10
    python scripts/test/test_like.py --account account_01 --users username1,username2 --max-likes 5
    python scripts/test/test_like.py --account account_01 --from-feed --max-likes 10
"""

# Standard library
import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Local
from browser.manager import BrowserManager
from browser.login_guard import LoginGuard
from config import Config, RunMode
from services.logger import StructuredLogger
from threads.engagement.like_engine import LikeEngine
from threads.engagement.types import LikeCriteria
from services.engagement_safety_guard import get_shared_engagement_safety_guard


async def test_like(
    account_id: str,
    hashtags: list = None,
    keywords: list = None,
    users: list = None,
    from_feed: bool = False,
    max_likes: int = 5
):
    """
    Test like functionality.
    
    Args:
        account_id: Account ID
        hashtags: List of hashtags to like posts from
        keywords: List of keywords to filter posts
        users: List of usernames to like posts from
        from_feed: Like posts from home feed
        max_likes: Maximum number of likes
    """
    print("=" * 60)
    print("🧪 TEST LIKE FUNCTIONALITY")
    print("=" * 60)
    print(f"Account ID: {account_id}")
    print(f"Max Likes: {max_likes}")
    
    if hashtags:
        print(f"Hashtags: {', '.join(hashtags)}")
    if keywords:
        print(f"Keywords: {', '.join(keywords)}")
    if users:
        print(f"Users: {', '.join(users)}")
    if from_feed:
        print("From Feed: Yes")
    print()
    
    config = Config(mode=RunMode.SAFE)
    logger = StructuredLogger(name=f"test_like_{account_id}")
    
    # Get engagement safety guard
    safety_guard = get_shared_engagement_safety_guard(logger=logger)
    
    # Check if can perform action
    from threads.engagement.types import EngagementAction
    can_perform, error_msg, delay = safety_guard.can_perform_action(
        account_id=account_id,
        action_type=EngagementAction.LIKE
    )
    
    if not can_perform:
        print(f"❌ Cannot perform like action: {error_msg}")
        if delay > 0:
            print(f"   Required delay: {delay:.1f}s")
        return
    
    print("✅ Safety check passed")
    print()
    
    try:
        async with BrowserManager(
            account_id=account_id,
            config=config,
            logger=logger
        ) as browser:
            print("🌐 Browser started")
            
            # Navigate to Threads
            await browser.navigate("https://www.threads.com/?hl=vi")
            print("🌐 Navigated to Threads")
            
            # Check login state
            login_guard = LoginGuard(browser.page, config=config, logger=logger)
            is_logged_in = await login_guard.check_login_state()
            
            if not is_logged_in:
                print("🔐 Not logged in, opening login form...")
                instagram_clicked = await login_guard.click_instagram_login()
                if instagram_clicked:
                    print("✅ Login form opened")
                else:
                    print("⚠️  Please login manually")
                
                login_success = await login_guard.wait_for_manual_login(timeout=300)
                if not login_success:
                    print("❌ Login failed")
                    return
                print("✅ Logged in successfully")
            else:
                print("✅ Already logged in")
            
            print()
            print("👍 Starting like actions...")
            print()
            
            # Create like criteria
            criteria = LikeCriteria(
                hashtags=hashtags,
                keywords=keywords,
                users=users,
                from_feed=from_feed,
                max_likes=max_likes,
                min_delay_seconds=2.0,
                max_delay_seconds=5.0
            )
            
            # Create like engine
            like_engine = LikeEngine(
                browser.page,
                config=config,
                logger=logger
            )
            
            # Execute like actions
            results = await like_engine.execute(criteria)
            
            # Record actions in safety guard
            for result in results:
                safety_guard.record_action(
                    account_id=account_id,
                    action_type=EngagementAction.LIKE,
                    success=result.success
                )
            
            # Print results
            print()
            print("=" * 60)
            print("📊 RESULTS")
            print("=" * 60)
            success_count = sum(1 for r in results if r.success)
            failure_count = len(results) - success_count
            
            print(f"Total actions: {len(results)}")
            print(f"✅ Success: {success_count}")
            print(f"❌ Failed: {failure_count}")
            
            if results:
                print()
                print("Details:")
                for i, result in enumerate(results[:10], 1):  # Show first 10
                    status = "✅" if result.success else "❌"
                    error_info = f" - {result.error}" if result.error else ""
                    print(f"  {i}. {status} {result.action_type.value}{error_info}")
                
                if len(results) > 10:
                    print(f"  ... and {len(results) - 10} more")
            
            print()
            print("✅ Test completed!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test Like functionality")
    parser.add_argument("--account", required=True, help="Account ID")
    parser.add_argument("--hashtags", help="Comma-separated hashtags (without #)")
    parser.add_argument("--keywords", help="Comma-separated keywords")
    parser.add_argument("--users", help="Comma-separated usernames (without @)")
    parser.add_argument("--from-feed", action="store_true", help="Like from home feed")
    parser.add_argument("--max-likes", type=int, default=5, help="Maximum number of likes (default: 5)")
    
    args = parser.parse_args()
    
    # Parse comma-separated values
    hashtags = [h.strip() for h in args.hashtags.split(",")] if args.hashtags else None
    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else None
    users = [u.strip() for u in args.users.split(",")] if args.users else None
    
    # Validate at least one criteria provided
    if not any([hashtags, keywords, users, args.from_feed]):
        parser.error("At least one of --hashtags, --keywords, --users, or --from-feed must be provided")
    
    asyncio.run(test_like(
        account_id=args.account,
        hashtags=hashtags,
        keywords=keywords,
        users=users,
        from_feed=args.from_feed,
        max_likes=args.max_likes
    ))


if __name__ == "__main__":
    main()
