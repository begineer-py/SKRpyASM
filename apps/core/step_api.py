import logging
from typing import Optional

from django.db import transaction
from ninja import Router
from ninja import Schema
from ninja.errors import HttpError

from apps.core.models import Step
from apps.core.models.analyze.Step import StepNote


logger = logging.getLogger(__name__)

router = Router(tags=["Core - Steps"])


class StepNoteUpsertIn(Schema):
    content: Optional[str] = None
    ai_thoughts: Optional[str] = None


class StepOut(Schema):
    id: int
    overview_id: Optional[int] = None
    parent_step_id: Optional[int] = None
    order: int
    status: str


class StepCreateIn(Schema):
    overview_id: Optional[int] = None
    parent_step_id: Optional[int] = None
    order: Optional[int] = None
    status: Optional[str] = None
    note: Optional[StepNoteUpsertIn] = None


class StepUpdateIn(Schema):
    overview_id: Optional[int] = None
    parent_step_id: Optional[int] = None
    order: Optional[int] = None
    status: Optional[str] = None


@router.post("/steps/", response={200: StepOut})
def create_step(request, payload: StepCreateIn):
    with transaction.atomic():
        step = Step.objects.create(
            overview_id=payload.overview_id,
            parent_step_id=payload.parent_step_id,
            order=payload.order or 1,
            status=payload.status or "PENDING",
        )

        if payload.note and (payload.note.content is not None or payload.note.ai_thoughts is not None):
            StepNote.objects.update_or_create(
                step=step,
                defaults={
                    "content": payload.note.content,
                    "ai_thoughts": payload.note.ai_thoughts,
                },
            )

    return {
        "id": step.id,
        "overview_id": step.overview_id,
        "parent_step_id": step.parent_step_id,
        "order": step.order,
        "status": step.status,
    }


@router.patch("/steps/{step_id}", response={200: StepOut})
def update_step(request, step_id: int, payload: StepUpdateIn):
    step = Step.objects.filter(id=step_id).first()
    if not step:
        raise HttpError(404, f"Step {step_id} not found")

    updated_fields = []
    if payload.overview_id is not None:
        step.overview_id = payload.overview_id
        updated_fields.append("overview")
    if payload.parent_step_id is not None:
        step.parent_step_id = payload.parent_step_id
        updated_fields.append("parent_step")
    if payload.order is not None:
        step.order = payload.order
        updated_fields.append("order")
    if payload.status is not None:
        step.status = payload.status
        updated_fields.append("status")

    if updated_fields:
        step.save(update_fields=updated_fields)

    return {
        "id": step.id,
        "overview_id": step.overview_id,
        "parent_step_id": step.parent_step_id,
        "order": step.order,
        "status": step.status,
    }


@router.delete("/steps/{step_id}", response={200: dict})
def delete_step(request, step_id: int):
    step = Step.objects.filter(id=step_id).first()
    if not step:
        raise HttpError(404, f"Step {step_id} not found")
    step.delete()
    return {"deleted": True, "step_id": step_id}


@router.put("/steps/{step_id}/note/", response={200: dict})
def upsert_step_note(request, step_id: int, payload: StepNoteUpsertIn):
    step = Step.objects.filter(id=step_id).first()
    if not step:
        raise HttpError(404, f"Step {step_id} not found")

    note, _created = StepNote.objects.update_or_create(
        step=step,
        defaults={
            "content": payload.content,
            "ai_thoughts": payload.ai_thoughts,
        },
    )

    return {
        "step_id": step.id,
        "note_id": note.id,
        "content": note.content,
        "ai_thoughts": note.ai_thoughts,
    }
