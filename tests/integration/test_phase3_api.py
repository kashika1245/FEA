from __future__ import annotations

import json
import shutil
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.app import create_app
from app.infrastructure.ids import encode_artifact_id
from app.infrastructure.settings import AppSettings
from app.scientific.surrogate.dataset import EXPECTED_DATASET_HASH

DATASET_ID = "paper-a.phase1.v1-n10000-seed20260905"
SOURCE = Path(__file__).resolve().parents[2]


def _copy_dataset(tmp_path: Path) -> None:
    src = SOURCE / "data" / "datasets" / DATASET_ID
    dst = tmp_path / "data" / "datasets" / DATASET_ID
    dst.mkdir(parents=True)
    shutil.copy2(src / "dataset.parquet", dst / "dataset.parquet")
    shutil.copy2(src / "metadata.json", dst / "metadata.json")
    (tmp_path / "data" / "experiments").mkdir(parents=True, exist_ok=True)


@contextmanager
def api_client(tmp_path: Path, repo_root: Path | None = None) -> Iterator[TestClient]:
    root = repo_root if repo_root is not None else tmp_path
    if repo_root is None:
        _copy_dataset(tmp_path)
    settings = AppSettings.from_repo(root, tmp_path / "phase3.sqlite")
    with TestClient(create_app(settings)) as client:
        yield client


def _poll_job(client: TestClient, job_id: str, timeout: float) -> dict[str, object]:
    deadline = time.time() + timeout
    payload: dict[str, object] = {}
    while time.time() < deadline:
        payload = client.get(f"/api/v1/jobs/{job_id}").json()
        if payload["status"] in {"completed", "failed", "cancelled"}:
            return payload
        time.sleep(0.25)
    return payload


def test_health_ready_and_errors(tmp_path: Path) -> None:
    with api_client(tmp_path) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        openapi = client.get("/openapi.json")
        assert openapi.status_code == 200
        assert "/api/v1/health" in openapi.json()["paths"]
        assert "X-Request-ID" in health.headers
        ready = client.get("/api/v1/ready")
        assert ready.status_code == 200
        assert ready.json()["ready"] is True
        missing = client.get("/api/v1/experiments/not-a-real-id")
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "EXPERIMENT_NOT_FOUND"
        assert "traceback" not in missing.text.lower()
        denied = client.options(
            "/api/v1/health",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" not in {
            key.lower() for key in denied.headers
        }
        allowed = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert allowed.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"


def test_immutable_phase2_cannot_run(tmp_path: Path) -> None:
    with api_client(tmp_path, repo_root=SOURCE) as client:
        response = client.post(
            "/api/v1/experiments/paper-a.phase2.v1/run",
            json={"job_type": "TRAIN_SURROGATE"},
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "EXPERIMENT_IMMUTABLE"


def test_research_reads_stored_phase2(tmp_path: Path) -> None:
    with api_client(tmp_path, repo_root=SOURCE) as client:
        summary = client.get(
            "/api/v1/research/summary", params={"experiment_id": "paper-a.phase2.v1"}
        )
        assert summary.status_code == 200
        body = summary.json()
        assert body["dataset_hash"] == EXPECTED_DATASET_HASH
        assert body["variable_wise_rows"] == 132000
        assert body["combined_rows"] == 242000
        assert body["profile_rows"] == 3960
        profiles = client.get(
            "/api/v1/research/profiles",
            params={"experiment_id": "paper-a.phase2.v1", "variable": "E", "limit": 5},
        )
        assert profiles.status_code == 200
        assert len(profiles.json()["rows"]) <= 5
        interp = client.get(
            "/api/v1/research/interpolation", params={"experiment_id": "paper-a.phase2.v1"}
        )
        assert interp.status_code == 200
        assert len(interp.json()["seeds"]) == 5
        thresholds = client.get(
            "/api/v1/research/thresholds", params={"experiment_id": "paper-a.phase2.v1", "limit": 3}
        )
        assert thresholds.status_code == 200
        assert len(thresholds.json()["rows"]) <= 3
        combined = client.get(
            "/api/v1/research/combined",
            params={
                "experiment_id": "paper-a.phase2.v1",
                "output": "sigma_max",
                "direction_a3": "upper",
                "direction_f": "upper",
                "seed": 20260905,
            },
        )
        assert combined.status_code == 200
        assert combined.json()["cells"]
        assert "median_relative_error_pct" in combined.json()["cells"][0]


def test_artifact_security(tmp_path: Path) -> None:
    with api_client(tmp_path, repo_root=SOURCE) as client:
        traversal = client.get("/api/v1/artifacts/%2e%2e%2f%2e%2e%2fetc%2fpasswd")
        assert traversal.status_code in {404, 422}
        token = encode_artifact_id("paper-a.phase2.v1", "manifest.json")
        ok = client.get(f"/api/v1/artifacts/{token}")
        assert ok.status_code == 200
        download = client.get(f"/api/v1/artifacts/{token}/download")
        assert download.status_code == 200
        manifest = json.loads(download.content.decode("utf-8"))
        assert manifest["dataset_hash"] == EXPECTED_DATASET_HASH


def test_pagination_and_injection(tmp_path: Path) -> None:
    with api_client(tmp_path) as client:
        huge = client.get("/api/v1/experiments", params={"limit": 10000})
        assert huge.status_code == 422
        injected = client.post(
            "/api/v1/experiments",
            json={
                "experiment_id": "paper-a.phase3.ok",
                "geometry": "override",
                "dataset_hash": "no",
            },
        )
        assert injected.status_code == 422
        shell = client.post(
            "/api/v1/experiments",
            json={"experiment_id": "paper-a.phase3.;rm -rf"},
        )
        assert shell.status_code == 422


def test_create_run_idempotency_concurrency(tmp_path: Path) -> None:
    with api_client(tmp_path) as client:
        created = client.post(
            "/api/v1/experiments", json={"experiment_id": "paper-a.phase3.tiny-a"}
        )
        assert created.status_code == 201
        first = client.post(
            "/api/v1/experiments/paper-a.phase3.tiny-a/run",
            json={"job_type": "TRAIN_SURROGATE"},
            headers={"X-Idempotency-Key": "same-key-1"},
        )
        second = client.post(
            "/api/v1/experiments/paper-a.phase3.tiny-a/run",
            json={"job_type": "TRAIN_SURROGATE"},
            headers={"X-Idempotency-Key": "same-key-1"},
        )
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["job_id"] == second.json()["job_id"]
        third = client.post(
            "/api/v1/experiments/paper-a.phase3.tiny-a/run",
            json={"job_type": "FULL_PHASE2_PIPELINE"},
        )
        assert third.status_code == 409
        cancelled = client.post(f"/api/v1/jobs/{first.json()['job_id']}/cancel")
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] in {"cancelled", "cancel_requested"}


def test_failed_job_without_dataset(tmp_path: Path) -> None:
    (tmp_path / "data" / "experiments").mkdir(parents=True)
    settings = AppSettings.from_repo(tmp_path, tmp_path / "phase3.sqlite")
    with TestClient(create_app(settings)) as client:
        client.post("/api/v1/experiments", json={"experiment_id": "paper-a.phase3.tiny-fail"})
        launched = client.post(
            "/api/v1/experiments/paper-a.phase3.tiny-fail/run",
            json={"job_type": "TRAIN_SURROGATE"},
        )
        job_id = launched.json()["job_id"]
        payload = _poll_job(client, job_id, 30)
        assert payload["status"] == "failed"
        assert payload["error_code"]


def test_real_tiny_pipeline(tmp_path: Path) -> None:
    with api_client(tmp_path) as client:
        client.post("/api/v1/experiments", json={"experiment_id": "paper-a.phase3.tiny-job"})
        launched = client.post(
            "/api/v1/experiments/paper-a.phase3.tiny-job/run",
            json={"job_type": "FULL_PHASE2_PIPELINE"},
        )
        assert launched.status_code == 200
        payload = _poll_job(client, launched.json()["job_id"], 240)
        assert payload["status"] == "completed", payload
        detail = client.get("/api/v1/experiments/paper-a.phase3.tiny-job").json()
        assert detail["dataset_hash"] == EXPECTED_DATASET_HASH
        assert detail["variable_wise_rows"] == 12
        cancel = client.post(f"/api/v1/jobs/{launched.json()['job_id']}/cancel")
        assert cancel.status_code == 409


def test_restart_marks_stale_running(tmp_path: Path) -> None:
    _copy_dataset(tmp_path)
    db_path = tmp_path / "phase3.sqlite"
    with TestClient(create_app(AppSettings.from_repo(tmp_path, db_path))) as client:
        client.get("/api/v1/health")
    raw = sqlite3.connect(db_path)
    raw.execute(
        """
        INSERT INTO jobs(job_id, experiment_id, job_type, status, created_at, stage)
        VALUES ('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'paper-a.phase3.tiny-job',
                'TRAIN_SURROGATE', 'running', '2026-01-01T00:00:00+00:00', 'train')
        """
    )
    raw.commit()
    raw.close()
    with TestClient(create_app(AppSettings.from_repo(tmp_path, db_path))) as restarted:
        stale = restarted.get("/api/v1/jobs/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        assert stale.status_code == 200
        assert stale.json()["status"] == "failed"
        assert stale.json()["error_code"] == "STALE_AFTER_RESTART"
