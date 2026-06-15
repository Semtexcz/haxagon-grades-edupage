import csv
from pathlib import Path

import pytest

from edu_page_automat.grade_diff import GradeDiffSummary, write_grade_diff_csv


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read generated grade diff CSV rows."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_write_grade_diff_outputs_only_changed_non_empty_truth_rows(tmp_path: Path) -> None:
    """The diff file contains only rows that `fill-grades` should save."""
    current_csv = tmp_path / "current.csv"
    truth_csv = tmp_path / "truth.csv"
    output_csv = tmp_path / "diff.csv"
    current_csv.write_text(
        "\n".join(
            [
                "first_name,last_name,task_name,points",
                "Ada,Lovelace,Task A,m",
                "Ada,Lovelace,Task B,100",
                "Ada,Lovelace,Task C,100",
                "Grace,Hopper,Task A,100",
                "Extra,Student,Task A,100",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    truth_csv.write_text(
        "\n".join(
            [
                "jmeno,prijmeni,jmeno_ulohy,pocet_bodu",
                "Ada,Lovelace,Task A,100",
                "Ada,Lovelace,Task B,100",
                "Ada,Lovelace,Task C,",
                "Missing,Student,Task A,100",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = write_grade_diff_csv(current_csv, truth_csv, output_csv)

    assert summary == GradeDiffSummary(
        written_rows=1,
        equal_rows=1,
        skipped_empty_target_rows=1,
        kept_better_current_rows=0,
        missing_current_rows=1,
        extra_current_rows=2,
    )
    assert read_rows(output_csv) == [
        {
            "jmeno": "Ada",
            "prijmeni": "Lovelace",
            "jmeno_ulohy": "Task A",
            "pocet_bodu": "100",
        }
    ]


def test_write_grade_diff_accepts_m_as_target_value(tmp_path: Path) -> None:
    """The EduPage absence marker can be written when it is the source-of-truth value."""
    current_csv = tmp_path / "current.csv"
    truth_csv = tmp_path / "truth.csv"
    output_csv = tmp_path / "diff.csv"
    current_csv.write_text("first_name,last_name,task_name,points\nAda,Lovelace,Task,100\n", encoding="utf-8")
    truth_csv.write_text("jmeno,prijmeni,jmeno_ulohy,pocet_bodu\nAda,Lovelace,Task,m\n", encoding="utf-8")

    summary = write_grade_diff_csv(current_csv, truth_csv, output_csv)

    assert summary.written_rows == 1
    assert summary.kept_better_current_rows == 0
    assert read_rows(output_csv)[0]["pocet_bodu"] == "m"


def test_write_grade_diff_accepts_exported_points_with_max_suffix(tmp_path: Path) -> None:
    """Existing EduPage exports with visible max-points suffixes remain diffable."""
    current_csv = tmp_path / "current.csv"
    truth_csv = tmp_path / "truth.csv"
    output_csv = tmp_path / "diff.csv"
    current_csv.write_text("first_name,last_name,task_name,points\nAda,Lovelace,Task,m · 20\n", encoding="utf-8")
    truth_csv.write_text("jmeno,prijmeni,jmeno_ulohy,pocet_bodu\nAda,Lovelace,Task,100\n", encoding="utf-8")

    summary = write_grade_diff_csv(current_csv, truth_csv, output_csv)

    assert summary.written_rows == 1
    assert summary.kept_better_current_rows == 0
    assert read_rows(output_csv)[0]["pocet_bodu"] == "100"


def test_write_grade_diff_keeps_better_current_grade_and_writes_report(tmp_path: Path) -> None:
    """A better current EduPage grade can be preserved with a report row."""
    current_csv = tmp_path / "current.csv"
    truth_csv = tmp_path / "truth.csv"
    output_csv = tmp_path / "diff.csv"
    report_csv = tmp_path / "diff-kept-current.csv"
    current_csv.write_text(
        "\n".join(
            [
                "first_name,last_name,task_name,points",
                "Ada,Lovelace,Task A,100",
                "Ada,Lovelace,Task B,m",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    truth_csv.write_text(
        "\n".join(
            [
                "jmeno,prijmeni,jmeno_ulohy,pocet_bodu",
                "Ada,Lovelace,Task A,90",
                "Ada,Lovelace,Task B,50",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = write_grade_diff_csv(
        current_csv,
        truth_csv,
        output_csv,
        keep_better_current=True,
        kept_current_report_csv=report_csv,
    )

    assert summary == GradeDiffSummary(
        written_rows=1,
        equal_rows=0,
        skipped_empty_target_rows=0,
        kept_better_current_rows=1,
        missing_current_rows=0,
        extra_current_rows=0,
    )
    assert read_rows(output_csv) == [
        {
            "jmeno": "Ada",
            "prijmeni": "Lovelace",
            "jmeno_ulohy": "Task B",
            "pocet_bodu": "50",
        }
    ]
    assert read_rows(report_csv) == [
        {
            "jmeno": "Ada",
            "prijmeni": "Lovelace",
            "jmeno_ulohy": "Task A",
            "soucasny_pocet_bodu": "100",
            "pozadovany_pocet_bodu": "90",
        }
    ]


def test_write_grade_diff_treats_m_as_zero_when_keeping_better_current(tmp_path: Path) -> None:
    """The absence marker compares as zero when preserving better current grades."""
    current_csv = tmp_path / "current.csv"
    truth_csv = tmp_path / "truth.csv"
    output_csv = tmp_path / "diff.csv"
    current_csv.write_text("first_name,last_name,task_name,points\nAda,Lovelace,Task,m\n", encoding="utf-8")
    truth_csv.write_text("jmeno,prijmeni,jmeno_ulohy,pocet_bodu\nAda,Lovelace,Task,1\n", encoding="utf-8")

    summary = write_grade_diff_csv(current_csv, truth_csv, output_csv, keep_better_current=True)

    assert summary.written_rows == 1
    assert summary.kept_better_current_rows == 0
    assert read_rows(output_csv)[0]["pocet_bodu"] == "1"


def test_write_grade_diff_accepts_raw_classroom_truth_csv(tmp_path: Path) -> None:
    """Raw Google Classroom exports can be used directly as source-of-truth CSVs."""
    current_csv = tmp_path / "current.csv"
    truth_csv = tmp_path / "classroom.csv"
    output_csv = tmp_path / "diff.csv"
    current_csv.write_text(
        "\n".join(
            [
                "first_name,last_name,task_name,points",
                "Ada,Lovelace,Submitted Task,m",
                "Grace,Hopper,Missing Task,100",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    truth_csv.write_text(
        "\n".join(
            [
                "Student,Email,Task,Topic,Max points,Points earned",
                'Ada Lovelace,,Submitted Task,Topic,100,100',
                'Grace Hopper,,Missing Task,Topic,100,',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = write_grade_diff_csv(current_csv, truth_csv, output_csv)

    assert summary.written_rows == 2
    assert summary.kept_better_current_rows == 0
    assert read_rows(output_csv) == [
        {
            "jmeno": "Ada",
            "prijmeni": "Lovelace",
            "jmeno_ulohy": "Submitted Task",
            "pocet_bodu": "100",
        },
        {
            "jmeno": "Grace",
            "prijmeni": "Hopper",
            "jmeno_ulohy": "Missing Task",
            "pocet_bodu": "m",
        },
    ]


def test_write_grade_diff_rejects_duplicate_keys(tmp_path: Path) -> None:
    """Ambiguous student-task rows fail before a diff file is trusted."""
    current_csv = tmp_path / "current.csv"
    truth_csv = tmp_path / "truth.csv"
    output_csv = tmp_path / "diff.csv"
    current_csv.write_text(
        "\n".join(
            [
                "first_name,last_name,task_name,points",
                "Ada,Lovelace,Task,100",
                "Ada,Lovelace,Task,m",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    truth_csv.write_text("jmeno,prijmeni,jmeno_ulohy,pocet_bodu\nAda,Lovelace,Task,100\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate grade"):
        write_grade_diff_csv(current_csv, truth_csv, output_csv)
