from __future__ import annotations

from core.packs.exam_pack import build_exam_pack
from core.packs.related_pack import build_related_pack
from core.packs.slides_pack import build_slides_pack


class PackServiceError(RuntimeError):
    pass


def make_pack(
    *, workspace_id: str, pack_type: str, source_id: str
) -> str:
    if pack_type == "slides":
        return str(build_slides_pack(workspace_id=workspace_id, doc_id=source_id))
    if pack_type == "exam":
        return str(build_exam_pack(workspace_id=workspace_id, course_id=source_id))
    if pack_type == "related":
        return str(build_related_pack(workspace_id=workspace_id, project_id=source_id))
    raise PackServiceError("Pack type must be slides, exam, or related.")
