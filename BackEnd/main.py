from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from routers import auth, users, accounts, trades, transactions, ai_recommendations, admin
from ai_integration.scheduler import ai_scheduler
from ai_integration.model_runner import run_ai_models
from utils.trade_monitor import trade_monitor
from models.user import User
from models.account import Account
from models.trade import Trade
from models.transaction import Transaction
import os
import time

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Trading App API",
    description="Python FastAPI backend for trading application with AI integration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    print(f"\n{'='*60}", flush=True)
    print(f"📨 INCOMING REQUEST", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"🌐 Method: {request.method}", flush=True)
    print(f"🔗 URL: {request.url.path}", flush=True)
    print(f"📍 Client: {request.client.host if request.client else 'Unknown'}", flush=True)
    
    try:
        response = await call_next(request)
        
        process_time = time.time() - start_time
        print(f"✅ Response Status: {response.status_code}", flush=True)
        print(f"⏱️  Process Time: {process_time:.3f}s", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        return response
    except Exception as e:
        import traceback
        print(f"❌ UNHANDLED EXCEPTION IN MIDDLEWARE", flush=True)
        print(f"⚠️ Error: {str(e)}", flush=True)
        traceback.print_exc()
        print(f"{'='*60}\n", flush=True)
        raise e

# Global Exception Handler
from fastapi.responses import JSONResponse
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"🔥 GLOBAL EXCEPTION CAUGHT", flush=True)
    print(f"⚠️ Error: {str(exc)}", flush=True)
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(trades.router)
app.include_router(transactions.router)
app.include_router(ai_recommendations.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Trading App API (Python FastAPI)",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "ai_scheduler": "running" if ai_scheduler.is_running else "stopped",
        "trade_monitor": "running"
    }


@app.on_event("startup")
async def startup_event():
    """
    Startup event - Initialize AI scheduler
    """
    print("=" * 50)
    print("Starting Trading App API (Python FastAPI)")
    print("=" * 50)
    
    # Test Database Connection
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print(f"Database: ✅ Connected to PostgreSQL")
    except Exception as e:
        print(f"Database: ❌ Connection Failed!")
        print(f"Error: {str(e)}")
        print("Please check your database credentials and ensure PostgreSQL is running.")
        
    # Auto-migration for Accounts table (Fix for VARCHAR limit)
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            # Use explicit transaction for DDL
            with connection.begin():
                connection.execute(text('ALTER TABLE "Accounts" ALTER COLUMN "AccountLoginPassword" TYPE VARCHAR(255);'))
                connection.execute(text('ALTER TABLE "Accounts" ALTER COLUMN "AccountLoginServer" TYPE VARCHAR(100);'))
                # Migration for TradeTicket - REMOVED as we now use TradeID as Ticket
                # connection.execute(text('ALTER TABLE "Trades" ADD COLUMN IF NOT EXISTS "TradeTicket" INTEGER;'))
                # Migration for TradeProfitLose (Integer -> Decimal)
                connection.execute(text('ALTER TABLE "Trades" ALTER COLUMN "TradeProfitLose" TYPE DECIMAL(12, 2);'))
                
                # Migration for Users (Push Notifications)
                connection.execute(text('ALTER TABLE "Users" ADD COLUMN IF NOT EXISTS "PushToken" VARCHAR(255);'))
                connection.execute(text('ALTER TABLE "Users" ADD COLUMN IF NOT EXISTS "IsNotificationsEnabled" BOOLEAN DEFAULT TRUE;'))
        print("Database: ✅ Applied schema migration for Accounts, Trades, and Users tables")
    except Exception as e:
        # Ignore if it fails (likely already applied or table doesn't exist yet)
        print(f"Database: ℹ️ Schema migration skipped: {str(e)}")
        
    print(f"Authentication: JWT enabled")
    print(f"AI Integration: Enabled")
    print("=" * 50)
    
    # Start AI scheduler (runs every 15 minutes)
    ai_scheduler.start(run_ai_models, interval_minutes=15)
    print("AI Scheduler started - Running every 15 minutes")
    
    # Start trade monitor (runs every 30 seconds)
    import asyncio
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    
    trade_scheduler = AsyncIOScheduler()
    trade_scheduler.add_job(
        trade_monitor.check_and_update_closed_trades,
        trigger=IntervalTrigger(seconds=30),
        id='trade_monitor_job',
        name='Trade Monitor Job',
        replace_existing=True
    )
    trade_scheduler.start()
    print("Trade Monitor started - Running every 30 seconds")
    print("=" * 50)
    print(f"API Documentation: http://localhost:{os.getenv('PORT', 3000)}/docs")
    print("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event - Stop AI scheduler
    """
    print("\n" + "=" * 50)
    print("Shutting down Trading App API...")
    ai_scheduler.stop()
    print("AI Scheduler stopped")
    print("=" * 50)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
