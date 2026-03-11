"""
Service layer for handling media uploads and compression.
"""
import os
import shutil
import uuid
import subprocess
from PIL import Image
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..models.repair_media import RepairMedia

UPLOAD_DIR = "uploads"

def process_and_save_image(file: UploadFile) -> str:
    """
    Compress image to WebP (80% quality) and save to disk.
    """
    unique_id = str(uuid.uuid4())
    filename = f"{unique_id}.webp"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        img = Image.open(file.file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(file_path, "WEBP", quality=80)
        return f"/{UPLOAD_DIR}/{filename}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image compression failed: {str(e)}")

def process_and_save_video(file: UploadFile) -> str:
    """
    Compress video to MP4 using FFmpeg and save to disk.
    """
    unique_id = str(uuid.uuid4())
    filename = f"{unique_id}.mp4"
    file_path = os.path.join(UPLOAD_DIR, filename)
    temp_input = os.path.join(UPLOAD_DIR, f"temp_{unique_id}_{file.filename}")
    
    # Save temp file
    with open(temp_input, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Run FFmpeg for compression
        cmd = [
            "ffmpeg", "-i", temp_input,
            "-vcodec", "libx264", "-crf", "28", "-preset", "faster",
            "-acodec", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            "-y", file_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return f"/{UPLOAD_DIR}/{filename}"
    except subprocess.CalledProcessError as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Video compression failed: {e.stderr.decode()}")
    finally:
        if os.path.exists(temp_input):
            os.remove(temp_input)

def save_repair_media(db: Session, repair_id: int, section: str, file: UploadFile) -> RepairMedia:
    """
    Orchestrate media saving and DB record creation.
    """
    is_image = file.content_type.startswith("image")
    is_video = file.content_type.startswith("video")
    
    if is_image:
        file_url = process_and_save_image(file)
        file_type = "image"
    elif is_video:
        file_url = process_and_save_video(file)
        file_type = "video"
    else:
        # Generic save for other types
        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_url = f"/{UPLOAD_DIR}/{filename}"
        file_type = "other"

    new_media = RepairMedia(
        repairId=repair_id,
        fileUrl=file_url,
        fileType=file_type,
        section=section
    )
    db.add(new_media)
    db.commit()
    db.refresh(new_media)
    return new_media
