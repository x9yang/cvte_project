from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from ..models.database import get_db
from ..models.models import AssignmentRecord
from ..schemas.schemas import AssignmentRecordResponse

router = APIRouter(prefix="/history", tags=["历史记录"])


@router.get("", response_model=List[AssignmentRecordResponse])
def list_history(
    limit: int = Query(20, ge=1, le=100),
    staff_id: int = Query(None, description="按人员筛选"),
    contract_type: str = Query(None, description="按合同类型筛选"),
    db: Session = Depends(get_db),
):
    """查询分派历史"""
    query = db.query(AssignmentRecord).order_by(desc(AssignmentRecord.created_at))

    if staff_id:
        query = query.filter(AssignmentRecord.staff_id == staff_id)
    if contract_type:
        query = query.filter(AssignmentRecord.contract_type == contract_type)

    return query.limit(limit).all()


@router.delete("/clear")
def clear_history(db: Session = Depends(get_db)):
    """清空所有分派历史"""
    count = db.query(AssignmentRecord).delete()
    db.commit()
    return {"message": f"已清空 {count} 条历史记录"}
