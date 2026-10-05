from io import BytesIO
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pypdf import PdfReader, PdfWriter

from .bundle_policy import order_documents
from .infrai_pdf import InfraiError, InfraiPdfClient
from .models import MergeBundleRequest, MergeBundleResult, PageRange

app = FastAPI(title="Property document bundler")


def get_infrai_client() -> InfraiPdfClient:
    return InfraiPdfClient()


@app.post("/bundles/merge", response_model=MergeBundleResult)
async def merge_property_bundle(
    request: MergeBundleRequest,
    client: Annotated[InfraiPdfClient, Depends(get_infrai_client)],
) -> MergeBundleResult:
    ordered = order_documents(request.documents)
    try:
        merge = await client.merge(
            inputs=[document.pdf_base64 for document in ordered],
            idempotency_key=f"property-bundle:{request.property_id}",
        )
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    return MergeBundleResult(
        property_id=request.property_id,
        ordered_document_ids=[document.document_id for document in ordered],
        merge=merge,
    )


@app.post("/bundles/split")
async def split_property_bundle(
    page_range: Annotated[PageRange, Depends()],
    bundle: Annotated[UploadFile, File()],
) -> StreamingResponse:
    reader = PdfReader(BytesIO(await bundle.read()))
    if page_range.end > len(reader.pages):
        raise HTTPException(status_code=422, detail="page range exceeds bundle length")

    writer = PdfWriter()
    for page_number in range(page_range.start - 1, page_range.end):
        writer.add_page(reader.pages[page_number])
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{page_range.name}.pdf"'
        },
    )
