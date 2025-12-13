"""
API Router for Broker and Server Management
Provides endpoints for broker/server selection in account creation UI
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models.broker import Broker
from models.broker_server import BrokerServer
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/brokers", tags=["Brokers & Servers"])


# ============= Schemas =============

class BrokerResponse(BaseModel):
    broker_id: int
    broker_name: str
    
    class Config:
        from_attributes = True


class ServerResponse(BaseModel):
    server_id: int
    broker_id: int
    server_name: str
    broker_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============= Endpoints =============

@router.get("/", response_model=List[BrokerResponse])
async def get_all_brokers(
    search: Optional[str] = Query(None, description="Search brokers by name"),
    db: Session = Depends(get_db)
):
    """
    Get all brokers with optional search/filter.
    Used for autocomplete dropdown in account creation.
    """
    query = db.query(Broker)
    
    if search:
        # Filter brokers that start with or contain the search term
        query = query.filter(Broker.BrokerName.ilike(f"%{search}%"))
    
    brokers = query.order_by(Broker.BrokerName).all()
    
    return [
        {
            'broker_id': b.BrokerID,
            'broker_name': b.BrokerName
        }
        for b in brokers
    ]


@router.get("/{broker_id}/servers", response_model=List[ServerResponse])
async def get_broker_servers(
    broker_id: int,
    search: Optional[str] = Query(None, description="Search servers by name"),
    db: Session = Depends(get_db)
):
    """
    Get all servers for a specific broker.
    Used for server dropdown after broker selection.
    """
    # Verify broker exists
    broker = db.query(Broker).filter(Broker.BrokerID == broker_id).first()
    if not broker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker not found"
        )
    
    query = db.query(BrokerServer).filter(BrokerServer.BrokerID == broker_id)
    
    if search:
        # Filter servers that contain the search term
        query = query.filter(BrokerServer.ServerName.ilike(f"%{search}%"))
    
    servers = query.order_by(BrokerServer.ServerName).all()
    
    return [
        {
            'server_id': s.ServerID,
            'broker_id': s.BrokerID,
            'server_name': s.ServerName,
            'broker_name': broker.BrokerName
        }
        for s in servers
    ]


@router.get("/servers/all", response_model=List[ServerResponse])
async def get_all_servers(
    search: Optional[str] = Query(None, description="Search servers by name"),
    db: Session = Depends(get_db)
):
    """
    Get all servers across all brokers.
    Includes broker name for each server.
    """
    query = db.query(
        BrokerServer.ServerID,
        BrokerServer.BrokerID,
        BrokerServer.ServerName,
        Broker.BrokerName
    ).join(Broker, BrokerServer.BrokerID == Broker.BrokerID)
    
    if search:
        query = query.filter(BrokerServer.ServerName.ilike(f"%{search}%"))
    
    servers = query.order_by(Broker.BrokerName, BrokerServer.ServerName).all()
    
    return [
        {
            'server_id': s.ServerID,
            'broker_id': s.BrokerID,
            'server_name': s.ServerName,
            'broker_name': s.BrokerName
        }
        for s in servers
    ]


@router.get("/servers/{server_id}", response_model=ServerResponse)
async def get_server_by_id(
    server_id: int,
    db: Session = Depends(get_db)
):
    """
    Get server details by ID.
    """
    server = db.query(
        BrokerServer.ServerID,
        BrokerServer.BrokerID,
        BrokerServer.ServerName,
        Broker.BrokerName
    ).join(Broker, BrokerServer.BrokerID == Broker.BrokerID).filter(
        BrokerServer.ServerID == server_id
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return {
        'server_id': server.ServerID,
        'broker_id': server.BrokerID,
        'server_name': server.ServerName,
        'broker_name': server.BrokerName
    }
