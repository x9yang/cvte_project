from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from ..models.database import get_db
from ..models.models import AssignmentRecord, Staff
from ..schemas.schemas import AssignmentInput, AssignmentOutput
from ..agent.graph import AssignmentAgent
from ..parser.contract_parser import ContractParser

router = APIRouter(tags=["分派"])


@router.post("/assign")
async def assign_contract(
    input_data: AssignmentInput,
    db: Session = Depends(get_db),
):
    """
    合同分派接口 (方式A: JSON body 传入结构化数据)
    """
    try:
        agent_input = input_data.model_dump()

        # 执行Agent分派
        agent = AssignmentAgent(db)
        result = agent.run(agent_input)

        # 保存记录
        record = AssignmentRecord(
            contract_info={
                "pages": agent_input.get("pages"),
                "word_count": agent_input.get("word_count"),
            },
            contract_type=result["contract_type"],
            staff_id=result["staff_id"],
            staff_name=result["recommended_staff"],
            reason=result["reason"],
            confidence=result["confidence"],
        )
        db.add(record)

        # 更新人员负载计数
        staff = db.query(Staff).filter(Staff.id == result["staff_id"]).first()
        if staff:
            staff.current_todo_count += 1
            staff.weekly_assigned += 1
            staff.monthly_assigned += 1

        db.commit()

        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/assign/upload")
async def assign_by_file(
    file: UploadFile = File(...),
    extra_info: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    通过文件分派合同 (方式B: 上传文件)
    """
    try:
        content = await file.read()
        parsed = ContractParser.parse(file.filename, content)

        if not parsed:
            return JSONResponse(status_code=400, content={"error": "不支持的文件格式"})

        agent_input = {
            "pages": parsed["pages"],
            "word_count": parsed["word_count"],
            "text_content": parsed["text_content"],
            "extra_info": extra_info,
        }

        # 执行Agent分派
        agent = AssignmentAgent(db)
        result = agent.run(agent_input)

        # 添加解析信息到返回结果
        result["parse_info"] = {
            "filename": file.filename,
            "pages": parsed["pages"],
            "word_count": parsed["word_count"],
            "text_preview": parsed["text_content"][:500]
        }

        # 保存记录
        record = AssignmentRecord(
            contract_info={
                "pages": agent_input.get("pages"),
                "word_count": agent_input.get("word_count"),
                "filename": file.filename,
            },
            contract_type=result["contract_type"],
            staff_id=result["staff_id"],
            staff_name=result["recommended_staff"],
            reason=result["reason"],
            confidence=result["confidence"],
        )
        db.add(record)

        # 更新人员负载计数
        staff = db.query(Staff).filter(Staff.id == result["staff_id"]).first()
        if staff:
            staff.current_todo_count += 1
            staff.weekly_assigned += 1
            staff.monthly_assigned += 1

        db.commit()

        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
async def assign_by_file(
    file: UploadFile = File(...),
    extra_info: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    通过文件分派合同 (方式B: 上传文件)
    """
    try:
        content = await file.read()
        parsed = ContractParser.parse(file.filename, content)

        if not parsed:
            return JSONResponse(status_code=400, content={"error": "不支持的文件格式"})

        agent_input = {
            "pages": parsed["pages"],
            "word_count": parsed["word_count"],
            "text_content": parsed["text_content"],
            "extra_info": extra_info,
        }

        # 执行Agent分派
        agent = AssignmentAgent(db)
        result = agent.run(agent_input)

        # 保存记录
        record = AssignmentRecord(
            contract_info={
                "pages": agent_input.get("pages"),
                "word_count": agent_input.get("word_count"),
                "filename": file.filename,
            },
            contract_type=result["contract_type"],
            staff_id=result["staff_id"],
            staff_name=result["recommended_staff"],
            reason=result["reason"],
            confidence=result["confidence"],
        )
        db.add(record)

        # 更新人员负载计数
        staff = db.query(Staff).filter(Staff.id == result["staff_id"]).first()
        if staff:
            staff.current_todo_count += 1
            staff.weekly_assigned += 1
            staff.monthly_assigned += 1

        db.commit()

        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
