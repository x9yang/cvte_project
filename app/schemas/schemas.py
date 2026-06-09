from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AssignmentInput(BaseModel):
    """分派请求输入 - 方式A: 结构化数据"""
    pages: Optional[int] = Field(None, description="合同页数")
    word_count: Optional[int] = Field(None, description="合同总字数")
    contract_type: Optional[str] = Field(None, description="合同类型")
    extra_info: Optional[str] = Field(None, description="额外信息，供Agent参考")


class AssignmentOutput(BaseModel):
    """分派结果输出"""
    recommended_staff: str = Field(..., description="推荐的法务人员姓名")
    staff_id: int = Field(..., description="人员ID")
    reason: str = Field(..., description="分派理由")
    confidence: float = Field(..., description="置信度 0-1")
    contract_type: str = Field(..., description="识别的合同类型")
    workload_summary: dict = Field(..., description="负载情况摘要")


class StaffBase(BaseModel):
    name: str = Field(..., description="姓名")


class StaffCreate(StaffBase):
    skill_tags: List[str] = Field(default=[], description="技能标签列表")


class StaffResponse(StaffBase):
    id: int
    skill_tags: List[str]
    current_todo_count: int
    weekly_assigned: int
    monthly_assigned: int

    class Config:
        from_attributes = True


class ContractTypeBase(BaseModel):
    name: str = Field(..., description="合同类型名称")
    description: Optional[str] = Field(None, description="类型描述")


class ContractTypeCreate(ContractTypeBase):
    pass


class ContractTypeResponse(ContractTypeBase):
    id: int

    class Config:
        from_attributes = True


class AssignmentRecordResponse(BaseModel):
    id: int
    contract_info: Optional[dict]
    contract_type: str
    staff_name: str
    staff_id: int
    reason: str
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True


class StaffWorkloadUpdate(BaseModel):
    """更新人员负载"""
    current_todo_count: Optional[int] = None
    weekly_assigned: Optional[int] = None
    monthly_assigned: Optional[int] = None
