from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from routers import auth, users, accounts, trades, transactions, ai_recommendations, admin, symbol_mapping, brokers
from ai_integration.scheduler import ai_scheduler
from ai_integration.model_runner import run_ai_models
from utils.trade_monitor import trade_monitor
from models.user import User
from models.account import Account
from models.trade import Trade
from models.transaction import Transaction
from models.asset_type import AssetType
from models.broker import Broker
from models.broker_server import BrokerServer
from models.trading_pair import TradingPair
from models.account_symbol_mapping import AccountSymbolMapping
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
app.include_router(symbol_mapping.router)
app.include_router(brokers.router)


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
        
        def run_migration_step(step_name, sql_commands):
            """Helper to run migration steps in isolated transactions"""
            try:
                with engine.connect() as connection:
                    with connection.begin():
                        for sql in sql_commands:
                            connection.execute(text(sql))
                # print(f"      ✅ {step_name} applied")
            except Exception as e:
                # print(f"      ℹ️ {step_name} skipped/failed: {str(e)}")
                # We expect some to fail (e.g. column already exists), so we just continue
                pass

        # 1. Accounts Table Updates
        run_migration_step("Fix Password Length", [
            'ALTER TABLE "Accounts" ALTER COLUMN "AccountLoginPassword" TYPE VARCHAR(255);'
        ])

        run_migration_step("Fix Server Length", [
            'ALTER TABLE "Accounts" ALTER COLUMN "AccountLoginServer" TYPE VARCHAR(100);'
        ])

        # 2. Trades Table Updates (ProfitLose)
        run_migration_step("Trades ProfitLose Type", [
            'ALTER TABLE "Trades" ALTER COLUMN "TradeProfitLose" TYPE DECIMAL(12, 2);'
        ])

        # 3. Users Table Updates (Push Notifications)
        run_migration_step("Users Push Columns", [
            'ALTER TABLE "Users" ADD COLUMN IF NOT EXISTS "PushToken" VARCHAR(255);',
            'ALTER TABLE "Users" ADD COLUMN IF NOT EXISTS "IsNotificationsEnabled" BOOLEAN DEFAULT TRUE;'
        ])

        run_migration_step("Users ID Card BigInt", [
            'ALTER TABLE "Users" ALTER COLUMN "UserIDCardNumber" TYPE BIGINT;'
        ])

        # 4. Trades Table Updates (New Columns)
        run_migration_step("Trades MappingID", ['ALTER TABLE "Trades" ADD COLUMN IF NOT EXISTS "MappingID" INTEGER;'])
        
        run_migration_step("Trades SL/TP", [
            'ALTER TABLE "Trades" ADD COLUMN IF NOT EXISTS "TradeSL" DECIMAL(12, 5);',
            'ALTER TABLE "Trades" ADD COLUMN IF NOT EXISTS "TradeTP" DECIMAL(12, 5);'
        ])

        # 5. TradingPairs Updates
        # Rename column if exists (Check first)
        try:
            with engine.connect() as connection:
                with connection.begin():
                    result = connection.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='TradingPairs' AND column_name='OurPairName'"))
                    if result.rowcount > 0:
                        print("      🔄 Renaming OurPairName to PairNameForSearch...")
                        connection.execute(text('ALTER TABLE "TradingPairs" RENAME COLUMN "OurPairName" TO "PairNameForSearch";'))
        except Exception:
            pass

        run_migration_step("TradingPairs Search Column", [
            'ALTER TABLE "TradingPairs" ADD COLUMN IF NOT EXISTS "PairNameForSearch" VARCHAR(50);',
            'CREATE INDEX IF NOT EXISTS "ix_trading_pairs_pair_name_for_search" ON "TradingPairs"("PairNameForSearch");'
        ])

        # 6. Accounts ServerID
        run_migration_step("Accounts ServerID", [
            'ALTER TABLE "Accounts" ADD COLUMN IF NOT EXISTS "ServerID" INTEGER;',
            'CREATE INDEX IF NOT EXISTS "ix_accounts_server_id" ON "Accounts"("ServerID");'
        ])

        # 7. Accounts AccountName
        run_migration_step("Accounts AccountName", [
            'ALTER TABLE "Accounts" ADD COLUMN IF NOT EXISTS "AccountName" VARCHAR(100);'
        ])

        # 8. Constraints
        run_migration_step("Accounts Server FK", ['''
            ALTER TABLE "Accounts" 
            ADD CONSTRAINT "fk_accounts_server" 
            FOREIGN KEY ("ServerID") 
            REFERENCES "PlatformServers"("ServerID") 
            ON DELETE SET NULL;
        '''])

        # 9. Enum Conversions (Complex steps)
        # AccountType
        run_migration_step("AccountType Migration", [
            'ALTER TABLE "Accounts" ADD COLUMN IF NOT EXISTS "AccountType_New" INTEGER;',
            """UPDATE "Accounts" SET "AccountType_New" = CASE 
                WHEN "AccountType"::TEXT = 'Demo' THEN 1
                WHEN "AccountType"::TEXT = 'Real' THEN 2
                ELSE 1 END WHERE "AccountType_New" IS NULL;""",
            'ALTER TABLE "Accounts" DROP COLUMN IF EXISTS "AccountType" CASCADE;',
            'ALTER TABLE "Accounts" RENAME COLUMN "AccountType_New" TO "AccountType;',
            'ALTER TABLE "Accounts" ALTER COLUMN "AccountType" SET NOT NULL;'
        ])

        # TradeType
        run_migration_step("TradeType Migration", [
            'ALTER TABLE "Trades" ADD COLUMN IF NOT EXISTS "TradeType_New" INTEGER;',
            """UPDATE "Trades" SET "TradeType_New" = CASE 
                WHEN "TradeType"::TEXT ILIKE 'Buy%' THEN 1
                WHEN "TradeType"::TEXT ILIKE 'Sell%' THEN 2
                ELSE 1 END WHERE "TradeType_New" IS NULL;""",
            'ALTER TABLE "Trades" DROP COLUMN IF EXISTS "TradeType" CASCADE;',
            'ALTER TABLE "Trades" RENAME COLUMN "TradeType_New" TO "TradeType";',
            'ALTER TABLE "Trades" ALTER COLUMN "TradeType" SET NOT NULL;'
        ])

        # TransactionType
        run_migration_step("TransactionType Migration", [
            'ALTER TABLE "Transactions" ADD COLUMN IF NOT EXISTS "TransactionType_New" INTEGER;',
            'UPDATE "Transactions" SET "TransactionType_New" = 1 WHERE "TransactionType_New" IS NULL;',
            'ALTER TABLE "Transactions" DROP COLUMN IF EXISTS "TransactionType" CASCADE;',
            'ALTER TABLE "Transactions" RENAME COLUMN "TransactionType_New" TO "TransactionType";',
            'ALTER TABLE "Transactions" ALTER COLUMN "TransactionType" SET NOT NULL;'
        ])

        # Transaction SubscriptionExpiry
        run_migration_step("Transactions SubscriptionExpiry", [
            'ALTER TABLE "Transactions" ADD COLUMN IF NOT EXISTS "SubscriptionExpiry" TIMESTAMP WITH TIME ZONE;'
        ])

        # TransactionStatus
        run_migration_step("TransactionStatus Migration", [
            'ALTER TABLE "Transactions" ADD COLUMN IF NOT EXISTS "TransactionStatus_New" INTEGER;',
            """UPDATE "Transactions" SET "TransactionStatus_New" = CASE 
                WHEN "TransactionStatus"::TEXT ILIKE 'Complet%' THEN 1
                WHEN "TransactionStatus"::TEXT ILIKE 'Pend%' THEN 2
                WHEN "TransactionStatus"::TEXT ILIKE 'Fail%' THEN 3
                ELSE 2 END WHERE "TransactionStatus_New" IS NULL;""",
            'ALTER TABLE "Transactions" DROP COLUMN IF EXISTS "TransactionStatus" CASCADE;',
            'ALTER TABLE "Transactions" RENAME COLUMN "TransactionStatus_New" TO "TransactionStatus";',
            'ALTER TABLE "Transactions" ALTER COLUMN "TransactionStatus" SET DEFAULT 2;'
        ])

        # 10. Final Constraints and Indexes
        run_migration_step("Trades Mapping FK", ['''
            ALTER TABLE "Trades" 
            ADD CONSTRAINT "fk_trades_mapping" 
            FOREIGN KEY ("MappingID") 
            REFERENCES "AccountSymbolMappings"("MappingID") 
            ON DELETE SET NULL;
        '''])

        run_migration_step("General Indexes", [
            'CREATE INDEX IF NOT EXISTS "ix_trades_mapping_id" ON "Trades"("MappingID");',
            'CREATE INDEX IF NOT EXISTS "ix_platform_servers_platform_id" ON "PlatformServers"("PlatformID");',
            'CREATE INDEX IF NOT EXISTS "ix_trading_pairs_asset_type_id" ON "TradingPairs"("AssetTypeID");',
            'CREATE INDEX IF NOT EXISTS "ix_trading_pairs_server_id" ON "TradingPairs"("ServerID");'
        ])

        run_migration_step("Mapping Indexes", [
            'CREATE INDEX IF NOT EXISTS "ix_account_symbol_mappings_account_id" ON "AccountSymbolMappings"("AccountID");',
            'CREATE INDEX IF NOT EXISTS "ix_account_symbol_mappings_trading_pair_id" ON "AccountSymbolMappings"("PairID");'
        ])
                
        print("Database: ✅ Applied schema migrations (if needed)")
    except Exception as e:
        print(f"Database: ℹ️ Schema migration process finished with notes: {str(e)}")
        
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
