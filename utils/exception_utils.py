"""
Module: utils/exception_utils.py

Utility functions cho safe exception handling.

Centralized logic để format exceptions an toàn,
tránh lỗi khi exception có __cause__ hoặc __context__ 
reference đến exceptions không tồn tại (ví dụ: ExcelFileError).
"""



def safe_get_exception_type_name(exception: Exception) -> str:
    """
    Lấy tên exception type một cách an toàn.
    
    Tránh lỗi khi exception có __cause__ hoặc __context__ 
    reference đến exceptions không tồn tại.
    
    Args:
        exception: Exception object
    
    Returns:
        Tên exception type hoặc "Exception" nếu không thể lấy được
    
    Example:
        >>> try:
        ...     raise ValueError("test")
        ... except Exception as e:
        ...     safe_get_exception_type_name(e)
        'ValueError'
    """
    try:
        return type(exception).__name__
    except AttributeError:
        # Fallback nếu không thể lấy __name__
        try:
            return str(type(exception))
        except Exception:
            return "Unknown"
    except Exception:
        # Catch-all để tránh mọi lỗi (bao gồm ExcelFileError reference)
        return "Exception"


def safe_get_exception_message(exception: Exception, max_length: int = 500) -> str:
    """
    Lấy exception message một cách an toàn.
    
    Tránh trigger chain reaction khi exception có reference 
    đến exceptions không tồn tại trong exception chain.
    
    Args:
        exception: Exception object
        max_length: Độ dài tối đa của message (truncate nếu quá dài)
    
    Returns:
        Exception message hoặc fallback message nếu không thể lấy được
    
    Example:
        >>> try:
        ...     raise ValueError("test error")
        ... except Exception as e:
        ...     safe_get_exception_message(e)
        'test error'
    """
    try:
        message = str(exception)
        # Truncate nếu quá dài
        if len(message) > max_length:
            message = message[:max_length] + "..."
        return message
    except Exception:
        # Nếu str(e) fails, có thể do exception chain reference đến ExcelFileError
        return "Error occurred but message unavailable"


def format_exception(exception: Exception, max_message_length: int = 500) -> str:
    """
    Format exception thành chuỗi "Type: message".
    
    Args:
        exception: Exception object
        max_message_length: Độ dài tối đa của message
    
    Returns:
        Formatted string: "Type: message"
    
    Example:
        >>> try:
        ...     raise ValueError("test error")
        ... except Exception as e:
        ...     format_exception(e)
        'ValueError: test error'
    """
    type_name = safe_get_exception_type_name(exception)
    message = safe_get_exception_message(exception, max_message_length)
    return f"{type_name}: {message}"

