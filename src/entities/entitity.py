import re
from abc import ABC, abstractmethod
import json

class Entity(ABC):
    def _extract(self, text: str, pattern: str, group: int = 1) -> str:
        match = re.search(pattern, text)
        return match.group(group).strip() if match else None    
    
    def _to_dict(self) -> dict:
        return self.__dict__
    
    def to_json(self) -> str:
        return json.dumps(
            self,
            indent=4,
            default=lambda obj: obj._to_dict(),
            ensure_ascii=False
        )
    
    @staticmethod
    def _to_float(s) -> float:
        if s is None:
            return 0.0
        # Remove separador de milhar (ponto) e converte vírgula decimal para ponto
        return float(s.replace(".", "").replace(",", "."))