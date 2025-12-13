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


# ============= Trading Pair Management =============

class TradingPairCreate(BaseModel):
    pair_name: str
    asset_type_id: int

@router.post("/pairs")
async def create_trading_pair(
    request: TradingPairCreate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user) # Uncomment in production
):
    """
    Add a new trading pair and automatically map it to all active accounts.
    """
    try:
        from models.trading_pair import TradingPair
        from utils.mt5_symbols import update_mappings_for_new_pair
        
        # Check if exists
        exists = db.query(TradingPair).filter(
            TradingPair.PairNameForSearch == request.pair_name
        ).first()
        
        if exists:
            # If it already exists, maybe we just want to re-run mapping?
            # For now, let's allow re-running mapping even if pair exists
            pair = exists
            created = False
        else:
            # Create new pair
            pair = TradingPair(
                PairNameForSearch=request.pair_name,
                AssetTypeID=request.asset_type_id
            )
            db.add(pair)
            db.commit()
            db.refresh(pair)
            created = True
        
        # Trigger Auto-Mapping
        print(f"🚀 Admin added pair '{request.pair_name}'. Triggering auto-mapping...")
        stats = update_mappings_for_new_pair(pair.PairID, request.pair_name)
        
        return {
            "message": "Trading pair processed successfully",
            "created": created,
            "pair_id": pair.PairID,
            "mapping_stats": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create trading pair: {str(e)}"
        )
