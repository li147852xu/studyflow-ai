from app.adapters.facade import (
    count_documents_for_filter,
    delete_document,
    doc_chunk_counts,
    doc_pages,
    get_document_detail,
    import_and_process,
    list_documents_with_tags,
    rebuild_index,
    recent_history,
    upload_dir,
    workspace_status,
)

__all__ = [
    "count_documents_for_filter",
    "delete_document",
    "doc_chunk_counts",
    "doc_pages",
    "get_document_detail",
    "import_and_process",
    "list_documents_with_tags",
    "recent_history",
    "rebuild_index",
    "upload_dir",
    "workspace_status",
]
