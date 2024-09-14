from collections import defaultdict
import logging
from typing import Literal
import pydantic
import datetime

START_WEEK_NUMBER = datetime.date(2024, 9, 16).isocalendar().week

day_translations = {
    "monday": "понеділок",
    "tuesday": "вівторок",
    "wednesday": "середа",
    "thursday": "четвер",
    "friday": "п'ятниця",
    "saturday": "субота",
}


class PairInfo(pydantic.BaseModel):
    pair_name: str
    teacher: str

    additional: str


class Pair(pydantic.BaseModel):
    pair_name: str
    teacher: str

    day: Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    pair_number: int
    periodicity: Literal["every", "odd", "even"]

    from_week: int
    to_week: int

    pair_type: Literal["lecture", "practice", "lab"] = "lecture"


class PairRepresentation(pydantic.BaseModel):
    pair_name: str
    teacher: str

    day: str
    pair_number: int
    periodicity: str
    additional: str


class Schedule(pydantic.BaseModel):
    pairs: list[Pair]

    pair_info: list[PairInfo]

    @staticmethod
    def get_week_oddity(day_of_the_week: datetime.date) -> Literal["even", "odd"]:
        week_number = day_of_the_week.isocalendar().week
        localized_week_number = (week_number - START_WEEK_NUMBER) + 1

        if localized_week_number < 0:
            raise ValueError("Week number is less than 0")

        return "odd" if localized_week_number % 2 == 1 else "even"

    def get_pair_info(self, pair: Pair) -> PairInfo:
        filtered_info = filter(
            lambda x: x.pair_name == pair.pair_name and x.teacher == pair.teacher,
            self.pair_info,
        )
        result = next(filtered_info, None)

        if result is None:
            logging.warning({"msg": "Pair info not found", "pair": pair})
            return PairInfo(
                pair_name=pair.pair_name, teacher=pair.teacher, additional=""
            )

        return result

    def get_schedule_for_week(
        self, day_of_the_week: datetime.date
    ) -> dict[str, list[PairRepresentation]]:
        def _add_pair(pair: Pair) -> None:
            week_pairs[pair.day].append(
                PairRepresentation(
                    **pair.model_dump(), additional=self.get_pair_info(pair).additional
                )
            )

        week_pairs = defaultdict(list)
        week_oddity = self.get_week_oddity(day_of_the_week)

        for pair in self.pairs:
            match (pair.periodicity, week_oddity):
                case "every", _:
                    _add_pair(pair)
                case "even", "even":
                    _add_pair(pair)
                case "odd", "odd":
                    _add_pair(pair)

        return week_pairs
