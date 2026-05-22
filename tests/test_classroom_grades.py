import csv
from pathlib import Path

import pytest

from edu_page_automat.classroom_grades import convert_classroom_grades_csv


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read CSV rows from a generated EduPage grade file."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_convert_classroom_grades_filters_topic_and_preserves_empty_points(tmp_path: Path) -> None:
    """Google Classroom rows become EduPage grade rows for the requested topic only."""
    input_csv = tmp_path / "classroom.csv"
    output_csv = tmp_path / "edupage.csv"
    input_csv.write_text(
        "\n".join(
            [
                '"Student","Email","Task","Topic","Max points","Points earned"',
                '"Michael Vysloužil","","Build an RPG Creature Search App Project","JavaScript – Certifications","100","100"',
                '"Stela Bilová","","Build an RPG Creature Search App Project","JavaScript – Certifications","100",""',
                '"Hovorková Julie","","Build a Cash Register Project","JavaScript – Certifications","100","100"',
                '"Michael Vysloužil","","Survey Form","HTML a CSS - Certifications","100","100"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    row_count = convert_classroom_grades_csv(
        input_csv,
        output_csv,
        topics=["JavaScript – Certifications"],
    )

    assert row_count == 3
    assert read_rows(output_csv) == [
        {
            "jmeno": "Michael",
            "prijmeni": "Vysloužil",
            "jmeno_ulohy": "Build an RPG Creature Search App Project",
            "pocet_bodu": "100",
        },
        {
            "jmeno": "Stela",
            "prijmeni": "Bilová",
            "jmeno_ulohy": "Build an RPG Creature Search App Project",
            "pocet_bodu": "",
        },
        {
            "jmeno": "Hovorková",
            "prijmeni": "Julie",
            "jmeno_ulohy": "Build a Cash Register Project",
            "pocet_bodu": "100",
        },
    ]


def test_convert_classroom_grades_filters_tasks(tmp_path: Path) -> None:
    """Task filters narrow conversion within a Classroom export."""
    input_csv = tmp_path / "classroom.csv"
    output_csv = tmp_path / "edupage.csv"
    input_csv.write_text(
        "\n".join(
            [
                "Student,Task,Topic,Points earned",
                "Ada Lovelace,Keep,Topic,42",
                "Ada Lovelace,Skip,Topic,10",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    row_count = convert_classroom_grades_csv(input_csv, output_csv, tasks=["Keep"])

    assert row_count == 1
    assert read_rows(output_csv)[0]["jmeno_ulohy"] == "Keep"


def test_convert_classroom_grades_rejects_non_integer_points(tmp_path: Path) -> None:
    """Generated files stay compatible with the fill-grades parser."""
    input_csv = tmp_path / "classroom.csv"
    output_csv = tmp_path / "edupage.csv"
    input_csv.write_text(
        "\n".join(
            [
                "Student,Task,Topic,Points earned",
                "Ada Lovelace,Task,Topic,42.5",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Row 2: points must be a whole number or empty"):
        convert_classroom_grades_csv(input_csv, output_csv)
