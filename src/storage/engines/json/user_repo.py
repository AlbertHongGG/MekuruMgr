import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import TypeAdapter

from src.domain.user_models import UserProfile, UserComicInteraction
from src.storage.core.user_interface import IUserStorage

logger = logging.getLogger(__name__)

class LocalUserStorage(IUserStorage):
    def __init__(self, db_path: str = "data/user_profile.json"):
        self.db_path = Path(db_path)
        self.data_dir = self.db_path.parent
        self._lock = threading.RLock()
        self._profile = UserProfile()
        self._load_db()

    def _load_db(self):
        with self._lock:
            if not self.db_path.exists():
                return
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.loads(f.read())
                self._profile = UserProfile.model_validate(data)
                logger.info(f"Loaded User Profile with {len(self._profile.interactions)} interactions")
            except Exception as e:
                logger.error(f"[red]Failed to load user profile DB: {e}[/]")
                self._profile = UserProfile()

    def _save_db(self):
        with self._lock:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            temp_path = self.db_path.with_suffix('.tmp')
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    data = self._profile.model_dump(mode='json')
                    json.dump(data, f, ensure_ascii=False, indent=2)
                temp_path.replace(self.db_path)
            except Exception as e:
                logger.error(f"[red]Failed to save user profile DB: {e}[/]")
                raise

    def get_interaction(self, provider_id: str, comic_id: str) -> Optional[UserComicInteraction]:
        key = f"{provider_id}::{comic_id}"
        with self._lock:
            return self._profile.interactions.get(key)

    def save_interaction(self, interaction: UserComicInteraction) -> None:
        key = f"{interaction.provider_id}::{interaction.comic_id}"
        with self._lock:
            self._profile.interactions[key] = interaction
            self._save_db()

    def get_all_interactions(self) -> List[UserComicInteraction]:
        with self._lock:
            return list(self._profile.interactions.values())
