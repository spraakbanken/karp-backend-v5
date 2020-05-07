import json
from pathlib import Path
from typing import Dict, List, Optional

from karp5.domain.model.mode import Mode, ModeRepository


class JsonFileModeRepository(ModeRepository):
    def __init__(self, config_dir: Path, filename: Optional[str] = None):
        self.config_dir = Path(config_dir)
        self.filename = "modes.json" if not filename else filename
        self.modes: Dict[str, Mode] = {}
        with open(self.config_dir / self.filename) as fp:
            modes_config = json.load(fp)

        self.defaults = modes_config.pop("default", None)
        for mode_id, mode_config in modes_config.items():
            self.modes[mode_id] = Mode.from_mapping(
                id=mode_id, mapping=mode_config, defaults=self.defaults
            )

    def mode_by_id(self, mode_id: str) -> Mode:
        return self.modes[mode_id]

    def mode_ids(self) -> List[str]:
        return list(self.modes.keys())
