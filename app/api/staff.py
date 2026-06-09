from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import List

from ..models.database import get_db
from ..models.models import Staff
from ..schemas.schemas import StaffCreate, StaffResponse, StaffWorkloadUpdate

router = APIRouter(prefix="/staff", tags=["人员管理"])


class SkillUpdate:
    def __init__(self, skill: str):
        self.skill = skill


@router.get("", response_model=List[StaffResponse])
def list_staff(db: Session = Depends(get_db)):
    """获取所有法务人员"""
    return db.query(Staff).all()


@router.post("", response_model=StaffResponse)
def create_staff(staff: StaffCreate, db: Session = Depends(get_db)):
    """添加法务人员"""
    existing = db.query(Staff).filter(Staff.name == staff.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="人员已存在")

    db_staff = Staff(
        name=staff.name,
        skill_tags=staff.skill_tags,
    )
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff


@router.put("/{staff_id}", response_model=StaffResponse)
def update_staff(staff_id: int, staff: StaffCreate, db: Session = Depends(get_db)):
    """更新人员技能标签"""
    db_staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not db_staff:
        raise HTTPException(status_code=404, detail="人员不存在")

    db_staff.name = staff.name
    db_staff.skill_tags = staff.skill_tags
    db.commit()
    db.refresh(db_staff)
    return db_staff


@router.patch("/{staff_id}/workload", response_model=StaffResponse)
def update_workload(
    staff_id: int,
    workload: StaffWorkloadUpdate,
    db: Session = Depends(get_db),
):
    """更新人员负载"""
    db_staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not db_staff:
        raise HTTPException(status_code=404, detail="人员不存在")

    if workload.current_todo_count is not None:
        db_staff.current_todo_count = workload.current_todo_count
    if workload.weekly_assigned is not None:
        db_staff.weekly_assigned = workload.weekly_assigned
    if workload.monthly_assigned is not None:
        db_staff.monthly_assigned = workload.monthly_assigned

    db.commit()
    db.refresh(db_staff)
    return db_staff


@router.delete("/{staff_id}")
def delete_staff(staff_id: int, db: Session = Depends(get_db)):
    """删除人员"""
    db_staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not db_staff:
        raise HTTPException(status_code=404, detail="人员不存在")

    db.delete(db_staff)
    db.commit()
    return {"message": "删除成功"}


@router.post("/reset-workload")
def reset_all_workload(db: Session = Depends(get_db)):
    """清空所有人员的任务量"""
    staff_list = db.query(Staff).all()
    for staff in staff_list:
        staff.current_todo_count = 0
        staff.weekly_assigned = 0
        staff.monthly_assigned = 0
    db.commit()
    return {"message": f"已清空 {len(staff_list)} 人的任务量"}


@router.post("/{staff_id}/skills")
def add_skill(staff_id: int, skill_data: dict, db: Session = Depends(get_db)):
    """添加技能"""
    db_staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not db_staff:
        raise HTTPException(status_code=404, detail="人员不存在")

    skill = skill_data.get("skill")
    if not skill:
        raise HTTPException(status_code=400, detail="技能名称不能为空")

    skills = list(db_staff.skill_tags or [])
    if skill in skills:
        raise HTTPException(status_code=400, detail="技能已存在")

    skills.append(skill)
    db_staff.skill_tags = skills
    flag_modified(db_staff, 'skill_tags')
    db.commit()
    db.refresh(db_staff)
    return db_staff


@router.delete("/{staff_id}/skills/{skill}")
def remove_skill(staff_id: int, skill: str, db: Session = Depends(get_db)):
    """删除技能"""
    db_staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not db_staff:
        raise HTTPException(status_code=404, detail="人员不存在")

    skills = list(db_staff.skill_tags or [])
    if skill not in skills:
        raise HTTPException(status_code=404, detail="技能不存在")

    skills.remove(skill)
    db_staff.skill_tags = skills
    flag_modified(db_staff, 'skill_tags')
    db.commit()
    db.refresh(db_staff)
    return db_staff
