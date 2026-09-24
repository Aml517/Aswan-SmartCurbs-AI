import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.analysis import AnalysisJob, VehicleDetectionLog
from app.models.zone import ParkingZone
from app.schemas.analysis import AnalysisJobResponse, AnalysisJobDetailResponse, VehicleDetectionResponse
from app.services.ai_pipeline_service import process_video_analysis

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "media" / "uploads"
PROCESSED_DIR = BASE_DIR / "media" / "processed_videos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/analysis/upload", response_model=AnalysisJobResponse)
async def upload_and_analyze_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    zone_id: int = Form(1),
    run_sync: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    Upload an MP4 / AVI / MOV video for automated AI vehicle tracking,
    homography-calibrated centimeter distance estimation, and parking occupancy analysis.
    """
    # 1. Validate Zone
    zone = db.query(ParkingZone).filter(ParkingZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Parking Zone #{zone_id} not found in database.")

    # 2. Validate Video Extension
    filename = video.filename or "uploaded_video.mp4"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".mp4", ".avi", ".mov", ".mkv"]:
        raise HTTPException(status_code=400, detail="Invalid video format. Supported formats: MP4, AVI, MOV, MKV.")

    # 3. Save uploaded file to disk
    job_temp = AnalysisJob(
        zone_id=zone_id,
        filename=filename,
        input_video_path="",
        status="pending"
    )
    db.add(job_temp)
    db.commit()
    db.refresh(job_temp)

    saved_filename = f"job_{job_temp.id}_{filename}"
    saved_path = UPLOAD_DIR / saved_filename
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)

    job_temp.input_video_path = str(saved_path)
    db.commit()

    # 4. Run Analysis (Synchronously or as BackgroundTask)
    if run_sync:
        try:
            job_temp = process_video_analysis(job_temp.id, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")
    else:
        # Note: for background task, use independent DB session
        def run_bg(j_id: int):
            from app.db.database import SessionLocal
            with SessionLocal() as bg_db:
                process_video_analysis(j_id, bg_db)
        background_tasks.add_task(run_bg, job_temp.id)

    resp = AnalysisJobResponse.model_validate(job_temp)
    if job_temp.output_video_path and os.path.exists(job_temp.output_video_path):
        resp.output_video_url = f"/api/v1/analysis/{job_temp.id}/video"
    return resp


@router.get("/analysis", response_model=List[AnalysisJobResponse])
def list_analysis_jobs(db: Session = Depends(get_db)):
    """List all AI video analysis jobs ordered by creation date."""
    jobs = db.query(AnalysisJob).order_by(AnalysisJob.created_at.desc()).all()
    results = []
    for j in jobs:
        r = AnalysisJobResponse.model_validate(j)
        if j.output_video_path and os.path.exists(j.output_video_path):
            r.output_video_url = f"/api/v1/analysis/{j.id}/video"
        results.append(r)
    return results


@router.get("/analysis/{job_id}", response_model=AnalysisJobDetailResponse)
def get_analysis_job_detail(job_id: int, db: Session = Depends(get_db)):
    """Retrieve detailed structured results for a specific analysis job."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Analysis Job #{job_id} not found.")

    detections = db.query(VehicleDetectionLog).filter(
        VehicleDetectionLog.job_id == job_id
    ).order_by(VehicleDetectionLog.frame_number.asc()).limit(50).all()

    resp = AnalysisJobDetailResponse.model_validate(job)
    if job.output_video_path and os.path.exists(job.output_video_path):
        resp.output_video_url = f"/api/v1/analysis/{job.id}/video"
    resp.recent_detections = [VehicleDetectionResponse.model_validate(d) for d in detections]
    return resp


@router.get("/analysis/{job_id}/video")
def stream_analysis_output_video(job_id: int, db: Session = Depends(get_db)):
    """Stream or download the annotated output video produced by the AI pipeline."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job or not job.output_video_path or not os.path.exists(job.output_video_path):
        raise HTTPException(status_code=404, detail="Processed video not found for this analysis job.")

    return FileResponse(
        path=job.output_video_path,
        media_type="video/mp4",
        filename=os.path.basename(job.output_video_path)
    )
