from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
from pathlib import Path

from app.core.database import get_db
from app.core.config import settings
from app.models.caption import Caption
from app.models.location import Location
from app.services.local_research import LocalResearchService
from app.services.openai_service import OpenAIService
from app.services.quality_scorer import QualityScorer

router = APIRouter()

# Ensure uploads directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/generate-caption")
async def generate_caption(
    media: UploadFile = File(..., description="Image or video file"),
    goal: str = Form(...),
    address: str = Form(...),
    platform: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Generate a localized caption based on:
    - Uploaded image or video
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

        # Save uploaded media temporarily
        media_path = UPLOAD_DIR / media.filename
        with media_path.open("wb") as buffer:
            shutil.copyfileobj(media.file, buffer)

        # Initialize services
        research_service = LocalResearchService(api_key=settings.OPENAI_API_KEY)
        openai_service = OpenAIService(api_key=settings.OPENAI_API_KEY)

        # Step 1: Analyze the media (image or video)
        media_type = "video" if openai_service.is_video_file(media.filename) else "image"
        print(f"Analyzing {media_type}: {media.filename}")
        media_analysis = openai_service.analyze_media(str(media_path))

        # Step 2: Research local area (or use cached)
        print(f"Checking location: {address}")

        # Check if location exists in database
        existing_location = db.query(Location).filter(Location.address == address).first()

        if existing_location:
            print(f"Using cached research for {existing_location.city}, {existing_location.state}")
            local_research = {
                "city": existing_location.city,
                "state": existing_location.state,
                "is_rural": existing_location.is_rural,
                "gpt_research": existing_location.gpt_research,
                "chamber_info": existing_location.chamber_info,
                "government_info": existing_location.government_info
            }
        else:
            print(f"Researching new location: {address}")
            local_research = research_service.research_location(address)

            if "error" in local_research:
                raise HTTPException(status_code=400, detail=local_research["error"])

            # Save to database
            new_location = Location(
                address=address,
                city=local_research["city"],
                state=local_research["state"],
                is_rural=local_research["is_rural"],
                gpt_research=local_research.get("gpt_research", ""),
                chamber_info=local_research.get("chamber_info", ""),
                government_info=local_research.get("government_info", "")
            )
            db.add(new_location)
            db.commit()
            print(f"Saved location: {local_research['city']}, {local_research['state']}")

        # Step 3: Generate caption
        print(f"Generating caption for {local_research['city']}, {local_research['state']}")
        caption = openai_service.generate_caption(
            goal=goal,
            image_analysis=media_analysis,  # Works for both images and videos
            local_research=local_research,
            platform=platform
        )

        # Step 4: Score caption quality
        print("Scoring caption quality...")
        quality_scorer = QualityScorer(api_key=settings.OPENAI_API_KEY)
        quality_scores = quality_scorer.score_caption(
            caption=caption,
            goal=goal,
            location=f"{local_research['city']}, {local_research['state']}",
            image_analysis=media_analysis
        )

        # Clean up uploaded file
        media_path.unlink()

        return {
            "caption": caption,
            "location_info": {
                "city": local_research["city"],
                "state": local_research["state"],
                "is_rural": local_research["is_rural"],
                "full_research": local_research.get("gpt_research", "")
            },
            "media_analysis": media_analysis,
            "media_type": media_type,
            "quality_scores": quality_scores,
            "reasoning": {
                "media_confirmation": f"✓ Analyzed {media_type}: {media_analysis[:200]}...",
                "local_research_summary": f"✓ Researched {local_research['city']}, {local_research['state']}: {local_research.get('gpt_research', '')[:300]}...",
                "caption_strategy": f"Created localized caption for {platform} targeting {local_research['city']}, {local_research['state']} audience with goal: {goal}"
            }
        }

    except Exception as e:
        # Clean up on error
        if media_path.exists():
            media_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate-caption")
async def regenerate_caption(
    media: UploadFile = File(..., description="Image or video file"),
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

        # Save uploaded media temporarily
        media_path = UPLOAD_DIR / media.filename
        with media_path.open("wb") as buffer:
            shutil.copyfileobj(media.file, buffer)

        # Initialize services
        research_service = LocalResearchService(api_key=settings.OPENAI_API_KEY)
        openai_service = OpenAIService(api_key=settings.OPENAI_API_KEY)

        # Analyze media and research location
        media_type = "video" if openai_service.is_video_file(media.filename) else "image"
        media_analysis = openai_service.analyze_media(str(media_path))
        local_research = research_service.research_location(address)

        if "error" in local_research:
            raise HTTPException(status_code=400, detail=local_research["error"])

        # Regenerate caption
        caption = openai_service.regenerate_caption(
            goal=goal,
            image_analysis=media_analysis,
            local_research=local_research,
            platform=platform,
            previous_caption=previous_caption
        )

        # Score the regenerated caption
        print("Scoring regenerated caption quality...")
        quality_scorer = QualityScorer(api_key=settings.OPENAI_API_KEY)
        quality_scores = quality_scorer.score_caption(
            caption=caption,
            goal=goal,
            location=f"{local_research['city']}, {local_research['state']}",
            image_analysis=media_analysis
        )

        # Clean up
        media_path.unlink()

        return {
            "caption": caption,
            "location_info": {
                "city": local_research["city"],
                "state": local_research["state"],
                "is_rural": local_research["is_rural"],
                "full_research": local_research.get("gpt_research", "")
            },
            "quality_scores": quality_scores
        }

    except Exception as e:
        if media_path.exists():
            media_path.unlink()
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


@router.get("/locations")
async def get_locations(
    db: Session = Depends(get_db)
):
    """
    Get all saved Urban Air locations with completed research, sorted alphabetically by city, then state
    """
    try:
        # Only return locations where research has been completed (gpt_research exists)
        locations = db.query(Location).filter(
            Location.gpt_research != None,
            Location.gpt_research != ""
        ).order_by(Location.city, Location.state).all()

        return {
            "locations": [
                {
                    "id": loc.id,
                    "address": loc.address,
                    "city": loc.city,
                    "state": loc.state,
                    "display": f"{loc.city}, {loc.state} - {loc.address}"
                }
                for loc in locations
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/locations/{location_id}")
async def get_location(
    location_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific location by ID
    """
    try:
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")

        return location.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/locations/{location_id}")
async def delete_location(
    location_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a location by ID
    """
    try:
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")

        db.delete(location)
        db.commit()

        return {"message": "Location deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research-location")
async def research_location(
    address: str = Form(...),
    force_update: bool = Form(False),
    db: Session = Depends(get_db)
):
    """
    Re-research a location to get updated local information
    Updates existing database entry if it exists
    """
    try:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured."
            )

        research_service = LocalResearchService(api_key=settings.OPENAI_API_KEY)
        local_research = research_service.research_location(address)

        if "error" in local_research:
            raise HTTPException(status_code=400, detail=local_research["error"])

        # Check if location exists and update it
        existing_location = db.query(Location).filter(Location.address == address).first()

        if existing_location:
            print(f"Updating existing location: {existing_location.city}, {existing_location.state}")
            existing_location.city = local_research["city"]
            existing_location.state = local_research["state"]
            existing_location.is_rural = local_research["is_rural"]
            existing_location.gpt_research = local_research.get("gpt_research", "")
            existing_location.chamber_info = local_research.get("chamber_info", "")
            existing_location.government_info = local_research.get("government_info", "")
            db.commit()
            print("Location updated successfully")
        else:
            # Save new location
            new_location = Location(
                address=address,
                city=local_research["city"],
                state=local_research["state"],
                is_rural=local_research["is_rural"],
                gpt_research=local_research.get("gpt_research", ""),
                chamber_info=local_research.get("chamber_info", ""),
                government_info=local_research.get("government_info", "")
            )
            db.add(new_location)
            db.commit()
            print(f"New location saved: {local_research['city']}, {local_research['state']}")

        return {
            "location_info": {
                "city": local_research["city"],
                "state": local_research["state"],
                "is_rural": local_research["is_rural"],
                "full_research": local_research.get("gpt_research", "")
            },
            "full_research": local_research.get("gpt_research", ""),
            "chamber_info": local_research.get("chamber_info", ""),
            "government_info": local_research.get("government_info", "")
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
