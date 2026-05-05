"""FastAPI route definitions."""

from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import HTMLResponse

from backend.models.database import get_report, list_reports, save_report
from backend.models.schemas import (
    DetectRequest,
    DetectResponse,
    FullPipelineRequest,
    HealthResponse,
    HumanizeRequest,
    HumanizeResponse,
    PipelineResponse,
)
from backend.services.ai_detector import detect_ai
from backend.services.humanizer import humanize_text_with_fallback
from backend.services.plagiarism_detector import detect_plagiarism
from backend.services.report_generator import generate_html_report
from backend.utils.similarity import is_model_loaded

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


# ── Health ─────────────────────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(models_loaded=is_model_loaded())


# ── Detect ─────────────────────────────────────────────────────────────
@router.post("/detect", response_model=DetectResponse)
async def detect(req: DetectRequest):
    try:
        result = await detect_plagiarism(req.text, check_web=req.check_web)
        ai_result = detect_ai(req.text)

        report_id = str(uuid4())
        response = DetectResponse(
            report_id=report_id,
            overall_similarity=result["overall_similarity"],
            risk_level=result["risk_level"],
            flagged_sentences=result["flagged_sentences"],
            ai_detection=ai_result,
            text_stats=result["text_stats"],
        )

        # Persist
        save_report(report_id, req.text, response.model_dump(mode="json"))
        return response

    except Exception as exc:
        logger.exception("Detection failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Humanize ───────────────────────────────────────────────────────────
@router.post("/humanize", response_model=HumanizeResponse)
async def humanize(req: HumanizeRequest):
    try:
        ai_before = detect_ai(req.text)

        result = await humanize_text_with_fallback(
            req.text, level=req.level.value, preserve_keywords=req.preserve_keywords
        )

        ai_after = detect_ai(result["humanized_text"])

        return HumanizeResponse(
            original_text=req.text,
            humanized_text=result["humanized_text"],
            changes_made=result["changes_made"],
            level=req.level,
            ai_detection_before=ai_before,
            ai_detection_after=ai_after,
        )
    except Exception as exc:
        logger.exception("Humanization failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Full Pipeline ──────────────────────────────────────────────────────
@router.post("/pipeline", response_model=PipelineResponse)
async def pipeline(req: FullPipelineRequest):
    """Detect → Humanize → Re-detect in one request."""
    try:
        # Step 1: initial detection
        det1 = await detect_plagiarism(req.text, check_web=req.check_web)
        ai1 = detect_ai(req.text)
        report1 = DetectResponse(
            overall_similarity=det1["overall_similarity"],
            risk_level=det1["risk_level"],
            flagged_sentences=det1["flagged_sentences"],
            ai_detection=ai1,
            text_stats=det1["text_stats"],
        )

        # Step 2: humanize
        hum = await humanize_text_with_fallback(
            req.text, level=req.humanize_level.value
        )
        humanized_text = hum["humanized_text"]

        # Step 3: re-detect
        det2 = await detect_plagiarism(humanized_text, check_web=False)
        ai2 = detect_ai(humanized_text)
        report2 = DetectResponse(
            overall_similarity=det2["overall_similarity"],
            risk_level=det2["risk_level"],
            flagged_sentences=det2["flagged_sentences"],
            ai_detection=ai2,
            text_stats=det2["text_stats"],
        )

        # Improvement = reduction in AI probability (the primary metric)
        ai_before = ai1["ai_probability"]
        ai_after = ai2["ai_probability"]
        if ai_before > 0:
            improvement = round(max((ai_before - ai_after) / ai_before * 100, 0), 2)
        else:
            improvement = 0.0

        report_id = str(uuid4())
        resp = PipelineResponse(
            report_id=report_id,
            original_detection=report1,
            humanized_text=humanized_text,
            post_humanize_detection=report2,
            improvement_percent=improvement,
        )

        save_report(report_id, req.text, resp.model_dump(mode="json"), report_type="pipeline")
        return resp

    except Exception as exc:
        logger.exception("Pipeline failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Reports ────────────────────────────────────────────────────────────
@router.get("/reports")
async def get_reports():
    return list_reports()


@router.get("/reports/{report_id}")
async def get_report_by_id(report_id: str):
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/reports/{report_id}/html", response_class=HTMLResponse)
async def get_report_html(report_id: str):
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    result = report["result"]
    html_content = generate_html_report(result, report.get("input_text", ""))
    return HTMLResponse(content=html_content)
