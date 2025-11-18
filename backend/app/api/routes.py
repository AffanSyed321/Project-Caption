from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
from pathlib import Path

from app.core.database import get_db
from app.core.config import settings
from app.models.caption import Caption
from app.services.local_research import LocalResearchService
from app.services.openai_service import OpenAIService

router = APIRouter()

# Ensure uploads directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/generate-caption")
async def generate_caption(
    image: UploadFile = File(...),
    goal: str = Form(...),
    address: str = Form(...),
    platform: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Generate a localized caption based on:
    - Uploaded image
    - Goal of the post
    - Urban Air location address
    - Target platform (Facebook or Instagram)
    """
    try:
        # Validate API key
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in environment."
            )

        # Save uploaded image temporarily
        image_path = UPLOAD_DIR / image.filename
        with image_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Initialize services
        research_service = LocalResearchService()
        openai_service = OpenAIService(api_key=settings.OPENAI_API_KEY)

        # Step 1: Analyze the image
        print(f"Analyzing image: {image.filename}")
        image_analysis = openai_service.analyze_image(str(image_path))

        # Step 2: Research local area
        print(f"Researching location: {address}")
        local_research = research_service.research_location(address)

        if "error" in local_research:
            raise HTTPException(status_code=400, detail=local_research["error"])

        # Step 3: Generate caption
        print(f"Generating caption for {local_research['city']}, {local_research['state']}")
        caption = openai_service.generate_caption(
            goal=goal,
            image_analysis=image_analysis,
            local_research=local_research,
            platform=platform
        )

        # Clean up uploaded file
        image_path.unlink()

        return {
            "caption": caption,
            "location_info": {
                "city": local_research["city"],
                "state": local_research["state"],
                "is_rural": local_research["is_rural"]
            },
            "image_analysis": image_analysis
        }

    except Exception as e:
        # Clean up on error
        if image_path.exists():
            image_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate-caption")
async def regenerate_caption(
    image: UploadFile = File(...),
    goal: str = Form(...),
    address: str = Form(...),
    platform: str = Form(...),
    previous_caption: str = Form(...),
):
    """
    Regenerate a different version of the caption
    """
    try:
        # Validate API key
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured."
            )

        # Save uploaded image temporarily
        image_path = UPLOAD_DIR / image.filename
        with image_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Initialize services
        research_service = LocalResearchService()
        openai_service = OpenAIService(api_key=settings.OPENAI_API_KEY)

        # Analyze image and research location
        image_analysis = openai_service.analyze_image(str(image_path))
        local_research = research_service.research_location(address)

        if "error" in local_research:
            raise HTTPException(status_code=400, detail=local_research["error"])

        # Regenerate caption
        caption = openai_service.regenerate_caption(
            goal=goal,
            image_analysis=image_analysis,
            local_research=local_research,
            platform=platform,
            previous_caption=previous_caption
        )

        # Clean up
        image_path.unlink()

        return {
            "caption": caption,
            "location_info": {
                "city": local_research["city"],
                "state": local_research["state"],
                "is_rural": local_research["is_rural"]
            }
        }

    except Exception as e:
        if image_path.exists():
            image_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-caption")
async def save_caption(
    goal: str = Form(...),
    caption: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Save a caption to the database
    """
    try:
        new_caption = Caption(
            goal=goal,
            caption=caption
        )
        db.add(new_caption)
        db.commit()
        db.refresh(new_caption)

        return {
            "message": "Caption saved successfully",
            "id": new_caption.id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/captions")
async def get_captions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get all saved captions
    """
    try:
        captions = db.query(Caption).order_by(Caption.created_at.desc()).offset(skip).limit(limit).all()
        return {
            "captions": [caption.to_dict() for caption in captions],
            "total": db.query(Caption).count()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "openai_configured": bool(settings.OPENAI_API_KEY)
    }
