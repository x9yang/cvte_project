from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..models.database import get_db
from ..models.models import ContractType
from ..schemas.schemas import ContractTypeCreate, ContractTypeResponse

router = APIRouter(prefix="/types", tags=["合同类型"])


@router.get("", response_model=List[ContractTypeResponse])
def list_types(db: Session = Depends(get_db)):
    """获取所有合同类型"""
    return db.query(ContractType).all()


@router.post("", response_model=ContractTypeResponse)
def create_type(type_data: ContractTypeCreate, db: Session = Depends(get_db)):
    """新增合同类型"""
    existing = db.query(ContractType).filter(ContractType.name == type_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="类型已存在")

    db_type = ContractType(
        name=type_data.name,
        description=type_data.description,
    )
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type


@router.delete("/{type_id}")
def delete_type(type_id: int, db: Session = Depends(get_db)):
    """删除合同类型"""
    db_type = db.query(ContractType).filter(ContractType.id == type_id).first()
    if not db_type:
        raise HTTPException(status_code=404, detail="类型不存在")

    db.delete(db_type)
    db.commit()
    return {"message": "删除成功"}
