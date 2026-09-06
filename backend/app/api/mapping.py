"""Map persistence rows to API schemas."""

from __future__ import annotations

from typing import Any

from app.api.schemas import JobDetail, JobProgress, JobSummary


def job_progress(row: dict[str, Any]) -> JobProgress:
    completed = row.get("completed_units")
    total = row.get("total_units")
    fraction = None
    if completed is not None and total:
        fraction = float(completed) / float(total)
    return JobProgress(stage=row.get("stage"), completed=completed, total=total, fraction=fraction)


def job_summary(row: dict[str, Any]) -> JobSummary:
    return JobSummary(
        job_id=row["job_id"],
        experiment_id=row["experiment_id"],
        job_type=row["job_type"],
        status=row["status"],
        created_at=row["created_at"],
        started_at=row.get("started_at"),
        completed_at=row.get("completed_at"),
    )


def job_detail(row: dict[str, Any]) -> JobDetail:
    return JobDetail(
        **job_summary(row).model_dump(),
        progress=job_progress(row),
        message=row.get("message"),
        error_code=row.get("error_code"),
        error_message=row.get("error_message"),
    )
