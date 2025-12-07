from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from utils.dependencies import get_current_user
from ai_integration.model_runner import ai_runner, run_ai_models
from ai_integration.scheduler import ai_scheduler

router = APIRouter(prefix="/api/ai", tags=["AI Recommendations"])


@router.get("/recommendations")
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get latest AI trading recommendations
    """
    try:
        recommendations = ai_runner.get_latest_recommendations()
        
        return {
            "success": True,
            "recommendations": recommendations,
            "message": "Latest AI recommendations retrieved successfully"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving recommendations: {str(e)}"
        )


@router.post("/trigger-analysis")
async def trigger_analysis(
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger AI analysis (runs immediately)
    """
    try:
        result = ai_scheduler.run_now(run_ai_models)
        
        return {
            "success": True,
            "result": result,
            "message": "AI analysis triggered successfully"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running AI analysis: {str(e)}"
        )


@router.get("/status")
async def get_ai_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get AI system status
    """
    return {
        "scheduler_running": ai_scheduler.is_running,
        "interval_minutes": 15,
        "message": "AI system status retrieved successfully"
    }
