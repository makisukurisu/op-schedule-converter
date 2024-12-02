from collections import defaultdict
import logging
from typing import Literal
import pydantic
import datetime

START_WEEK_NUMBER = datetime.date(2024, 9, 2).isocalendar().week

day_translations = {
    "monday": "понеділок",
    "tuesday": "вівторок",
    "wednesday": "середа",
    "thursday": "четвер",
    "friday": "п'ятниця",
    "saturday": "субота",
}
pair_type_translations = {
    "lecture": "лекція",
    "practice": "практика",
    "lab": "лабораторна",
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
    pair_type: str

    @pydantic.field_validator("pair_type", mode="after")
    @classmethod
    def translate_pair_type(cls: "type[PairRepresentation]", value: str) -> str:
        return pair_type_translations[value]

    @pydantic.field_validator("day", mode="after")
    @classmethod
    def translate_day(cls: "type[PairRepresentation]", value: str) -> str:
        return day_translations[value]


class Schedule(pydantic.BaseModel):
    pairs: list[Pair]

    pair_info: list[PairInfo]

    @staticmethod
    def localized_week_number(day_of_the_week: datetime.date) -> int:
        week_number = day_of_the_week.isocalendar().week
        localized_week_number = (week_number - START_WEEK_NUMBER) + 1

        if localized_week_number < 0:
            raise ValueError("Week number is less than 0")

        return localized_week_number

    @staticmethod
    def get_week_oddity(day_of_the_week: datetime.date) -> Literal["even", "odd"]:
        return (
            "odd"
            if Schedule.localized_week_number(day_of_the_week=day_of_the_week) % 2 == 1
            else "even"
        )

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

    def filter_pairs_by_week(self, day_of_the_week: datetime.date) -> list[Pair]:
        localized_week_number = Schedule.localized_week_number(day_of_the_week)
        week_oddity = self.get_week_oddity(day_of_the_week)

        return list(
            filter(
                lambda x: x.from_week <= localized_week_number <= x.to_week
                and (x.periodicity == "every" or x.periodicity == week_oddity),
                self.pairs,
            )
        )

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
        pairs = self.filter_pairs_by_week(day_of_the_week)

        for pair in pairs:
            _add_pair(pair)

        return week_pairs
