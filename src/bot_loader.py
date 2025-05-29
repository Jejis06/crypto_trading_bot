import logging
from typing import List
from simple_bot import SimpleBot
from bot_definitions import get_available_bots

logger = logging.getLogger(__name__)

class BotLoader:
    def __init__(self, client):
        """Initialize the bot loader."""
        self.client = client

    def load_bots(self) -> List[SimpleBot]:
        """Load all bot configurations and create bot instances."""
        try:
            # Get bots from Python definitions
            bots = get_available_bots(self.client)
            logger.info(f"Loaded {len(bots)} trading bots")
            return bots

        except Exception as e:
            logger.error(f"Failed to load bot configurations: {str(e)}")
            return [] 