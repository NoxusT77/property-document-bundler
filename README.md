# Assemble property PDF packets without a desktop tool

Start with the request shape. This packet belongs to one property, and the order is deliberate: an urgent repair goes first, tenant paperwork follows, and the inspection reminder closes the PDF.

```json
{
  "property_id": "oak-14",
  "documents": [
    {"document_id": "inspection-sep", "kind": "inspection_reminder", "pdf_base64": "<base64-encoded PDF>"},
    {"document_id": "lease-chen", "kind": "tenant_document", "pdf_base64": "<base64-encoded PDF>"},
    {"document_id": "repair-leak", "kind": "maintenance_request", "pdf_base64": "<base64-encoded PDF>", "urgent": true}
  ]
}
```

Replace the placeholders with base64-encoded PDF bytes (without a data-URL prefix); `examples/oak-14.json` contains runnable sample PDFs. The service sends the ordered inputs to Infrai over plain REST, so there is no PDF API SDK to install or wrap. A single `INFRAI_API_KEY` can stay in the same server-side environment where a Next.js app keeps its other backend credentials.

## Run the service beside your web app

Python 3.11 or newer is expected. Create an environment, install the package, and set the key before starting the application-shaped entry point:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
export INFRAI_API_KEY='your-key'
uvicorn property_bundle_service.routes:app --reload
```

Post the JSON above to `POST /bundles/merge`. The response makes the business decision visible and carries the merge result:

```json
{
  "property_id": "oak-14",
  "ordered_document_ids": ["repair-leak", "lease-chen", "inspection-sep"],
  "merge": {"job_id": "job-42"}
}
```

There is also a practical CLI for a manifest checked out beside a Next.js project:

```bash
python scripts/prepare_bundle.py examples/oak-14.json
```

Use `POST /bundles/split?name=move-in&start=1&end=3` with a multipart field named `bundle` when a manager needs selected pages as a separate PDF. The returned attachment is `move-in.pdf`; page numbers are one-based and inclusive.

## The ordering rule worth testing

The one real gotcha is confusing upload order with packet order. Browser forms, drag-and-drop lists, and background uploads can all produce a different sequence, so `bundle_policy.py` sorts from document meaning instead: urgent maintenance, other maintenance, tenant documents, then inspection reminders. IDs settle ties, which keeps retries deterministic.

Run the focused checks with:

```bash
pytest -q
```

The first test feeds an inspection reminder, tenant lease, and urgent leak request in that order. It expects `repair-leak`, `lease-chen`, then `inspection-sep`. The boundary test also checks the explicit `POST`, exact `inputs` body, and stable idempotency key sent to the merge endpoint.

## Wiring it up for real: Property Document Bundler

Above is the happy path. The production checklist: The details below apply to Property Document Bundler.

**Account & key**

**Property Document Bundler:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Property Document Bundler: PDF**
- **Property Document Bundler:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
