from helloagents.types import FavorabilityLevel


class FavorabilitySystem:
    FLOOR = -100
    CEILING = 100
    DELTA_FLOOR = -10
    DELTA_CEILING = 10

    def __init__(self, initial: int = 0):
        self._score = max(self.FLOOR, min(self.CEILING, initial))

    @property
    def score(self) -> int:
        return self._score

    @property
    def level(self) -> FavorabilityLevel:
        return self.score_to_level(self._score)

    def apply_delta(self, delta: int) -> int:
        delta = max(self.DELTA_FLOOR, min(self.DELTA_CEILING, delta))
        self._score = max(self.FLOOR, min(self.CEILING, self._score + delta))
        return self._score

    def level_name(self) -> str:
        return self.level.name

    @staticmethod
    def score_to_level(score: int) -> FavorabilityLevel:
        if score <= -61:
            return FavorabilityLevel.HATED
        elif score <= -21:
            return FavorabilityLevel.DISLIKED
        elif score <= 20:
            return FavorabilityLevel.NEUTRAL
        elif score <= 60:
            return FavorabilityLevel.FRIENDLY
        else:
            return FavorabilityLevel.TRUSTED
