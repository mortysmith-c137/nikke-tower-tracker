from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

MOLDS_PER_OPENING = 50
BONUS_FLOOR_INTERVAL = 5
FLOORS_PER_OPEN_DAY = 3
DAYS_PER_WEEK = 7


class Weekday(IntEnum):
    MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)


DAY_LABELS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
TOWER_SCHEDULE: dict[Weekday, frozenset[str]] = {
    Weekday.MONDAY: frozenset({"Tetra"}),
    Weekday.TUESDAY: frozenset({"Elysion"}),
    Weekday.WEDNESDAY: frozenset({"Missilis", "Pilgrim"}),
    Weekday.THURSDAY: frozenset({"Tetra"}),
    Weekday.FRIDAY: frozenset({"Elysion"}),
    Weekday.SATURDAY: frozenset({"Missilis"}),
    Weekday.SUNDAY: frozenset({"Elysion", "Missilis", "Tetra", "Pilgrim"}),
}


@dataclass(frozen=True, slots=True)
class TowerInput:
    tower_name: str
    last_reached_floor: int
    current_molds: int
    requested_openings: int

    @property
    def target_molds(self) -> int:
        if self.requested_openings == 0:
            return self.current_molds
        completed_band = (max(self.current_molds, 1) - 1) // MOLDS_PER_OPENING
        return (completed_band + self.requested_openings) * MOLDS_PER_OPENING


@dataclass(frozen=True, slots=True)
class FloorReward:
    floor: int
    gained_molds: int
    total_molds: int


@dataclass(frozen=True, slots=True)
class TowerCalculation:
    request: TowerInput
    end_floor: int | None
    final_molds: int
    elapsed_days: int
    rewards: tuple[FloorReward, ...]

    @property
    def climbed_floors(self) -> int:
        return len(self.rewards)

    @property
    def gained_molds(self) -> int:
        return self.final_molds - self.request.current_molds


def calculate_tower(request: TowerInput, start_day: Weekday) -> TowerCalculation:
    molds, floor, rewards = request.current_molds, request.last_reached_floor + 1, []
    while molds < request.target_molds:
        reward = 5 if floor % BONUS_FLOOR_INTERVAL == 0 else 1
        molds += reward
        rewards.append(FloorReward(floor, reward, molds))
        floor += 1

    remaining, day, elapsed_days = len(rewards), start_day, 0
    while remaining:
        if request.tower_name in TOWER_SCHEDULE[day]:
            remaining -= min(FLOORS_PER_OPEN_DAY, remaining)
        elapsed_days += 1
        day = Weekday((day + 1) % DAYS_PER_WEEK)

    return TowerCalculation(
        request=request,
        end_floor=rewards[-1].floor if rewards else request.last_reached_floor,
        final_molds=molds,
        elapsed_days=elapsed_days,
        rewards=tuple(rewards),
    )
