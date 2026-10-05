import argparse
import asyncio
import json
from pathlib import Path

from property_bundle_service.bundle_policy import order_documents
from property_bundle_service.infrai_pdf import InfraiPdfClient
from property_bundle_service.models import MergeBundleRequest


async def prepare(manifest_path: Path) -> None:
    request = MergeBundleRequest.model_validate_json(manifest_path.read_text())
    ordered = order_documents(request.documents)
    async with InfraiPdfClient() as client:
        result = await client.merge(
            inputs=[document.pdf_base64 for document in ordered],
            idempotency_key=f"property-bundle:{request.property_id}",
        )
    print(json.dumps({
        "property_id": request.property_id,
        "ordered_document_ids": [document.document_id for document in ordered],
        "merge": result,
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare one property PDF bundle")
    parser.add_argument("manifest", type=Path)
    arguments = parser.parse_args()
    asyncio.run(prepare(arguments.manifest))
