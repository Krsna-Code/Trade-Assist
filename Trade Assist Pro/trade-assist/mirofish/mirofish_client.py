import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

import logging
import requests
from config import MIROFISH_URL, MIROFISH_AGENTS, MIROFISH_ROUNDS

logger = logging.getLogger(__name__)


def run_simulation(
    seed: str,
    num_agents: int = MIROFISH_AGENTS,
    num_rounds: int = MIROFISH_ROUNDS,
) -> dict:
    try:
        response = requests.post(
            f"{MIROFISH_URL}/api/simulate",
            json={"seed": seed, "num_agents": num_agents, "num_rounds": num_rounds},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.error("MiroFish simulation failed: %s", exc)
        return {
            "status": "fallback",
            "dominant_behavior": "NEUTRAL",
            "confidence": 0.5,
            "bullish_agents": num_agents // 2,
            "bearish_agents": num_agents // 2,
            "neutral_agents": 0,
            "summary": "MiroFish unavailable — falling back to sentiment-only signal",
            "rounds": [],
        }


def is_available() -> bool:
    try:
        response = requests.get(f"{MIROFISH_URL}/health", timeout=3)
        return response.status_code == 200
    except Exception:
        return False
