"""
Utility functions để tránh cảnh báo pylance
"""
from typing import Any


def safe_get_related_field(obj: Any, field_name: str) -> Any:
    """
    An truy cập vào các related fields để tránh cảnh báo pylance
    
    Args:
        obj: Đối tượng chứa related field
        field_name: Tên của related field
        
    Returns:
        RelatedManager hoặc None nếu không tồn tại
    """
    if hasattr(obj, field_name):
        return getattr(obj, field_name)
    return None 