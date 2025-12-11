"""
API Router for Platform and Server Management
Provides endpoints for platform/server selection in account creation UI
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models.platform import Platform
from models.platform_server import PlatformServer
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/platforms", tags=["Platforms & Servers"])


# ============= Schemas =============

class PlatformResponse(BaseModel):
    platform_id: int
    platform_name: str
    
    class Config:
        from_attributes = True


class ServerResponse(BaseModel):
    server_id: int
    platform_id: int
    server_name: str
    platform_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============= Endpoints =============

@router.get("/", response_model=List[PlatformResponse])
async def get_all_platforms(
    search: Optional[str] = Query(None, description="Search platforms by name"),
    db: Session = Depends(get_db)
):
    """
    Get all platforms with optional search/filter.
    Used for autocomplete dropdown in account creation.
    """
    query = db.query(Platform)
    
    if search:
        # Filter platforms that start with or contain the search term
        query = query.filter(Platform.PlatformName.ilike(f"%{search}%"))
    
    platforms = query.order_by(Platform.PlatformName).all()
    
    return [
        {
            'platform_id': p.PlatformID,
            'platform_name': p.PlatformName
        }
        for p in platforms
    ]


@router.get("/{platform_id}/servers", response_model=List[ServerResponse])
async def get_platform_servers(
    platform_id: int,
    search: Optional[str] = Query(None, description="Search servers by name"),
    db: Session = Depends(get_db)
):
    """
    Get all servers for a specific platform.
    Used for server dropdown after platform selection.
    """
    # Verify platform exists
    platform = db.query(Platform).filter(Platform.PlatformID == platform_id).first()
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform not found"
        )
    
    query = db.query(PlatformServer).filter(PlatformServer.PlatformID == platform_id)
    
    if search:
        # Filter servers that contain the search term
        query = query.filter(PlatformServer.ServerName.ilike(f"%{search}%"))
    
    servers = query.order_by(PlatformServer.ServerName).all()
    
    return [
        {
            'server_id': s.ServerID,
            'platform_id': s.PlatformID,
            'server_name': s.ServerName,
            'platform_name': platform.PlatformName
        }
        for s in servers
    ]


@router.get("/servers/all", response_model=List[ServerResponse])
async def get_all_servers(
    search: Optional[str] = Query(None, description="Search servers by name"),
    db: Session = Depends(get_db)
):
    """
    Get all servers across all platforms.
    Includes platform name for each server.
    """
    query = db.query(
        PlatformServer.ServerID,
        PlatformServer.PlatformID,
        PlatformServer.ServerName,
        Platform.PlatformName
    ).join(Platform, PlatformServer.PlatformID == Platform.PlatformID)
    
    if search:
        query = query.filter(PlatformServer.ServerName.ilike(f"%{search}%"))
    
    servers = query.order_by(Platform.PlatformName, PlatformServer.ServerName).all()
    
    return [
        {
            'server_id': s.ServerID,
            'platform_id': s.PlatformID,
            'server_name': s.ServerName,
            'platform_name': s.PlatformName
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
        PlatformServer.ServerID,
        PlatformServer.PlatformID,
        PlatformServer.ServerName,
        Platform.PlatformName
    ).join(Platform, PlatformServer.PlatformID == Platform.PlatformID).filter(
        PlatformServer.ServerID == server_id
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return {
        'server_id': server.ServerID,
        'platform_id': server.PlatformID,
        'server_name': server.ServerName,
        'platform_name': server.PlatformName
    }
