"""
Media service for feed items.

Handles downloading, caching, and serving media from Instagram CDN.
"""

# Standard library
import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

# Third-party
import httpx
from fastapi.responses import StreamingResponse, FileResponse

# Local
from services.logger import StructuredLogger
from services.storage.feed_storage import FeedStorage
from config.storage_config_loader import get_storage_config_from_env


class MediaService:
    """
    Service for managing media downloads and caching.
    
    Downloads media from Instagram CDN and caches in filesystem.
    Serves media with proper headers to bypass CORS.
    """
    
    def __init__(self, feed_storage: Optional[FeedStorage] = None):
        """
        Initialize media service.
        
        Args:
            feed_storage: FeedStorage instance. If None, creates new instance.
        """
        self.logger = StructuredLogger(name="media_service")
        
        # Initialize feed storage
        if feed_storage:
            self.feed_storage = feed_storage
        else:
            try:
                storage_config = get_storage_config_from_env()
                mysql_config = storage_config.mysql
                self.feed_storage = FeedStorage(
                    host=mysql_config.host,
                    port=mysql_config.port,
                    user=mysql_config.user,
                    password=mysql_config.password,
                    database=mysql_config.database,
                    charset=mysql_config.charset,
                    logger=self.logger
                )
            except Exception as e:
                self.logger.log_step(
                    step="INIT_MEDIA_SERVICE",
                    result="ERROR",
                    error=f"Failed to initialize FeedStorage: {str(e)}"
                )
                raise
        
        # Media storage directory
        self.media_dir = Path("./media")
        self.media_dir.mkdir(exist_ok=True, mode=0o755)
        
        # Max file sizes (bytes)
        self.max_image_size = 10 * 1024 * 1024  # 10MB
        self.max_video_size = 50 * 1024 * 1024  # 50MB
        
        # HTTP client for downloads
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.threads.net/",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            }
        )
    
    def _get_media_path(self, post_id: str, index: int, extension: Optional[str] = None) -> Path:
        """
        Get filesystem path for media file.
        
        Args:
            post_id: Post ID
            index: Media index (0-based)
            extension: File extension (e.g., 'jpg', 'png'). If None, will be detected.
        
        Returns:
            Path object for media file
        """
        # Sanitize post_id to prevent path traversal
        safe_post_id = self._sanitize_path_component(post_id)
        
        # Create post directory
        post_dir = self.media_dir / safe_post_id
        post_dir.mkdir(exist_ok=True, mode=0o755)
        
        # Build filename
        if extension:
            filename = f"{index}.{extension}"
        else:
            filename = str(index)
        
        return post_dir / filename
    
    def _get_avatar_path(self, user_id: str, extension: Optional[str] = None) -> Path:
        """
        Get filesystem path for avatar file.
        
        Args:
            user_id: User ID
            extension: File extension. If None, will be detected.
        
        Returns:
            Path object for avatar file
        """
        # Sanitize user_id to prevent path traversal
        safe_user_id = self._sanitize_path_component(user_id)
        
        # Create avatars directory
        avatars_dir = self.media_dir / "avatars"
        avatars_dir.mkdir(exist_ok=True, mode=0o755)
        
        # Build filename
        if extension:
            filename = f"{safe_user_id}.{extension}"
        else:
            filename = safe_user_id
        
        return avatars_dir / filename
    
    def _sanitize_path_component(self, component: str) -> str:
        """
        Sanitize path component to prevent directory traversal.
        
        Args:
            component: Path component to sanitize
        
        Returns:
            Sanitized path component
        """
        # Remove any path separators
        sanitized = component.replace("/", "_").replace("\\", "_")
        # Remove any other dangerous characters
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in "._-")
        # Limit length
        sanitized = sanitized[:255]
        return sanitized
    
    def _detect_extension_from_url(self, url: str) -> str:
        """
        Detect file extension from URL.
        
        Args:
            url: Media URL
        
        Returns:
            File extension (e.g., 'jpg', 'png', 'mp4')
        """
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Check common image extensions
        for ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            if f'.{ext}' in path:
                return ext
        
        # Check video extensions
        for ext in ['mp4', 'mov', 'webm']:
            if f'.{ext}' in path:
                return ext
        
        # Default to jpg for images
        return 'jpg'
    
    def _detect_content_type(self, url: str, response_headers: Optional[dict] = None) -> Tuple[str, str]:
        """
        Detect content type and extension from URL or response headers.
        
        Args:
            url: Media URL
            response_headers: Optional response headers from download
        
        Returns:
            Tuple of (content_type, extension)
        """
        # Check response headers first
        if response_headers:
            content_type = response_headers.get('content-type', '')
            if 'image' in content_type:
                if 'jpeg' in content_type or 'jpg' in content_type:
                    return ('image/jpeg', 'jpg')
                elif 'png' in content_type:
                    return ('image/png', 'png')
                elif 'gif' in content_type:
                    return ('image/gif', 'gif')
                elif 'webp' in content_type:
                    return ('image/webp', 'webp')
                else:
                    return ('image/jpeg', 'jpg')
            elif 'video' in content_type:
                if 'mp4' in content_type:
                    return ('video/mp4', 'mp4')
                elif 'webm' in content_type:
                    return ('video/webm', 'webm')
                else:
                    return ('video/mp4', 'mp4')
        
        # Fallback to URL detection
        extension = self._detect_extension_from_url(url)
        
        content_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'mp4': 'video/mp4',
            'mov': 'video/mp4',
            'webm': 'video/webm',
        }
        
        content_type = content_type_map.get(extension, 'image/jpeg')
        return (content_type, extension)
    
    async def get_media_url(self, post_id: str, index: int) -> Optional[str]:
        """
        Get media URL from database.
        
        Args:
            post_id: Post ID
            index: Media index (0-based)
        
        Returns:
            Media URL or None if not found
        """
        try:
            # Query database for media_urls
            result = self.feed_storage.get_feed_items(
                post_id=post_id,
                limit=1
            )
            
            items = result.get("items", [])
            if not items:
                self.logger.log_step(
                    step="GET_MEDIA_URL",
                    result="NOT_FOUND",
                    post_id=post_id,
                    index=index
                )
                return None
            
            item = items[0]
            media_urls = item.get("media_urls", [])
            
            if not isinstance(media_urls, list):
                self.logger.log_step(
                    step="GET_MEDIA_URL",
                    result="ERROR",
                    error="media_urls is not a list",
                    post_id=post_id,
                    index=index
                )
                return None
            
            if index < 0 or index >= len(media_urls):
                self.logger.log_step(
                    step="GET_MEDIA_URL",
                    result="INDEX_OUT_OF_RANGE",
                    post_id=post_id,
                    index=index,
                    media_count=len(media_urls)
                )
                return None
            
            url = media_urls[index]
            return url
            
        except Exception as e:
            self.logger.log_step(
                step="GET_MEDIA_URL",
                result="ERROR",
                error=str(e),
                post_id=post_id,
                index=index
            )
            return None
    
    async def get_avatar_url(self, user_id: str) -> Optional[str]:
        """
        Get avatar URL from database.
        
        Args:
            user_id: User ID
        
        Returns:
            Avatar URL or None if not found
        """
        try:
            # Query database for user_avatar_url
            result = self.feed_storage.get_feed_items(
                limit=100  # Get recent items
            )
            
            items = result.get("items", [])
            for item in items:
                if item.get("user_id") == user_id:
                    avatar_url = item.get("user_avatar_url")
                    if avatar_url:
                        return avatar_url
            
            self.logger.log_step(
                step="GET_AVATAR_URL",
                result="NOT_FOUND",
                user_id=user_id
            )
            return None
            
        except Exception as e:
            self.logger.log_step(
                step="GET_AVATAR_URL",
                result="ERROR",
                error=str(e),
                user_id=user_id
            )
            return None
    
    async def download_media(self, post_id: str, index: int, cdn_url: str) -> Optional[Path]:
        """
        Download media from CDN and save to filesystem.
        
        Args:
            post_id: Post ID
            index: Media index (0-based)
            cdn_url: CDN URL to download from
        
        Returns:
            Path to downloaded file or None if download failed
        """
        try:
            self.logger.log_step(
                step="DOWNLOAD_MEDIA_START",
                result="IN_PROGRESS",
                post_id=post_id,
                index=index,
                url_length=len(cdn_url)
            )
            
            # Download media
            response = await self.client.get(cdn_url)
            response.raise_for_status()
            
            # Check content length
            content_length = response.headers.get('content-length')
            if content_length:
                size = int(content_length)
                max_size = self.max_video_size if 'video' in response.headers.get('content-type', '') else self.max_image_size
                if size > max_size:
                    self.logger.log_step(
                        step="DOWNLOAD_MEDIA",
                        result="ERROR",
                        error=f"File too large: {size} bytes",
                        post_id=post_id,
                        index=index
                    )
                    return None
            
            # Detect content type and extension
            content_type, extension = self._detect_content_type(cdn_url, dict(response.headers))
            
            # Get file path
            file_path = self._get_media_path(post_id, index, extension)
            
            # Save to filesystem
            file_path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Set file permissions
            os.chmod(file_path, 0o644)
            
            self.logger.log_step(
                step="DOWNLOAD_MEDIA",
                result="SUCCESS",
                post_id=post_id,
                index=index,
                file_path=str(file_path),
                content_type=content_type,
                size=len(response.content)
            )
            
            return file_path
            
        except httpx.HTTPStatusError as e:
            self.logger.log_step(
                step="DOWNLOAD_MEDIA",
                result="HTTP_ERROR",
                error=f"HTTP {e.response.status_code}",
                post_id=post_id,
                index=index,
                url_length=len(cdn_url)
            )
            return None
        except httpx.TimeoutException:
            self.logger.log_step(
                step="DOWNLOAD_MEDIA",
                result="TIMEOUT",
                post_id=post_id,
                index=index
            )
            return None
        except Exception as e:
            self.logger.log_step(
                step="DOWNLOAD_MEDIA",
                result="ERROR",
                error=str(e),
                post_id=post_id,
                index=index
            )
            return None
    
    async def download_avatar(self, user_id: str, cdn_url: str) -> Optional[Path]:
        """
        Download avatar from CDN and save to filesystem.
        
        Args:
            user_id: User ID
            cdn_url: CDN URL to download from
        
        Returns:
            Path to downloaded file or None if download failed
        """
        try:
            self.logger.log_step(
                step="DOWNLOAD_AVATAR_START",
                result="IN_PROGRESS",
                user_id=user_id,
                url_length=len(cdn_url)
            )
            
            # Download avatar
            response = await self.client.get(cdn_url)
            response.raise_for_status()
            
            # Check content length
            content_length = response.headers.get('content-length')
            if content_length:
                size = int(content_length)
                if size > self.max_image_size:
                    self.logger.log_step(
                        step="DOWNLOAD_AVATAR",
                        result="ERROR",
                        error=f"File too large: {size} bytes",
                        user_id=user_id
                    )
                    return None
            
            # Detect content type and extension
            content_type, extension = self._detect_content_type(cdn_url, dict(response.headers))
            
            # Get file path
            file_path = self._get_avatar_path(user_id, extension)
            
            # Save to filesystem
            file_path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Set file permissions
            os.chmod(file_path, 0o644)
            
            self.logger.log_step(
                step="DOWNLOAD_AVATAR",
                result="SUCCESS",
                user_id=user_id,
                file_path=str(file_path),
                content_type=content_type,
                size=len(response.content)
            )
            
            return file_path
            
        except httpx.HTTPStatusError as e:
            self.logger.log_step(
                step="DOWNLOAD_AVATAR",
                result="HTTP_ERROR",
                error=f"HTTP {e.response.status_code}",
                user_id=user_id
            )
            return None
        except httpx.TimeoutException:
            self.logger.log_step(
                step="DOWNLOAD_AVATAR",
                result="TIMEOUT",
                user_id=user_id
            )
            return None
        except Exception as e:
            self.logger.log_step(
                step="DOWNLOAD_AVATAR",
                result="ERROR",
                error=str(e),
                user_id=user_id
            )
            return None
    
    def _get_resized_path(
        self,
        post_id: str,
        index: int,
        width: Optional[int],
        height: Optional[int]
    ) -> Optional[Path]:
        """
        Get path for resized image.
        
        Args:
            post_id: Post ID
            index: Media index
            width: Width in pixels
            height: Height in pixels
        
        Returns:
            Path to resized image or None if original not found
        """
        # Get original path to determine extension
        original_path = None
        for ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            test_path = self._get_media_path(post_id, index, ext)
            if test_path.exists():
                original_path = test_path
                break
        
        if not original_path:
            return None
        
        # Build resized filename: {index}_w{width}_h{height}.{ext}
        width_str = f"w{width}" if width else ""
        height_str = f"h{height}" if height else ""
        size_suffix = f"_{width_str}_{height_str}".strip('_')
        
        resized_filename = f"{index}_{size_suffix}{original_path.suffix}"
        return original_path.parent / resized_filename
    
    async def _resize_image(
        self,
        image_path: Path,
        post_id: str,
        index: int,
        width: Optional[int],
        height: Optional[int]
    ) -> Optional[Path]:
        """
        Resize image using Pillow and cache result.
        
        Args:
            image_path: Path to original image
            post_id: Post ID
            index: Media index
            width: Target width (pixels)
            height: Target height (pixels)
        
        Returns:
            Path to resized image or None if failed
        """
        try:
            # Try to import Pillow
            try:
                from PIL import Image
            except ImportError:
                self.logger.log_step(
                    step="RESIZE_IMAGE",
                    result="ERROR",
                    error="Pillow not installed. Install with: pip install Pillow",
                    post_id=post_id,
                    index=index
                )
                return None
            
            # Get resized path
            resized_path = self._get_resized_path(post_id, index, width, height)
            if not resized_path:
                return None
            
            # Skip if resized version already exists
            if resized_path.exists():
                return resized_path
            
            # Open and resize image
            with Image.open(image_path) as img:
                # Get original dimensions
                orig_width, orig_height = img.size
                
                # Calculate target dimensions maintaining aspect ratio
                if width and height:
                    # Both specified - maintain aspect ratio, fit within bounds
                    ratio = min(width / orig_width, height / orig_height)
                    target_width = int(orig_width * ratio)
                    target_height = int(orig_height * ratio)
                elif width:
                    # Only width specified
                    ratio = width / orig_width
                    target_width = width
                    target_height = int(orig_height * ratio)
                elif height:
                    # Only height specified
                    ratio = height / orig_height
                    target_width = int(orig_width * ratio)
                    target_height = height
                else:
                    # No resize needed
                    return None
                
                # Don't upscale - only resize if smaller
                if target_width >= orig_width and target_height >= orig_height:
                    return None
                
                # Resize image
                resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Save resized image
                resized_path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
                
                # Determine format and save
                if image_path.suffix.lower() in ['.jpg', '.jpeg']:
                    resized_img.save(resized_path, 'JPEG', quality=85, optimize=True)
                elif image_path.suffix.lower() == '.png':
                    resized_img.save(resized_path, 'PNG', optimize=True)
                elif image_path.suffix.lower() == '.webp':
                    resized_img.save(resized_path, 'WEBP', quality=85, method=6)
                else:
                    # Default to JPEG
                    resized_path = resized_path.with_suffix('.jpg')
                    resized_img.save(resized_path, 'JPEG', quality=85, optimize=True)
                
                # Set file permissions
                os.chmod(resized_path, 0o644)
                
                self.logger.log_step(
                    step="RESIZE_IMAGE",
                    result="SUCCESS",
                    post_id=post_id,
                    index=index,
                    original_size=f"{orig_width}x{orig_height}",
                    resized_size=f"{target_width}x{target_height}",
                    file_path=str(resized_path)
                )
                
                return resized_path
                
        except Exception as e:
            self.logger.log_step(
                step="RESIZE_IMAGE",
                result="ERROR",
                error=str(e),
                post_id=post_id,
                index=index
            )
            return None
    
    async def serve_media(
        self,
        post_id: str,
        index: int,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> StreamingResponse:
        """
        Serve media file, downloading if necessary.
        
        Args:
            post_id: Post ID
            index: Media index (0-based)
            width: Optional width for thumbnail (pixels)
            height: Optional height for thumbnail (pixels)
        
        Returns:
            StreamingResponse with media file
        """
        # Validate inputs
        if not post_id or not isinstance(post_id, str):
            from backend.app.core.exceptions import ValidationError
            raise ValidationError("Invalid post_id")
        
        if not isinstance(index, int) or index < 0:
            from backend.app.core.exceptions import ValidationError
            raise ValidationError("Invalid index")
        
        # Get media URL from database
        cdn_url = await self.get_media_url(post_id, index)
        if not cdn_url:
            from backend.app.core.exceptions import NotFoundError
            raise NotFoundError(f"Media not found for post_id={post_id}, index={index}")
        
        # Check if resized version exists (if width/height provided)
        resized_path = None
        if width or height:
            resized_path = self._get_resized_path(post_id, index, width, height)
            if resized_path and resized_path.exists():
                content_type, _ = self._detect_content_type(str(resized_path))
                return FileResponse(
                    path=resized_path,
                    media_type=content_type,
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET',
                        'Access-Control-Allow-Headers': '*',
                        'Cache-Control': 'public, max-age=3600',
                    }
                )
        
        # Check if media is cached
        # Try common extensions
        cached_path = None
        for ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'webm']:
            test_path = self._get_media_path(post_id, index, ext)
            if test_path.exists():
                cached_path = test_path
                break
        
        # If not cached, download
        if not cached_path:
            cached_path = await self.download_media(post_id, index, cdn_url)
            if not cached_path:
                from backend.app.core.exceptions import InternalError
                raise InternalError("Failed to download media")
        
        # If width/height provided and it's an image, resize and cache
        if (width or height) and cached_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            resized_path = await self._resize_image(cached_path, post_id, index, width, height)
            if resized_path:
                content_type, _ = self._detect_content_type(str(resized_path))
                return FileResponse(
                    path=resized_path,
                    media_type=content_type,
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET',
                        'Access-Control-Allow-Headers': '*',
                        'Cache-Control': 'public, max-age=3600',
                    }
                )
        
        # Serve original file
        content_type, _ = self._detect_content_type(str(cached_path))
        return FileResponse(
            path=cached_path,
            media_type=content_type,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': '*',
                'Cache-Control': 'public, max-age=3600',
            }
        )
    
    def _get_resized_avatar_path(
        self,
        user_id: str,
        width: Optional[int],
        height: Optional[int]
    ) -> Optional[Path]:
        """
        Get path for resized avatar.
        
        Args:
            user_id: User ID
            width: Width in pixels
            height: Height in pixels
        
        Returns:
            Path to resized avatar or None if original not found
        """
        # Get original path to determine extension
        original_path = None
        for ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            test_path = self._get_avatar_path(user_id, ext)
            if test_path.exists():
                original_path = test_path
                break
        
        if not original_path:
            return None
        
        # Build resized filename: {user_id}_w{width}_h{height}.{ext}
        width_str = f"w{width}" if width else ""
        height_str = f"h{height}" if height else ""
        size_suffix = f"_{width_str}_{height_str}".strip('_')
        
        resized_filename = f"{self._sanitize_path_component(user_id)}_{size_suffix}{original_path.suffix}"
        return original_path.parent / resized_filename
    
    async def _resize_avatar(
        self,
        avatar_path: Path,
        user_id: str,
        width: Optional[int],
        height: Optional[int]
    ) -> Optional[Path]:
        """
        Resize avatar image using Pillow and cache result.
        
        Args:
            avatar_path: Path to original avatar
            user_id: User ID
            width: Target width (pixels)
            height: Target height (pixels)
        
        Returns:
            Path to resized avatar or None if failed
        """
        try:
            # Try to import Pillow
            try:
                from PIL import Image
            except ImportError:
                self.logger.log_step(
                    step="RESIZE_AVATAR",
                    result="ERROR",
                    error="Pillow not installed. Install with: pip install Pillow",
                    user_id=user_id
                )
                return None
            
            # Get resized path
            resized_path = self._get_resized_avatar_path(user_id, width, height)
            if not resized_path:
                return None
            
            # Skip if resized version already exists
            if resized_path.exists():
                return resized_path
            
            # Open and resize image
            with Image.open(avatar_path) as img:
                # Get original dimensions
                orig_width, orig_height = img.size
                
                # Calculate target dimensions maintaining aspect ratio
                if width and height:
                    # Both specified - maintain aspect ratio, fit within bounds
                    ratio = min(width / orig_width, height / orig_height)
                    target_width = int(orig_width * ratio)
                    target_height = int(orig_height * ratio)
                elif width:
                    # Only width specified
                    ratio = width / orig_width
                    target_width = width
                    target_height = int(orig_height * ratio)
                elif height:
                    # Only height specified
                    ratio = height / orig_height
                    target_width = int(orig_width * ratio)
                    target_height = height
                else:
                    # No resize needed
                    return None
                
                # Don't upscale - only resize if smaller
                if target_width >= orig_width and target_height >= orig_height:
                    return None
                
                # Resize image (use LANCZOS for better quality)
                resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Save resized image
                resized_path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
                
                # Determine format and save
                if avatar_path.suffix.lower() in ['.jpg', '.jpeg']:
                    resized_img.save(resized_path, 'JPEG', quality=85, optimize=True)
                elif avatar_path.suffix.lower() == '.png':
                    resized_img.save(resized_path, 'PNG', optimize=True)
                elif avatar_path.suffix.lower() == '.webp':
                    resized_img.save(resized_path, 'WEBP', quality=85, method=6)
                else:
                    # Default to JPEG
                    resized_path = resized_path.with_suffix('.jpg')
                    resized_img.save(resized_path, 'JPEG', quality=85, optimize=True)
                
                # Set file permissions
                os.chmod(resized_path, 0o644)
                
                self.logger.log_step(
                    step="RESIZE_AVATAR",
                    result="SUCCESS",
                    user_id=user_id,
                    original_size=f"{orig_width}x{orig_height}",
                    resized_size=f"{target_width}x{target_height}",
                    file_path=str(resized_path)
                )
                
                return resized_path
                
        except Exception as e:
            self.logger.log_step(
                step="RESIZE_AVATAR",
                result="ERROR",
                error=str(e),
                user_id=user_id
            )
            return None
    
    async def serve_avatar(
        self,
        user_id: str,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> StreamingResponse:
        """
        Serve avatar file, downloading if necessary.
        
        Args:
            user_id: User ID
            width: Optional width for thumbnail (pixels)
            height: Optional height for thumbnail (pixels)
        
        Returns:
            StreamingResponse with avatar file
        """
        # Validate inputs
        if not user_id or not isinstance(user_id, str):
            from backend.app.core.exceptions import ValidationError
            raise ValidationError("Invalid user_id")
        
        # Get avatar URL from database
        cdn_url = await self.get_avatar_url(user_id)
        if not cdn_url:
            from backend.app.core.exceptions import NotFoundError
            raise NotFoundError(f"Avatar not found for user_id={user_id}")
        
        # Check if resized version exists (if width/height provided)
        resized_path = None
        if width or height:
            resized_path = self._get_resized_avatar_path(user_id, width, height)
            if resized_path and resized_path.exists():
                content_type, _ = self._detect_content_type(str(resized_path))
                return FileResponse(
                    path=resized_path,
                    media_type=content_type,
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET',
                        'Access-Control-Allow-Headers': '*',
                        'Cache-Control': 'public, max-age=3600',
                    }
                )
        
        # Check if avatar is cached
        # Try common extensions
        cached_path = None
        for ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            test_path = self._get_avatar_path(user_id, ext)
            if test_path.exists():
                cached_path = test_path
                break
        
        # If not cached, download
        if not cached_path:
            cached_path = await self.download_avatar(user_id, cdn_url)
            if not cached_path:
                from backend.app.core.exceptions import InternalError
                raise InternalError("Failed to download avatar")
        
        # If width/height provided, resize and cache
        if (width or height) and cached_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            resized_path = await self._resize_avatar(cached_path, user_id, width, height)
            if resized_path:
                content_type, _ = self._detect_content_type(str(resized_path))
                return FileResponse(
                    path=resized_path,
                    media_type=content_type,
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET',
                        'Access-Control-Allow-Headers': '*',
                        'Cache-Control': 'public, max-age=3600',
                    }
                )
        
        # Serve original file
        content_type, _ = self._detect_content_type(str(cached_path))
        return FileResponse(
            path=cached_path,
            media_type=content_type,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': '*',
                'Cache-Control': 'public, max-age=3600',
            }
        )
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
