from dataclasses import dataclass
from typing import Optional

@dataclass
class PlayerData:
    name: str
    unique_id: str
    house_level: int
    home_location: str
    xml_content: str  # 存储完整的玩家XML内容
    is_host: bool = False

class SaveGameData:
    def __init__(self):
        self.host: Optional[PlayerData] = None
        self.farmhands: list[PlayerData] = []
        self.save_path: str = ""
        
    def add_player(self, player: PlayerData):
        if player.is_host:
            self.host = player
        else:
            self.farmhands.append(player) 