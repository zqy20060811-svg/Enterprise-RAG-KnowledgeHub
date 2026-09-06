"""
FastAPI 应用入口
注册路由、中间件、全局异常处理
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.exceptions import BizException
from api import document, knowledge_base, retrieval, chat

# ===================== 应用初始化 =====================
app = FastAPI(
    title="企业级智能知识库平台",
    description="基于 RAG 的企业知识库问答系统：文档解析、混合检索、重排序、流式生成",
    version="2.0.0",
)

# ===================== 跨域配置 =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== 注册路由 =====================
app.include_router(document.router)
app.include_router(knowledge_base.router)
app.include_router(retrieval.router)
app.include_router(chat.router)


# ===================== 全局异常处理 =====================
@app.exception_handler(BizException)
async def biz_exception_handler(request: Request, exc: BizException):
    return JSONResponse(
        status_code=200,
        content={"code": exc.code, "msg": exc.msg, "data": None},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=200,
        content={"code": exc.status_code, "msg": exc.detail, "data": None},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content={"code": 500, "msg": f"服务器内部错误：{str(exc)}", "data": None},
    )


# ===================== 健康检查 =====================
@app.get("/", summary="健康检查")
async def root():
    return {"code": 200, "msg": "企业级智能知识库平台运行正常", "data": None}
