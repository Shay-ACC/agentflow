from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps import get_document_service
from app.schemas.document import DocumentRead
from app.services.document_service import DocumentService


router = APIRouter(prefix="/documents", tags=["documents"])
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]


@router.get("", response_model=list[DocumentRead])
def list_documents(service: DocumentServiceDep) -> list[DocumentRead]:
    documents = service.list_documents()
    return [DocumentRead.model_validate(document) for document in documents]


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    service: DocumentServiceDep,
) -> DocumentRead:
    document = await service.upload_document(file=file)
    return DocumentRead.model_validate(document)
