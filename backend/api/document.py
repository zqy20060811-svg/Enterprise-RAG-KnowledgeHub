"""
文档接口：上传、列表、删除
"""

from fastapi import APIRouter, UploadFile, File, Depends
from core.dependencies import get_document_service
from services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["文档管理"])


@router.post("/upload", summary="上传文档")
async def upload_document(
    file: UploadFile = File(...),
    doc_service: DocumentService = Depends(get_document_service),
):
    file_bytes = await file.read()
    msg, chunk_count = doc_service.upload(file_bytes, file.filename)
    return {"code": 200, "msg": msg, "data": {"filename": file.filename, "chunk_count": chunk_count}}


@router.get("", summary="文档列表")
async def list_documents(
    doc_service: DocumentService = Depends(get_document_service),
):
    docs = doc_service.list_documents()
    return {"code": 200, "msg": "success", "data": docs}


@router.delete("/{filename}", summary="删除文档")
async def delete_document(
    filename: str,
    doc_service: DocumentService = Depends(get_document_service),
):
    msg = doc_service.delete_by_source(filename)
    return {"code": 200, "msg": msg}
