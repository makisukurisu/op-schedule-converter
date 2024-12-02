import datetime
import json
import pathlib

import typer

try:
    from schedule import classes
except ImportError:
    import sys

    sys.path.append(str(pathlib.Path(__file__).parent.parent))
    from schedule import classes


def main(
    top_directory: pathlib.Path | None = None,
    date_str: str | None = None,
) -> None:
    top_directory = top_directory or pathlib.Path(__file__).parent.parent.parent

    schedule = classes.Schedule(
        pairs=[
            classes.Pair.model_validate(obj)
            for obj in json.load(
                open(
                    top_directory / "source" / "pairs.json",
                    "r",
                    encoding="utf-8",
                )
            )
        ],
        pair_info=[
            classes.PairInfo.model_validate(obj)
            for obj in json.load(
                open(
                    top_directory / "source" / "pair_info.json",
                    "r",
                    encoding="utf-8",
                )
            )
        ],
    )

    if date_str is None:
        date_str = input("Enter the date for schedule generation (YYYY-MM-DD): ")

    date = datetime.date.fromisoformat(date_str)

    result = schedule.get_schedule_for_week(date)

    message = f"Розклад на тиждень з {date} року:\n\n"
    for day, pairs in result.items():
        message += f"# {classes.day_translations[day].capitalize()}:\n\n"
        for pair in sorted(pairs, key=lambda x: x.pair_number):
            message += f"## #{pair.pair_number}\nНазва пари: {pair.pair_name}\n\nВикладач: {pair.teacher} ({pair.pair_type})\n\nДодаткова інформація:\n{pair.additional}\n\n"
        message += "\n---\n"

    print(
        message,
        file=open(
            top_directory / "schedule-results" / f"schedule-{date.isoformat()}.md",
            "w",
            encoding="utf-8",
        ),
    )


if __name__ == "__main__":
    typer.run(main)
