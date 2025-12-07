"""
AI Scheduler - Runs AI models every 15 minutes
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIScheduler:
    """Background scheduler for AI model execution"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start(self, job_function, interval_minutes=15):
        """
        Start the scheduler
        
        Args:
            job_function: Function to run periodically
            interval_minutes: Interval in minutes (default: 15)
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Add job to run every N minutes
        self.scheduler.add_job(
            job_function,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='ai_analysis_job',
            name='AI Analysis Job',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"AI Scheduler started - Running every {interval_minutes} minutes")
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("AI Scheduler stopped")
    
    def run_now(self, job_function):
        """Run the job immediately (for manual trigger)"""
        logger.info("Running AI analysis manually...")
        try:
            result = job_function()
            logger.info(f"Manual AI analysis completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in manual AI analysis: {str(e)}")
            raise


# Global scheduler instance
ai_scheduler = AIScheduler()
