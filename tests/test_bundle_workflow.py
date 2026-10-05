import json

import httpx
import pytest

from property_bundle_service.bundle_policy import order_documents
from property_bundle_service.infrai_pdf import InfraiPdfClient
from property_bundle_service.models import MergeBundleRequest


def sample_request() -> MergeBundleRequest:
    return MergeBundleRequest.model_validate({
        "property_id": "oak-14",
        "documents": [
            {
                "document_id": "inspection-sep",
                "kind": "inspection_reminder",
                "pdf_base64": "inspection-pdf-base64",
            },
            {
                "document_id": "lease-chen",
                "kind": "tenant_document",
                "pdf_base64": "lease-pdf-base64",
            },
            {
                "document_id": "repair-leak",
                "kind": "maintenance_request",
                "pdf_base64": "repair-pdf-base64",
                "urgent": True,
            },
        ],
    })


def test_urgent_maintenance_leads_and_inspection_reminder_closes_bundle() -> None:
    ordered = order_documents(sample_request().documents)
    assert [document.document_id for document in ordered] == [
        "repair-leak",
        "lease-chen",
        "inspection-sep",
    ]


@pytest.mark.asyncio
async def test_merge_boundary_sends_ordered_inputs_and_idempotency_key() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        seen["idempotency"] = request.headers["Idempotency-Key"]
        return httpx.Response(200, json={"ok": True, "data": {"job_id": "job-42"}})

    request = sample_request()
    ordered = order_documents(request.documents)
    async with InfraiPdfClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await client.merge(
            [document.pdf_base64 for document in ordered],
            f"property-bundle:{request.property_id}",
        )

    assert result == {"job_id": "job-42"}
    assert seen == {
        "method": "POST",
        "path": "/v1/pdf/merge",
        "body": {"inputs": [
            "repair-pdf-base64",
            "lease-pdf-base64",
            "inspection-pdf-base64",
        ]},
        "idempotency": "property-bundle:oak-14",
    }
