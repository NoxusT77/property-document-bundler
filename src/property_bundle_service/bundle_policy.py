from .models import DocumentKind, PropertyDocument


def order_documents(documents: list[PropertyDocument]) -> list[PropertyDocument]:
    """Put actionable maintenance first and calendar reminders last."""
    priority = {
        DocumentKind.MAINTENANCE_REQUEST: 0,
        DocumentKind.TENANT_DOCUMENT: 2,
        DocumentKind.INSPECTION_REMINDER: 3,
    }
    return sorted(
        documents,
        key=lambda item: (
            -int(item.urgent),
            priority[item.kind],
            item.document_id,
        ),
    )

