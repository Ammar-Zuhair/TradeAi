from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from utils.dependencies import get_current_user
from utils.notifications import send_push_notification
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["Admin"])

class MessageRequest(BaseModel):
    title: str
    body: str
    target_user_id: int = None # If None, send to all (broadcast)

@router.post("/send-message")
async def send_admin_message(
    request: MessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send admin message to users"""
    # In a real app, check if current_user is admin
    
    count = 0
    
    if request.target_user_id:
        # Send to specific user
        user = db.query(User).filter(User.UserID == request.target_user_id).first()
        if user and user.IsNotificationsEnabled and user.PushToken:
            send_push_notification(user.PushToken, request.title, request.body)
            count = 1
    else:
        # Broadcast to all users with notifications enabled
        users = db.query(User).filter(
            User.IsNotificationsEnabled == True,
            User.PushToken.isnot(None)
        ).all()
        
        for user in users:
            if user.PushToken:
                send_push_notification(user.PushToken, request.title, request.body)
                count += 1
                
    return {"message": f"Message sent to {count} users"}
