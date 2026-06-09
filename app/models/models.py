from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from .database import Base


class Staff(Base):
    """法务人员表"""
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    skill_tags = Column(JSON, default=list)  # ["租赁合同", "购销合同"]
    current_todo_count = Column(Integer, default=0)
    weekly_assigned = Column(Integer, default=0)
    monthly_assigned = Column(Integer, default=0)


class ContractType(Base):
    """合同类型表"""
    __tablename__ = "contract_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)


class AssignmentRecord(Base):
    """分派记录表"""
    __tablename__ = "assignment_records"

    id = Column(Integer, primary_key=True, index=True)
    contract_info = Column(JSON, nullable=True)  # 合同元数据
    contract_type = Column(String, nullable=False)
    staff_id = Column(Integer, nullable=False)
    staff_name = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
