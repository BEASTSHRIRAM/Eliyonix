"""
Recommendation Scheduler
Runs the RecommendationAgent on a cron schedule (every 60 minutes by default)
Can also be triggered on-demand
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable
from .vector_store import get_vector_store

logger = logging.getLogger(__name__)


class RecommendationScheduler:
    """
    Scheduler for running recommendation agent on a regular cadence
    Uses asyncio for background task execution
    """
    
    def __init__(
        self,
        invoke_callback: Callable,
        interval_minutes: int = 60,
        auto_start: bool = False
    ):
        """
        Initialize scheduler
        
        Args:
            invoke_callback: Async function to call for recommendation generation
            interval_minutes: Interval between runs in minutes (default: 60)
            auto_start: Whether to automatically start the scheduler
        """
        self.invoke_callback = invoke_callback
        self.interval_minutes = interval_minutes
        self.is_running = False
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.task: Optional[asyncio.Task] = None
        
        if auto_start:
            self.start()
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        self.is_running = True
        self.next_run = datetime.now() + timedelta(minutes=self.interval_minutes)
        self.task = asyncio.create_task(self._run_loop())
        logger.info(
            f"Started recommendation scheduler (interval: {self.interval_minutes} min, "
            f"next run: {self.next_run.isoformat()})"
        )
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler not running")
            return
        
        self.is_running = False
        if self.task:
            self.task.cancel()
        logger.info("Stopped recommendation scheduler")
    
    async def _run_loop(self):
        """Main scheduler loop"""
        try:
            while self.is_running:
                # Calculate time until next run
                now = datetime.now()
                if self.next_run and now >= self.next_run:
                    logger.info(f"Triggering scheduled recommendation generation")
                    try:
                        await self.invoke_callback()
                        self.last_run = datetime.now()
                    except Exception as e:
                        logger.error(f"Error in scheduled recommendation run: {e}")
                    
                    # Schedule next run
                    self.next_run = datetime.now() + timedelta(minutes=self.interval_minutes)
                    logger.info(f"Next recommendation run scheduled for {self.next_run.isoformat()}")
                
                # Sleep for a short interval before checking again
                await asyncio.sleep(30)  # Check every 30 seconds
        except asyncio.CancelledError:
            logger.info("Recommendation scheduler task cancelled")
        except Exception as e:
            logger.error(f"Error in recommendation scheduler loop: {e}")
    
    def trigger_now(self):
        """
        Trigger recommendation generation immediately
        Doesn't affect the regular schedule
        """
        asyncio.create_task(self.invoke_callback())
        logger.info("Triggered on-demand recommendation generation")
    
    def get_status(self) -> dict:
        """Get current scheduler status"""
        time_until_next = None
        if self.next_run:
            delta = self.next_run - datetime.now()
            time_until_next = max(0, int(delta.total_seconds() / 60))  # Minutes
        
        return {
            "is_running": self.is_running,
            "interval_minutes": self.interval_minutes,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "time_until_next_minutes": time_until_next,
            "vector_store_stats": get_vector_store().get_stats(),
        }


# Global scheduler instance
_scheduler: Optional[RecommendationScheduler] = None


def get_scheduler() -> Optional[RecommendationScheduler]:
    """Get the global recommendation scheduler"""
    return _scheduler


def set_scheduler(scheduler: RecommendationScheduler) -> None:
    """Set the global recommendation scheduler"""
    global _scheduler
    _scheduler = scheduler


def create_scheduler(
    invoke_callback: Callable,
    interval_minutes: int = 60
) -> RecommendationScheduler:
    """
    Create and set the global recommendation scheduler
    
    Args:
        invoke_callback: Async function to call for recommendation generation
        interval_minutes: Interval between runs in minutes
    
    Returns:
        The created scheduler instance
    """
    scheduler = RecommendationScheduler(
        invoke_callback=invoke_callback,
        interval_minutes=interval_minutes,
        auto_start=True
    )
    set_scheduler(scheduler)
    return scheduler
