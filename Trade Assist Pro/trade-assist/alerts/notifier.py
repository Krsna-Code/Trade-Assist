from apscheduler.schedulers.background import BackgroundScheduler
import logging, json
from datetime import datetime, timezone
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertNotifier:
    def __init__(self, alert_threshold: float = 70.0):
        self.alert_threshold = alert_threshold
        self.scheduler = BackgroundScheduler()
        self.alerts = []
        self._callback = None

    def check_and_alert(self, recommendation: dict):
        score = recommendation.get("composite_score", 50.0)
        ticker = recommendation.get("ticker", "UNKNOWN")
        direction = recommendation.get("recommendation", "HOLD")

        if score > self.alert_threshold or score < (100 - self.alert_threshold):
            alert = {
                "ticker": ticker,
                "score": score,
                "direction": direction,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": f"Alert: {ticker} scored {score:.1f} -> {direction}",
            }
            self.alerts.append(alert)
            logger.info("TRADE ALERT | %s", json.dumps(alert))
            return alert
        return None

    def start_scheduler(self, interval_minutes: int = 5):
        if self._callback is None:
            logger.warning("No callback registered; scheduler will run but do nothing.")
            return

        self.scheduler.add_job(
            self._callback,
            "interval",
            minutes=interval_minutes,
            id="alert_job",
            replace_existing=True,
        )
        if not self.scheduler.running:
            self.scheduler.start()
        logger.info("Alert scheduler started (every %d minutes).", interval_minutes)

    def register_callback(self, callback):
        self._callback = callback

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Alert scheduler stopped.")

    def get_recent_alerts(self, n: int = 10) -> list:
        return self.alerts[-n:]


def send_alert(recommendation: dict, threshold: float = 70.0):
    score = recommendation.get("composite_score", 50.0)
    ticker = recommendation.get("ticker", "UNKNOWN")
    direction = recommendation.get("recommendation", "HOLD")

    if score > threshold or score < (100 - threshold):
        message = (
            f"[{datetime.now(timezone.utc).isoformat()}] "
            f"ALERT | {ticker} | score={score:.1f} | {direction}"
        )
        logger.info(message)
        return message
    return None
