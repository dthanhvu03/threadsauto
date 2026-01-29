"""
Module: threads/behavior.py

Anti-detection behavior helpers cho Threads automation.
"""

# Standard library
import asyncio
import random

# Local
from threads.types import TEXT_CONTENT_EXPRESSION


class BehaviorHelper:
    """Helper class cho anti-detection behavior."""
    
    def __init__(self, logger):
        """
        Khởi tạo behavior helper.
        
        Args:
            logger: Instance structured logger
        """
        self.logger = logger
    
    async def human_like_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
        """
        Delay ngẫu nhiên để mô phỏng hành vi người dùng.
        
        Args:
            min_seconds: Thời gian delay tối thiểu (giây)
            max_seconds: Thời gian delay tối đa (giây)
        """
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def type_in_chunks(
        self,
        element,
        text: str,
        chunk_size: int = 4
    ) -> None:
        """
        Gõ text theo từng chunk với delay ngẫu nhiên (giống người dùng).
        
        Hỗ trợ cả contenteditable div (Lexical editor) và textarea.
        
        Args:
            element: Handle element Playwright
            text: Text cần gõ
            chunk_size: Số ký tự mỗi chunk (mặc định: 4)
        """
        self.logger.log_step(
            step="TYPE_CONTENT",
            result="IN_PROGRESS",
            content_length=len(text),
            note=f"Starting to type {len(text)} characters"
        )
        
        # Kiểm tra xem có phải Lexical editor không với error handling
        is_lexical = False
        try:
            is_lexical = await element.get_attribute("data-lexical-editor")
            is_lexical = bool(is_lexical)
        except Exception:
            # Default to False nếu không thể get attribute
            is_lexical = False
        
        # Đảm bảo element được focus trước khi type
        try:
            await element.focus()
            await asyncio.sleep(0.2)  # Chờ focus hoàn thành
        except (TimeoutError, RuntimeError) as e:
            self.logger.log_step(
                step="TYPE_CONTENT",
                result="WARNING",
                error=f"Focus failed: {type(e).__name__}: {str(e)}, trying to continue",
                error_type=type(e).__name__
            )
        except Exception as e:
            self.logger.log_step(
                step="TYPE_CONTENT",
                result="WARNING",
                error=f"Focus failed: {type(e).__name__}: {str(e)}, trying to continue",
                error_type=type(e).__name__
            )
        
        # Nếu text ngắn (< 20 chars), gõ trực tiếp không cần chunk
        if len(text) < 20:
            try:
                if is_lexical:
                    # Lexical editor: dùng fill
                    await element.fill(text)
                    self.logger.log_step(
                        step="TYPE_CONTENT",
                        result="SUCCESS",
                        method="fill",
                        content_length=len(text)
                    )
                else:
                    await element.type(text, delay=random.uniform(50, 150))
                    self.logger.log_step(
                        step="TYPE_CONTENT",
                        result="SUCCESS",
                        method="type",
                        content_length=len(text)
                    )
                return
            except (TimeoutError, RuntimeError) as e:
                self.logger.log_step(
                    step="TYPE_CONTENT",
                    result="WARNING",
                    error=f"Direct type failed: {type(e).__name__}: {str(e)}, trying chunks",
                    error_type=type(e).__name__
                )
                # Fallback: tiếp tục với chunks
            except Exception as e:
                self.logger.log_step(
                    step="TYPE_CONTENT",
                    result="WARNING",
                    error=f"Direct type failed: {type(e).__name__}: {str(e)}, trying chunks",
                    error_type=type(e).__name__
                )
                # Fallback: tiếp tục với chunks
        
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        typed_chars = 0
        
        for i, chunk in enumerate(chunks):
            try:
                # Cả Lexical editor và textarea đều dùng type với delay=0
                await element.type(chunk, delay=0, timeout=5000)
                typed_chars += len(chunk)
            except Exception as e:
                # Fallback: sử dụng evaluate để set text
                try:
                    current_text = await element.evaluate(TEXT_CONTENT_EXPRESSION)
                    # Escape single quotes trong chunk để tránh JavaScript syntax error
                    escaped_chunk = chunk.replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
                    escaped_current = (current_text or "").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
                    await element.evaluate(f"el => el.textContent = '{escaped_current}{escaped_chunk}'")
                    typed_chars += len(chunk)
                except Exception as eval_error:
                    # Nếu cả evaluate fail, skip chunk này
                    self.logger.log_step(
                        step="TYPE_CONTENT",
                        result="WARNING",
                        error=f"Chunk {i+1}/{len(chunks)} failed: {type(e).__name__}: {str(e)}, evaluate also failed: {type(eval_error).__name__}: {str(eval_error)}",
                        error_type=f"{type(e).__name__}, {type(eval_error).__name__}"
                    )
                    continue
            
            # Delay ngẫu nhiên giữa các chunk (30-100ms - giảm để nhanh hơn)
            await asyncio.sleep(random.uniform(0.03, 0.10))
        
        # Verify content đã được type (chỉ verify nếu dùng chunks, không verify nếu dùng direct type)
        if len(text) >= 20:
            try:
                await asyncio.sleep(0.3)  # Chờ content được render
                actual_text = await element.evaluate(TEXT_CONTENT_EXPRESSION)
                actual_length = len(actual_text.strip())
                expected_length = len(text)
                
                # Check nếu actual_length khác expected_length quá nhiều (>30%)
                # Có thể text không được type vào đúng hoặc có placeholder text
                if actual_length > 0:
                    length_diff = abs(actual_length - expected_length)
                    length_diff_percent = (length_diff / expected_length * 100) if expected_length > 0 else 0
                    
                    # Nếu sai lệch > 30%, có thể là placeholder text hoặc type không thành công
                    if length_diff_percent > 30:
                        self.logger.log_step(
                            step="TYPE_CONTENT",
                            result="WARNING",
                            typed_chars=typed_chars,
                            expected_length=expected_length,
                            actual_length=actual_length,
                            length_diff=length_diff,
                            length_diff_percent=round(length_diff_percent, 2),
                            actual_text_preview=actual_text[:50] if len(actual_text) > 50 else actual_text,
                            note=f"Content length mismatch ({length_diff_percent:.1f}% difference) - may not have been typed correctly"
                        )
                    else:
                        # SUCCESS: length match (sai lệch <= 30%)
                        self.logger.log_step(
                            step="TYPE_CONTENT",
                            result="SUCCESS",
                            typed_chars=typed_chars,
                            expected_length=expected_length,
                            actual_length=actual_length,
                            actual_text_preview=actual_text[:50] if len(actual_text) > 50 else actual_text,
                            note="Content typed successfully and verified"
                        )
                else:
                    self.logger.log_step(
                        step="TYPE_CONTENT",
                        result="WARNING",
                        typed_chars=typed_chars,
                        actual_length=0,
                        note="Content may not have been typed - input appears empty"
                    )
            except Exception as e:
                self.logger.log_step(
                    step="TYPE_CONTENT",
                    result="WARNING",
                    error=f"Could not verify typed content: {str(e)}",
                    error_type=type(e).__name__
                )
    
    async def click_with_offset(self, element) -> None:
        """
        Click element với offset ngẫu nhiên (không phải chính giữa).
        
        Args:
            element: Handle element Playwright
        """
        try:
            # Lấy bounding box với error handling
            try:
                box = await element.bounding_box()
            except Exception as e:
                self.logger.log_step(
                    step="CLICK_WITH_OFFSET",
                    result="WARNING",
                    error=f"Failed to get bounding box: {str(e)}, using direct click",
                    error_type=type(e).__name__
                )
                # Fallback to direct click
                try:
                    await element.click()
                except Exception as click_error:
                    self.logger.log_step(
                        step="CLICK_WITH_OFFSET",
                        result="ERROR",
                        error=f"Direct click also failed: {str(click_error)}",
                        error_type=type(click_error).__name__
                    )
                    raise
                return
            
            if not box:
                try:
                    await element.click()
                except Exception as click_error:
                    self.logger.log_step(
                        step="CLICK_WITH_OFFSET",
                        result="ERROR",
                        error=f"Direct click failed: {str(click_error)}",
                        error_type=type(click_error).__name__
                    )
                    raise
                return
            
            # Validate box có width và height
            width = box.get('width', 0)
            height = box.get('height', 0)
            
            # Offset ngẫu nhiên (-5 đến +5 pixels)
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            
            try:
                await element.click(
                    position={
                        'x': (width / 2) + offset_x,
                        'y': (height / 2) + offset_y
                    }
                )
            except Exception as e:
                self.logger.log_step(
                    step="CLICK_WITH_OFFSET",
                    result="WARNING",
                    error=f"Click with offset failed: {str(e)}, trying direct click",
                    error_type=type(e).__name__
                )
                # Fallback to direct click
                try:
                    await element.click()
                except Exception as click_error:
                    self.logger.log_step(
                        step="CLICK_WITH_OFFSET",
                        result="ERROR",
                        error=f"Direct click also failed: {str(click_error)}",
                        error_type=type(click_error).__name__
                    )
                    raise
        except Exception as e:
            self.logger.log_step(
                step="CLICK_WITH_OFFSET",
                result="ERROR",
                error=f"Failed to click with offset: {str(e)}",
                error_type=type(e).__name__
            )
            raise

