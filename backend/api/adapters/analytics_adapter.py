"""
Analytics API wrapper cho UI components.

Cung cấp API để lấy analytics data cho dashboard.
"""

# Standard library
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

# Local
from services.analytics.storage import MetricsStorage
from services.analytics.service import MetricsService
from services.logger import StructuredLogger


class AnalyticsAPI:
    """
    Analytics API wrapper cho UI components.
    """
    
    def __init__(self):
        """Initialize AnalyticsAPI."""
        self.logger = StructuredLogger(name="analytics_api")
        
        # Initialize MetricsStorage với config từ environment
        try:
            from config.storage_config_loader import get_storage_config_from_env
            storage_config = get_storage_config_from_env()
            mysql_config = storage_config.mysql
            
            self.storage = MetricsStorage(
                host=mysql_config.host,
                port=mysql_config.port,
                user=mysql_config.user,
                password=mysql_config.password,
                database=mysql_config.database,
                logger=self.logger
            )
        except Exception as e:
            # Fallback to defaults nếu không load được config
            self.logger.log_step(
                step="INIT_ANALYTICS_API",
                result="WARNING",
                error=f"Failed to load MySQL config, using defaults: {str(e)}",
                error_type=type(e).__name__
            )
            self.storage = MetricsStorage(logger=self.logger)
        
        self.service = MetricsService(storage=self.storage, logger=self.logger)
    
    def get_account_dashboard_data(
        self,
        account_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get dashboard data for account.
        
        Args:
            account_id: Account ID
            days: Number of days to look back
        
        Returns:
            Dict với summary, top_posts, charts data
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get all metrics for account
            metrics_history = self.storage.get_account_metrics_history(
                account_id=account_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if not metrics_history:
                return {
                    "summary": {
                        "total_posts": 0,
                        "total_likes": 0,
                        "total_replies": 0,
                        "total_reposts": 0,
                        "total_shares": 0,
                        "total_views": 0,
                        "avg_likes_per_post": 0.0,
                        "avg_replies_per_post": 0.0,
                        "avg_engagement_rate": 0.0
                    },
                    "top_posts": [],
                    "charts": {
                        "likes_over_time": [],
                        "replies_over_time": [],
                        "engagement_over_time": []
                    }
                }
            
            # Calculate summary
            summary = self._calculate_summary(metrics_history)
            
            # Get top posts
            top_posts = self._get_top_posts(metrics_history)
            
            # Prepare charts data
            charts_data = self._prepare_charts_data(metrics_history)
            
            return {
                "summary": summary,
                "top_posts": top_posts,
                "charts": charts_data
            }
            
        except Exception as e:
            self.logger.log_step(
                step="GET_ACCOUNT_DASHBOARD_DATA",
                result="ERROR",
                error=f"Failed to get dashboard data: {str(e)}",
                account_id=account_id
            )
            raise
    
    def get_thread_details(
        self,
        thread_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed metrics for a thread.
        
        Args:
            thread_id: Thread ID
        
        Returns:
            Dict với thread details và metrics history
        """
        try:
            # Get metrics history
            metrics_history = self.storage.get_thread_metrics_history(thread_id)
            
            if not metrics_history:
                return None
            
            # Get latest metrics
            latest = metrics_history[-1] if metrics_history else None
            
            # Prepare data
            return {
                "thread_id": thread_id,
                "latest_metrics": latest,
                "history": metrics_history,
                "engagement_trend": self._calculate_engagement_trend(metrics_history)
            }
            
        except Exception as e:
            self.logger.log_step(
                step="GET_THREAD_DETAILS",
                result="ERROR",
                error=f"Failed to get thread details: {str(e)}",
                thread_id=thread_id
            )
            return None
    
    def refresh_metrics(
        self,
        account_id: str,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger manual metrics fetch.
        
        Args:
            account_id: Account ID
            thread_id: Optional specific thread ID
        
        Returns:
            Dict với result
        """
        try:
            # This will be handled by MetricsAPI/MetricsService
            # This method is a placeholder for future implementation
            return {
                "success": True,
                "message": "Metrics refresh triggered",
                "account_id": account_id,
                "thread_id": thread_id
            }
        except Exception as e:
            self.logger.log_step(
                step="REFRESH_METRICS",
                result="ERROR",
                error=f"Failed to refresh metrics: {str(e)}",
                account_id=account_id,
                thread_id=thread_id
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    def _should_replace_metric(
        self,
        current_fetched: Optional[str],
        metric_fetched: Optional[str]
    ) -> bool:
        """
        Check if metric should replace current based on fetched_at timestamp.
        
        Args:
            current_fetched: Current metric fetched_at timestamp
            metric_fetched: New metric fetched_at timestamp
        
        Returns:
            True if should replace, False otherwise
        """
        if not metric_fetched or not current_fetched:
            return False
        return metric_fetched > current_fetched
    
    def _update_latest_metrics(
        self,
        latest_metrics: Dict[str, Dict],
        metric: Dict
    ) -> None:
        """
        Update latest metrics dict with new metric.
        
        Args:
            latest_metrics: Dict mapping thread_id -> latest metrics
            metric: New metric dict
        """
        thread_id = metric.get('thread_id')
        if not thread_id:
            return
        
        if thread_id not in latest_metrics:
            latest_metrics[thread_id] = metric
        else:
            # Keep latest by fetched_at
            current = latest_metrics[thread_id]
            if self._should_replace_metric(
                current.get('fetched_at'),
                metric.get('fetched_at')
            ):
                latest_metrics[thread_id] = metric
    
    def _get_latest_metrics_per_thread(self, metrics_history: List[Dict]) -> Dict[str, Dict]:
        """
        Get latest metrics for each thread from history.
        
        Args:
            metrics_history: List of metrics dicts
        
        Returns:
            Dict mapping thread_id -> latest metrics dict
        """
        latest_metrics = {}
        for metric in metrics_history:
            self._update_latest_metrics(latest_metrics, metric)
        return latest_metrics
    
    def _calculate_summary(self, metrics_history: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics."""
        
        # Get latest metrics for each thread
        latest_metrics = self._get_latest_metrics_per_thread(metrics_history)
        
        # Get unique threads
        total_posts = len(latest_metrics)
        
        # Sum up metrics
        total_likes = sum(m.get('likes', 0) for m in latest_metrics.values())
        total_replies = sum(m.get('replies', 0) for m in latest_metrics.values())
        total_reposts = sum(m.get('reposts', 0) for m in latest_metrics.values())
        total_shares = sum(m.get('shares', 0) for m in latest_metrics.values())
        total_views = sum(m.get('views', 0) or 0 for m in latest_metrics.values())
        
        # Calculate averages
        avg_likes = total_likes / total_posts if total_posts > 0 else 0.0
        avg_replies = total_replies / total_posts if total_posts > 0 else 0.0
        
        # Engagement rate (likes + replies + shares) / posts
        total_engagement = total_likes + total_replies + total_shares
        avg_engagement_rate = total_engagement / total_posts if total_posts > 0 else 0.0
        
        return {
            "total_posts": total_posts,
            "total_likes": total_likes,
            "total_replies": total_replies,
            "total_reposts": total_reposts,
            "total_shares": total_shares,
            "total_views": total_views,
            "avg_likes_per_post": round(avg_likes, 2),
            "avg_replies_per_post": round(avg_replies, 2),
            "avg_engagement_rate": round(avg_engagement_rate, 2)
        }
    
    def _get_top_posts(self, metrics_history: List[Dict], limit: int = 10) -> List[Dict]:
        """Get top posts by engagement."""
        
        # Get latest metrics for each thread (reuse helper method)
        latest_metrics = self._get_latest_metrics_per_thread(metrics_history)
        
        # Get job content from database
        try:
            from services.scheduler.storage.mysql_storage import MySQLJobStorage
            from services.scheduler.models import JobStatus
            from config.storage_config_loader import get_storage_config_from_env
            
            storage_config = get_storage_config_from_env()
            mysql_config = storage_config.mysql
            
            job_storage = MySQLJobStorage(
                host=mysql_config.host,
                port=mysql_config.port,
                user=mysql_config.user,
                password=mysql_config.password,
                database=mysql_config.database
            )
            
            # Get all completed jobs và tạo dict thread_id -> content
            jobs = job_storage.get_jobs_by_status(JobStatus.COMPLETED)
            thread_content_map = {}
            for job in jobs:
                if job.thread_id:
                    thread_content_map[job.thread_id] = job.content
        except Exception as e:
            self.logger.log_step(
                step="GET_TOP_POSTS_CONTENT",
                result="WARNING",
                error=f"Failed to load job content: {str(e)}",
                note="Top posts will be shown without content"
            )
            thread_content_map = {}
        
        # Calculate engagement for each post
        posts_with_engagement = []
        for thread_id, metric in latest_metrics.items():
            engagement = (
                metric.get('likes', 0) +
                metric.get('replies', 0) +
                metric.get('shares', 0)
            )
            # Trả về content thực tế cho UI
            # CHỈ sanitize trong logs, KHÔNG sanitize trong API responses
            content = thread_content_map.get(thread_id, "")
            
            posts_with_engagement.append({
                "thread_id": thread_id,
                "account_id": metric.get('account_id'),
                "content": content,
                "likes": metric.get('likes', 0),
                "replies": metric.get('replies', 0),
                "reposts": metric.get('reposts', 0),
                "shares": metric.get('shares', 0),
                "views": metric.get('views'),
                "engagement": engagement,
                "fetched_at": metric.get('fetched_at')
            })
        
        # Sort by engagement
        posts_with_engagement.sort(key=lambda x: x['engagement'], reverse=True)
        
        return posts_with_engagement[:limit]
    
    def _prepare_charts_data(self, metrics_history: List[Dict]) -> Dict[str, List]:
        """Prepare data for charts."""
        
        # Group by date
        likes_by_date = {}
        replies_by_date = {}
        engagement_by_date = {}
        
        for metric in metrics_history:
            fetched_at = metric.get('fetched_at')
            if not fetched_at:
                continue
            
            # Parse date
            try:
                if isinstance(fetched_at, str):
                    date = datetime.fromisoformat(fetched_at.replace('Z', '+00:00')).date()
                elif isinstance(fetched_at, datetime):
                    date = fetched_at.date()
                else:
                    continue
            except (ValueError, TypeError, AttributeError):
                continue
            
            # Aggregate by date (keep max for each day)
            if date not in likes_by_date:
                likes_by_date[date] = 0
                replies_by_date[date] = 0
                engagement_by_date[date] = 0
            
            # Update if this metric is newer
            likes = metric.get('likes', 0)
            replies = metric.get('replies', 0)
            shares = metric.get('shares', 0)
            engagement = likes + replies + shares
            
            likes_by_date[date] = max(likes_by_date[date], likes)
            replies_by_date[date] = max(replies_by_date[date], replies)
            engagement_by_date[date] = max(engagement_by_date[date], engagement)
        
        # Convert to lists sorted by date
        sorted_dates = sorted(likes_by_date.keys())
        
        likes_over_time = [
            {"date": str(date), "likes": likes_by_date[date]}
            for date in sorted_dates
        ]
        
        replies_over_time = [
            {"date": str(date), "replies": replies_by_date[date]}
            for date in sorted_dates
        ]
        
        engagement_over_time = [
            {"date": str(date), "engagement": engagement_by_date[date]}
            for date in sorted_dates
        ]
        
        return {
            "likes_over_time": likes_over_time,
            "replies_over_time": replies_over_time,
            "engagement_over_time": engagement_over_time
        }
    
    def _calculate_engagement_trend(self, metrics_history: List[Dict]) -> List[Dict]:
        """Calculate engagement trend over time."""
        
        trend = []
        for metric in sorted(metrics_history, key=lambda x: x.get('fetched_at', '')):
            fetched_at = metric.get('fetched_at')
            if not fetched_at:
                continue
            
            engagement = (
                metric.get('likes', 0) +
                metric.get('replies', 0) +
                metric.get('shares', 0)
            )
            
            trend.append({
                "date": str(fetched_at),
                "engagement": engagement,
                "likes": metric.get('likes', 0),
                "replies": metric.get('replies', 0),
                "shares": metric.get('shares', 0)
            })
        
        return trend
    
    def get_content_performance_correlation(
        self,
        account_id: str,
        jobs: List[Dict],
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze correlation between content features and engagement metrics.
        
        Args:
            account_id: Account ID
            jobs: List of job dicts (with content)
            days: Number of days to look back for metrics
        
        Returns:
            Dict với correlation data cho charts
        """
        try:
            import re
            from datetime import datetime, timedelta
            
            # Get metrics history
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            metrics_history = self.storage.get_account_metrics_history(
                account_id=account_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if not metrics_history:
                return {
                    "correlation_data": [],
                    "insights": {
                        "optimal_length": None,
                        "optimal_hashtags": None,
                        "optimal_emojis": None,
                        "avg_length_top_posts": None,
                        "avg_hashtags_top_posts": None,
                        "avg_emojis_top_posts": None
                    }
                }
            
            # Get latest metrics per thread
            latest_metrics = self._get_latest_metrics_per_thread(metrics_history)
            
            # Combine jobs with metrics
            correlation_data = []
            top_posts_engagement = []
            
            for job in jobs:
                thread_id = job.get('thread_id')
                if not thread_id:
                    continue
                
                metrics = latest_metrics.get(thread_id)
                if not metrics:
                    continue
                
                content = job.get('content', '')
                if not content:
                    continue
                
                # Calculate content features
                length = len(content)
                word_count = len(content.split())
                hashtag_count = len(re.findall(r'#\w+', content))
                emoji_count = self._count_emojis(content)
                
                # Get engagement
                likes = metrics.get('likes', 0)
                replies = metrics.get('replies', 0)
                shares = metrics.get('shares', 0)
                engagement = likes + replies + shares
                
                correlation_data.append({
                    "thread_id": thread_id,
                    "content_length": length,
                    "word_count": word_count,
                    "hashtag_count": hashtag_count,
                    "emoji_count": emoji_count,
                    "likes": likes,
                    "replies": replies,
                    "shares": shares,
                    "engagement": engagement,
                    "completed_at": job.get('completed_at')
                })
                
                if engagement > 0:
                    top_posts_engagement.append({
                        "length": length,
                        "hashtag_count": hashtag_count,
                        "emoji_count": emoji_count,
                        "engagement": engagement
                    })
            
            # Calculate insights
            insights = self._calculate_correlation_insights(correlation_data, top_posts_engagement)
            
            return {
                "correlation_data": correlation_data,
                "insights": insights
            }
            
        except Exception as e:
            self.logger.log_step(
                step="GET_CONTENT_PERFORMANCE_CORRELATION",
                result="ERROR",
                error=f"Failed to get correlation data: {str(e)}",
                account_id=account_id
            )
            return {
                "correlation_data": [],
                "insights": {}
            }
    
    def _count_emojis(self, text: str) -> int:
        """Count emojis in text."""
        import re
        # Basic emoji pattern (covers most common emojis)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return len(emoji_pattern.findall(text))
    
    def _calculate_correlation_insights(
        self,
        correlation_data: List[Dict],
        top_posts: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate insights from correlation data."""
        
        if not correlation_data:
            return {}
        
        if not top_posts:
            return {}
        
        # Calculate optimal values from top performers (top 20% by engagement)
        top_posts_sorted = sorted(top_posts, key=lambda x: x['engagement'], reverse=True)
        top_20_percent = max(1, int(len(top_posts_sorted) * 0.2))
        top_performers = top_posts_sorted[:top_20_percent]
        
        if top_performers:
            avg_length_top = sum(p['length'] for p in top_performers) / len(top_performers)
            avg_hashtags_top = sum(p['hashtag_count'] for p in top_performers) / len(top_performers)
            avg_emojis_top = sum(p['emoji_count'] for p in top_performers) / len(top_performers)
        else:
            avg_length_top = None
            avg_hashtags_top = None
            avg_emojis_top = None
        
        # Calculate overall averages for comparison
        avg_length_all = sum(d['content_length'] for d in correlation_data) / len(correlation_data)
        
        # Determine optimal range (top performers average ± 20%)
        optimal_length = None
        optimal_hashtags = None
        optimal_emojis = None
        
        if avg_length_top:
            optimal_length = {
                "min": int(avg_length_top * 0.8),
                "max": int(avg_length_top * 1.2),
                "avg": int(avg_length_top)
            }
        
        if avg_hashtags_top is not None:
            optimal_hashtags = {
                "min": max(0, int(avg_hashtags_top * 0.8)),
                "max": int(avg_hashtags_top * 1.2),
                "avg": round(avg_hashtags_top, 1)
            }
        
        if avg_emojis_top is not None:
            optimal_emojis = {
                "min": max(0, int(avg_emojis_top * 0.8)),
                "max": int(avg_emojis_top * 1.2),
                "avg": round(avg_emojis_top, 1)
            }
        
        return {
            "optimal_length": optimal_length,
            "optimal_hashtags": optimal_hashtags,
            "optimal_emojis": optimal_emojis,
            "avg_length_top_posts": int(avg_length_top) if avg_length_top else None,
            "avg_hashtags_top_posts": round(avg_hashtags_top, 1) if avg_hashtags_top is not None else None,
            "avg_emojis_top_posts": round(avg_emojis_top, 1) if avg_emojis_top is not None else None,
            "avg_length_all": int(avg_length_all) if correlation_data else None
        }
