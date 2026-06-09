from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class AgentState(BaseModel):
    """Agent状态定义"""
    # 输入
    pages: Optional[int] = None
    word_count: Optional[int] = None
    contract_type: Optional[str] = None
    text_content: Optional[str] = None
    extra_info: Optional[str] = None

    # 中间状态
    identified_type: Optional[str] = None
    candidates: List[Dict[str, Any]] = []
    workload_analysis: Optional[str] = None
    capability_analysis: Optional[str] = None

    # 输出
    recommended_staff: Optional[str] = None
    staff_id: Optional[int] = None
    reason: Optional[str] = None
    confidence: Optional[float] = None
