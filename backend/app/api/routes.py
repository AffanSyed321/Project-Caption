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
from app.services.caption_chat import CaptionChatService

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
    video_description: str = Form(None, description="User's description of video content (required for videos)"),
    db: Session = Depends(get_db)
):
    """
    Generate a localized caption based on:
    - Uploaded image or video
    - Goal of the post
    - Urban Air location address
    - Target platform (Facebook or Instagram)
    """
    media_path = None
    try:
        # Validate API key
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in environment."
            )

        # Save uploaded media temporarily
        print(f"[STEP 0] Saving uploaded media: {media.filename}")
        media_path = UPLOAD_DIR / media.filename
        with media_path.open("wb") as buffer:
            shutil.copyfileobj(media.file, buffer)
        print(f"[STEP 0] ✓ Media saved to {media_path}")

        # Initialize services
        print("[STEP 1] Initializing services...")
        try:
            research_service = LocalResearchService(api_key=settings.OPENAI_API_KEY)
            print("[STEP 1] ✓ Research service initialized")
        except Exception as e:
            print(f"[STEP 1] ✗ Failed to initialize research service: {e}")
            raise
        
        try:
            openai_service = OpenAIService(api_key=settings.OPENAI_API_KEY)
            print("[STEP 1] ✓ OpenAI service initialized")
        except Exception as e:
            print(f"[STEP 1] ✗ Failed to initialize OpenAI service: {e}")
            raise

        # Step 2: Analyze the media (image or video)
        media_type = "video" if openai_service.is_video_file(media.filename) else "image"
        print(f"[STEP 2] Analyzing {media_type}: {media.filename}")
        try:
            # For videos, use user's description instead of AI analysis (cost-effective!)
            if media_type == "video":
                if not video_description:
                    raise HTTPException(
                        status_code=400,
                        detail="Video description is required when uploading a video"
                    )
                media_analysis = f"Video content (described by user): {video_description}"
                print(f"[STEP 2] ✓ Using user's video description")
            else:
                # For images, use AI analysis
                media_analysis = openai_service.analyze_media(str(media_path))
                print(f"[STEP 2] ✓ Media analyzed: {media_analysis[:100]}...")
        except HTTPException:
            raise
        except Exception as e:
            print(f"[STEP 2] ✗ Media analysis failed: {e}")
            raise

        # Step 3: Research local area (or use cached)
        print(f"[STEP 3] Checking location: {address}")

        # Check if location exists in database
        existing_location = db.query(Location).filter(Location.address == address).first()

        if existing_location:
            print(f"[STEP 3] ✓ Using cached research for {existing_location.city}, {existing_location.state}")
            local_research = {
                "city": existing_location.city,
                "state": existing_location.state,
                "is_rural": existing_location.is_rural,
                "gpt_research": existing_location.gpt_research,
                "chamber_info": existing_location.chamber_info,
                "government_info": existing_location.government_info
            }
        else:
            print(f"[STEP 3] Researching new location: {address}")
            try:
                local_research = research_service.research_location(address)
                if "error" in local_research:
                    raise HTTPException(status_code=400, detail=local_research["error"])
                print(f"[STEP 3] ✓ Location researched: {local_research['city']}, {local_research['state']}")
            except Exception as e:
                print(f"[STEP 3] ✗ Location research failed: {e}")
                raise

            # Save to database
            try:
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
                print(f"[STEP 3] ✓ Saved location to database")
            except Exception as e:
                print(f"[STEP 3] ✗ Database save failed: {e}")
                raise

        # Step 4: Generate caption
        print(f"[STEP 4] Generating caption for {local_research['city']}, {local_research['state']}")
        try:
            caption = openai_service.generate_caption(
                goal=goal,
                image_analysis=media_analysis,
                local_research=local_research,
                platform=platform
            )
            print(f"[STEP 4] ✓ Caption generated: {caption[:100]}...")
        except Exception as e:
            print(f"[STEP 4] ✗ Caption generation failed: {e}")
            import traceback
            print(f"[STEP 4] Full traceback:\n{traceback.format_exc()}")
            raise

        # Step 5: Score caption quality
        print("[STEP 5] Scoring caption quality...")
        try:
            quality_scorer = QualityScorer(api_key=settings.OPENAI_API_KEY)
            quality_scores = quality_scorer.score_caption(
                caption=caption,
                goal=goal,
                location=f"{local_research['city']}, {local_research['state']}",
                image_analysis=media_analysis
            )
            print(f"[STEP 5] ✓ Quality scored")
        except Exception as e:
            print(f"[STEP 5] ✗ Quality scoring failed: {e}")
            # Don't fail the whole request if quality scoring fails
            quality_scores = {"overall": "N/A", "error": str(e)}

        # Clean up uploaded file
        media_path.unlink()
        print("[STEP 6] ✓ Cleanup complete")

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

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        if media_path and media_path.exists():
            media_path.unlink()
        raise
    except Exception as e:
        # Clean up on error
        if media_path and media_path.exists():
            media_path.unlink()
        
        # Return detailed error information
        import traceback
        error_details = {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        print(f"[ERROR] {error_details}")
        raise HTTPException(status_code=500, detail=str(error_details))


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


@router.post("/chat-edit-caption")
async def chat_edit_caption(
    current_caption: str = Form(...),
    user_instruction: str = Form(...),
    chat_history: str = Form("[]"),  # JSON string of chat history
    city: str = Form(...),
    state: str = Form(...),
    goal: str = Form(...),
    platform: str = Form(...)
):
    """
    Edit caption using conversational AI chat.
    Maintains chat history for context.
    """
    try:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured."
            )
        
        import json
        history = json.loads(chat_history) if chat_history else []
        
        chat_service = CaptionChatService(api_key=settings.OPENAI_API_KEY)
        
        context = {
            "city": city,
            "state": state,
            "goal": goal,
            "platform": platform
        }
        
        edited_caption = chat_service.chat_edit_caption(
            current_caption=current_caption,
            user_instruction=user_instruction,
            chat_history=history,
            context=context
        )
        
        return {
            "edited_caption": edited_caption,
            "success": True
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


@router.get("/test-openai")
async def test_openai():
    """
    Diagnostic endpoint to test OpenAI API connectivity.
    Returns detailed information about connection success/failure.
    """
    try:
        if not settings.OPENAI_API_KEY:
            return {
                "status": "error",
                "error": "OpenAI API key not configured",
                "api_key_present": False
            }
        
        from openai import OpenAI
        import time
        
        # Test with minimal timeout first
        start_time = time.time()
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=30.0,
            max_retries=2
        )
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=5
        )
        
        elapsed_time = time.time() - start_time
        
        return {
            "status": "success",
            "api_key_present": True,
            "api_key_prefix": settings.OPENAI_API_KEY[:10] + "...",
            "response": response.choices[0].message.content,
            "model_used": response.model,
            "elapsed_seconds": round(elapsed_time, 2),
            "message": "OpenAI API connection successful!"
        }
    
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "api_key_present": bool(settings.OPENAI_API_KEY),
            "api_key_prefix": settings.OPENAI_API_KEY[:10] + "..." if settings.OPENAI_API_KEY else None
        }
