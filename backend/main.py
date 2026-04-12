# 导入FastAPI核心类，用于创建Web应用、处理HTTP异常、接收文件上传
from fastapi import FastAPI, HTTPException, Request, File, UploadFile,Header,Depends
# 导入响应类：流式响应用于AI打字机输出，JSONResponse用于统一返回JSON格式数据
from fastapi.responses import StreamingResponse,JSONResponse
# 导入跨域中间件，解决前端页面访问后端接口的跨域问题
from fastapi.middleware.cors import CORSMiddleware
# 导入数据模型基类，用于定义接口请求参数的格式
from pydantic import BaseModel
# 导入字节流工具，用于处理文件二进制数据
from io import BytesIO
# 导入操作系统相关功能，用于文件路径、文件操作
import os
# 导入生成器类型注解，用于标注流式返回的数据类型
from typing import Generator
# 导入UUID工具，用于生成唯一的会话ID
import uuid

# 导入项目业务逻辑服务（RAG对话核心）
from rag import rag_service


# ===================== 应用初始化 =====================
# 创建FastAPI应用实例，设置接口文档的标题和版本号
app = FastAPI(
    title="个人知识库智能问答系统",
    version="1.0.0"
)

# ===================== 全局跨域配置 =====================
# 配置跨域中间件，允许所有来源、所有请求头、所有请求方法访问接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== 统一响应工具函数 =====================
# 成功响应：返回标准格式，包含状态码、提示信息、业务数据
def resp_success(data=None, msg="success", code=200):
    return {"code": code, "msg": msg, "data": data}

# 失败响应：统一错误返回格式，方便前端处理异常
def resp_error(msg="error", code=500, data=None):
    return {"code": code, "msg": msg, "data": data}

# ===================== 自定义业务异常 =====================
# 自定义异常类，用于主动抛出业务逻辑错误（如文件不存在、参数错误）
class BizException(Exception):
    def __init__(self, msg="业务错误", code=400):
        self.code = code  # 自定义业务状态码
        self.msg = msg    # 错误提示信息

# ===================== 全局异常捕获处理器 =====================
# 捕获自定义业务异常，统一返回错误格式
@app.exception_handler(BizException)
async def biz_exception_handler(request: Request, exc: BizException):
    return JSONResponse(
        status_code=200,
        content=resp_error(msg=exc.msg, code=exc.code)
    )

# 捕获FastAPI内置HTTP异常（如404、401、403）
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=200,
        content=resp_error(msg=exc.detail, code=exc.status_code)
    )

# 捕获所有未知系统异常，防止程序崩溃，返回友好提示
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content=resp_error(msg="服务器内部错误", code=500)
    )

# 自己设一个密码
API_TOKEN = "600123"

# 独立鉴权函数
def verify_token(token: str = Header(None)):
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="无权访问")
# ===================== 请求参数模型 =====================
# 定义对话接口的请求体格式，包含用户问题和可选的会话ID
class ChatRequest(BaseModel):
    prompt: str          # 用户输入的问题
    session_id: str = None  # 会话ID，用于上下文关联（可选）


# ===================== 核心业务接口 =====================
# 流式问答接口：接收用户问题，返回AI打字机式的回答
@app.post("/chat/stream", dependencies=[Depends(verify_token)])
async def chat_stream(req: ChatRequest):
    # 如果前端未传session_id，自动生成唯一ID
    session_id = req.session_id or str(uuid.uuid4())

    # 调用业务层方法，获取流式回答生成器
    gen = rag_service.ask_question_stream(
        prompt=req.prompt,
        session_id=session_id  # 把ID传进去
    )

    # 以文本流形式返回给前端，实现打字机效果11111111111111111111111111111111111111111111111111111111111111111111111
    return StreamingResponse(
        gen,
        media_type="text/plain"#11111111111111111111111111111111
    )

## ===================== 文件上传接口 =====================
# 支持上传 TXT / PDF / DOCX 文档，自动解析文本并存入向量库
@app.post("/file/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # 只干两件事：读二进制 + 拿文件名
        file_bytes = await file.read()
        filename = file.filename

        # 全部丢给 rag 处理，接口不解析
        result = rag_service.upload_file_process(file_bytes, filename)
        return resp_success(msg=result)

    except Exception as e:
        return resp_error(msg=str(e))

# ===================== 向量库管理接口 =====================
# 根据文件名删除向量库中对应的所有数据
@app.post("/vector/delete")
async def delete_by_filename(filename: str):
    res = rag_service.vector_service.delete_by_filename(filename)
    return resp_success(msg=res)

# 一键清空整个向量库的所有数据
@app.post("/vector/clear")
async def clear_vector_store():
    res = rag_service.vector_service.clear_all()
    return resp_success(msg=res)

# ===================== 健康检查接口 =====================
# 用于测试服务是否正常启动运行
@app.get("/")
async def root():
    return resp_success(msg="知识库问答系统运行正常！")