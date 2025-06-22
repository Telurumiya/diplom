"""Celery tasks for email and notifications."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from asgiref.sync import async_to_sync
from celery import Celery

from app.core.config import get_settings
from app.core.logger import app_logger
from app.db import get_async_session_context
from app.db.crud.document_crud import DocumentCrud, SyncDocumentCrud
from app.db.database import get_sync_session_context
from app.services.email_service import EmailSendService
from app.utils.enums import DocumentStatus
from app.utils.formatting import check_document_formatting

settings = get_settings()

celery = Celery(
    "chat", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_BACKEND_URL
)

celery.conf.update(
    task_serializer=settings.TASK_SERIALIZER,
    result_serializer=settings.RESULT_SERIALIZER,
    accept_content=settings.get_accept_content_list(),
    timezone=settings.TIMEZONE,
    enable_utc=settings.ENABLE_UTC,
    task_time_limit=settings.TASK_TIME_LIMIT,
    task_soft_time_limit=settings.TASK_SOFT_TIME_LIMIT,
    worker_concurrency=settings.WORKER_CONCURRENCY,
    task_retry_delay=settings.TASK_RETRY_DELAY,
    task_acks_late=settings.TASK_ACKS_LATE,
    task_reject_on_worker_lost=settings.TASK_REJECT_ON_WORKER_LOST,
)


@celery.task(
    name="send_email",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    retry_backoff=True,
    ignore_result=True,
)
def task_to_confirm_email(self, email: str, template_type: str, **template_kwargs):
    """Send notification about new message asynchronously.

    Args:
        email (str): Email address to send.
        template_type (str): Template type to send.
    """

    async def _task():
        service = EmailSendService()
        await service.send_email_once(email, template_type, **template_kwargs)

    try:
        async_to_sync(_task)()
    except ValueError as e:
        app_logger.error(f"Template error for {email}: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        app_logger.error(
            f"Failed to send {template_type} email to {email}: {str(e)}",
            exc_info=True,
        )
        raise self.retry(exc=e, countdown=5)

@celery.task(
    name="process_document_formating",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    retry_backoff=True,
    ignore_result=True,
)
def task_process_document_formatting(self, document_id: int, file_path: str):
    try:
        path = Path(file_path)
        new_path = path.with_name(f"{path.stem}_NEW{path.suffix}")
        json_path = path.with_name(f"{path.stem}_errors.json")

        # 1. Проверяем формат
        is_ok = check_document_formatting(
            str(path), str(new_path), str(json_path)
        )

        # 2. Считаем ошибки
        err_count = 0
        if json_path.exists():
            with open(json_path, encoding="utf-8") as f:
                errs = json.load(f)
                err_count = len(errs)

        # 3. Готовим данные для БД
        status = DocumentStatus.CHECKED if is_ok else DocumentStatus.FAILED
        data = {
            "status": status,
            "error_count": err_count,
        }
        if is_ok and new_path.exists():
            data["new_filepath"] = str(new_path)
        if json_path.exists():
            data["json_filepath"] = str(json_path)

        # 4. Синхронно обновляем запись
        with get_sync_session_context() as session:
            crud = SyncDocumentCrud(session)
            crud.update(document_id, data)

        app_logger.info(
            f"Документ {document_id} обработан: статус={status.value}, ошибок={err_count}"
        )

    except Exception as e:
        app_logger.error(
            f"Ошибка обработки документа {document_id}: {e}", exc_info=True
        )
        raise self.retry(exc=e, countdown=5)