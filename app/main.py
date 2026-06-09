from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

# 清除代理环境变量（避免影响 API 调用）
for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(key, None)

# 加载 .env 文件
load_dotenv()

from .models.database import init_db, SessionLocal
from .models.models import ContractType, Staff
from .api import assign, staff, types, history


def seed_data():
    """初始化默认数据"""
    db = SessionLocal()

    # 初始化默认合同类型
    default_types = [
        ("租赁合同", "房屋、设备等租赁相关合同"),
        ("购销合同", "采购、销售相关合同"),
        ("筹建合同", "项目筹建、建设相关合同"),
        ("劳动合同", "员工劳动关系相关合同"),
        ("保密协议", "保密、竞业限制相关协议"),
        ("知识产权合同", "专利、商标、著作权相关合同"),
        ("其他", "未分类合同"),
    ]
    for name, desc in default_types:
        if not db.query(ContractType).filter(ContractType.name == name).first():
            db.add(ContractType(name=name, description=desc))

    # 初始化示例人员
    default_staff = [
        ("张三", ["租赁合同", "筹建合同"]),
        ("李四", ["购销合同", "知识产权合同"]),
        ("王五", ["劳动合同", "保密协议"]),
        ("赵六", ["租赁合同", "购销合同", "筹建合同"]),
    ]
    for name, skills in default_staff:
        if not db.query(Staff).filter(Staff.name == name).first():
            db.add(Staff(name=name, skill_tags=skills))

    db.commit()
    db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    init_db()
    seed_data()
    yield


app = FastAPI(
    title="法务合同分派智能体",
    description="基于AI Agent的合同智能分派系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 注册路由
app.include_router(assign.router)
app.include_router(staff.router)
app.include_router(types.router)
app.include_router(history.router)

# 静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )


@app.get("/")
def root():
    return FileResponse("static/index.html")


@app.get("/api")
def api_info():
    return {
        "message": "法务合同分派智能体 API",
        "docs": "/docs",
    }
