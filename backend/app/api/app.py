"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import APIRouter, FastAPI, Header, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.mapping import job_detail
from app.api.schemas import (
    ArtifactDetail,
    ArtifactSummary,
    AsymmetryResponse,
    CombinedResponse,
    ErrorBody,
    ErrorResponse,
    ExperimentCreateRequest,
    ExperimentDetail,
    ExperimentRunRequest,
    ExperimentSummary,
    HealthResponse,
    InterpolationResponse,
    JobDetail,
    ProfileResponse,
    ReadinessResponse,
    ThresholdResponse,
)
from app.application.executor import JobExecutor
from app.application.job_repo import mark_stale_running
from app.application.services import AppServices
from app.infrastructure.db import connect, initialize
from app.infrastructure.errors import ApplicationError
from app.infrastructure.ids import validate_experiment_id, validate_request_id
from app.infrastructure.settings import AppSettings
from app.scientific.exceptions import ScientificError
from app.scientific.phase2_errors import InterpolationGateError, Phase1IntegrityError, Phase2Error

SCIENTIFIC_STATUS = {
    InterpolationGateError: ("INTERPOLATION_GATE_FAILED", 409),
    Phase1IntegrityError: ("PHASE1_INTEGRITY_FAILED", 409),
}


def create_app(settings: AppSettings | None = None) -> FastAPI:
    resolved = settings if settings is not None else AppSettings.from_repo()
    connection = connect(resolved.db_path)
    initialize(connection)
    mark_stale_running(connection)
    executor = JobExecutor(resolved, connection)
    services = AppServices(resolved, connection, executor)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        executor.start()
        yield
        executor.stop()
        connection.close()

    app = FastAPI(
        title="Paper A Phase 3 API",
        version="0.3.0",
        description="Research infrastructure around the frozen Phase 1/2 scientific engine.",
        lifespan=lifespan,
    )
    app.state.settings = resolved
    app.state.connection = connection
    app.state.executor = executor
    app.state.services = services
    if resolved.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved.cors_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["X-Request-ID", "X-Idempotency-Key", "Content-Type"],
        )

    router = APIRouter(prefix="/api/v1")

    def svc(request: Request) -> AppServices:
        return services

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next: Any) -> Any:
        request_id = validate_request_id(request.headers.get("X-Request-ID"))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    def envelope(request: Request, code: str, message: str, status_code: int) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        body = ErrorResponse(error=ErrorBody(code=code, message=message, request_id=request_id))
        return JSONResponse(status_code=status_code, content=jsonable_encoder(body))

    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
        return envelope(request, exc.code, exc.message, exc.http_status)

    @app.exception_handler(Phase2Error)
    async def phase2_error_handler(request: Request, exc: Phase2Error) -> JSONResponse:
        code, status = SCIENTIFIC_STATUS.get(type(exc), (type(exc).__name__, 409))
        return envelope(request, code, str(exc), status)

    @app.exception_handler(ScientificError)
    async def scientific_error_handler(request: Request, exc: ScientificError) -> JSONResponse:
        return envelope(request, type(exc).__name__, "A scientific operation failed.", 409)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return envelope(request, "VALIDATION_ERROR", "Request failed schema validation.", 422)

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return envelope(request, "HTTP_ERROR", str(exc.detail), exc.status_code)

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        return envelope(request, "INTERNAL_ERROR", "An unexpected error occurred.", 500)

    @router.get("/health", response_model=HealthResponse)
    def health(request: Request) -> HealthResponse:
        return HealthResponse.model_validate(svc(request).health())

    @router.get("/ready", response_model=ReadinessResponse)
    def ready(request: Request) -> ReadinessResponse:
        return ReadinessResponse.model_validate(svc(request).ready())

    @router.get("/experiments", response_model=list[ExperimentSummary])
    def experiments(
        request: Request,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> list[ExperimentSummary]:
        return [
            ExperimentSummary.model_validate(item)
            for item in svc(request).list_experiments(offset, limit)
        ]

    @router.post("/experiments", response_model=ExperimentSummary, status_code=201)
    def create_experiment(body: ExperimentCreateRequest, request: Request) -> ExperimentSummary:
        return ExperimentSummary.model_validate(svc(request).create_experiment(body.experiment_id))

    @router.get("/experiments/{experiment_id}", response_model=ExperimentDetail)
    def get_experiment(experiment_id: str, request: Request) -> ExperimentDetail:
        return ExperimentDetail.model_validate(svc(request).experiment_detail(experiment_id))

    @router.post("/experiments/{experiment_id}/run", response_model=JobDetail)
    def run_experiment(
        experiment_id: str,
        body: ExperimentRunRequest,
        request: Request,
        x_idempotency_key: Annotated[str | None, Header()] = None,
    ) -> JobDetail:
        job = svc(request).run_experiment(experiment_id, body.job_type, x_idempotency_key)
        return job_detail(job)

    @router.post("/experiments/{experiment_id}/cancel", response_model=JobDetail)
    def cancel_experiment(experiment_id: str, request: Request) -> JobDetail:
        return job_detail(svc(request).cancel_active_experiment(experiment_id))

    @router.get("/jobs", response_model=list[JobDetail])
    def jobs(
        request: Request,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
        experiment_id: str | None = None,
    ) -> list[JobDetail]:
        return [job_detail(item) for item in svc(request).list_jobs(offset, limit, experiment_id)]

    @router.get("/jobs/{job_id}", response_model=JobDetail)
    def get_job(job_id: str, request: Request) -> JobDetail:
        return job_detail(svc(request).get_job(job_id))

    @router.post("/jobs/{job_id}/cancel", response_model=JobDetail)
    def cancel_job(job_id: str, request: Request) -> JobDetail:
        return job_detail(svc(request).cancel_job(job_id))

    @router.get("/artifacts", response_model=list[ArtifactSummary])
    def artifacts(
        experiment_id: str,
        request: Request,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> list[ArtifactSummary]:
        validate_experiment_id(experiment_id)
        return [
            ArtifactSummary.model_validate(item)
            for item in svc(request).list_artifacts(experiment_id, offset, limit)
        ]

    @router.get("/artifacts/{artifact_id}", response_model=ArtifactDetail)
    def artifact_detail(artifact_id: str, request: Request) -> ArtifactDetail:
        return ArtifactDetail.model_validate(svc(request).artifact_detail(artifact_id))

    @router.get("/artifacts/{artifact_id}/download")
    def artifact_download(artifact_id: str, request: Request) -> FileResponse:
        path = svc(request).artifact_file(artifact_id)
        return FileResponse(path, filename=path.name)

    @router.get("/research/summary", response_model=ExperimentDetail)
    def research_summary(experiment_id: str, request: Request) -> ExperimentDetail:
        return ExperimentDetail.model_validate(svc(request).research_summary(experiment_id))

    @router.get("/research/profiles", response_model=ProfileResponse)
    def research_profiles(
        experiment_id: str,
        request: Request,
        variable: str | None = None,
        output: str | None = None,
        seed: int | None = None,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=200, ge=1, le=2000),
    ) -> ProfileResponse:
        rows = svc(request).read_parquet_page(
            experiment_id,
            "profiles/profiles.parquet",
            offset,
            limit,
            {"variable": variable, "response": output, "seed": seed},
        )
        return ProfileResponse(experiment_id=experiment_id, rows=rows)

    @router.get("/research/thresholds", response_model=ThresholdResponse)
    def research_thresholds(
        experiment_id: str,
        request: Request,
        variable: str | None = None,
        output: str | None = None,
        seed: int | None = None,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=200, ge=1, le=2000),
    ) -> ThresholdResponse:
        rows = svc(request).read_parquet_page(
            experiment_id,
            "profiles/thresholds.parquet",
            offset,
            limit,
            {"variable": variable, "response": output, "seed": seed},
        )
        return ThresholdResponse(experiment_id=experiment_id, rows=rows)

    @router.get("/research/asymmetry", response_model=AsymmetryResponse)
    def research_asymmetry(
        experiment_id: str,
        request: Request,
        variable: str | None = None,
        output: str | None = None,
        seed: int | None = None,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=200, ge=1, le=2000),
    ) -> AsymmetryResponse:
        rows = svc(request).read_parquet_page(
            experiment_id,
            "profiles/asymmetry.parquet",
            offset,
            limit,
            {"variable": variable, "response": output, "seed": seed},
        )
        return AsymmetryResponse(experiment_id=experiment_id, rows=rows)

    @router.get("/research/interpolation", response_model=InterpolationResponse)
    def research_interpolation(experiment_id: str, request: Request) -> InterpolationResponse:
        seeds = svc(request).read_json_dir(experiment_id, "interpolation", "seed-*.json")
        return InterpolationResponse(experiment_id=experiment_id, seeds=seeds)

    @router.get("/research/combined", response_model=CombinedResponse)
    def research_combined(
        experiment_id: str,
        request: Request,
        output: str,
        direction_a3: str,
        direction_f: str,
        seed: int,
    ) -> CombinedResponse:
        return CombinedResponse.model_validate(
            svc(request).combined_grid(
                experiment_id,
                response=output,
                direction_a3=direction_a3,
                direction_f=direction_f,
                seed=seed,
            )
        )

    app.include_router(router)
    return app
