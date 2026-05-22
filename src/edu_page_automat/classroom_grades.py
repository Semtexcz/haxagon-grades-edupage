"""Convert Google Classroom grade exports into EduPage grade CSV input."""

import csv
from pathlib import Path
from typing import Iterable, Sequence

EDUPAGE_GRADE_HEADERS = ["jmeno", "prijmeni", "jmeno_ulohy", "pocet_bodu"]
_CSV_SAMPLE_SIZE = 2048


def _normalize_header(header: str) -> str:
    """Normalize CSV headers for case-insensitive lookup."""
    return header.strip().casefold().replace(" ", "_").replace("-", "_")


def _find_header(fieldnames: Sequence[str], accepted_names: set[str], label: str) -> str:
    """Return the source header matching one of the accepted normalized names."""
    for fieldname in fieldnames:
        if _normalize_header(fieldname) in accepted_names:
            return fieldname
    raise ValueError(f"CSV header must contain a column for {label}")


def _split_student_name(student_name: str, row_index: int) -> tuple[str, str]:
    """Split a Google Classroom student display name into first and last name."""
    name_parts = student_name.split()
    if len(name_parts) < 2:
        raise ValueError(f"Row {row_index}: student name must contain first and last name")
    return name_parts[0], " ".join(name_parts[1:])


def _normalize_points(points: str, row_index: int) -> str:
    """Return an EduPage-compatible point value, using `m` for empty values."""
    normalized_points = points.strip()
    if not normalized_points:
        return "m"
    if not normalized_points.isdecimal():
        raise ValueError(f"Row {row_index}: points must be a whole number or empty")
    return normalized_points


def convert_classroom_grades_csv(
    input_csv: Path,
    output_csv: Path,
    *,
    topics: Iterable[str] = (),
    tasks: Iterable[str] = (),
) -> int:
    """Convert a Google Classroom grade export into a CSV accepted by `fill-grades`.

    Optional topic and task filters keep the conversion focused on the EduPage
    tasks the teacher wants to import. Rows with empty points are converted to
    the EduPage `m` marker so they remain explicit fillable grade entries.
    """
    if not input_csv.exists():
        raise ValueError(f"CSV file {input_csv} does not exist")

    topic_filter = {topic.strip() for topic in topics if topic.strip()}
    task_filter = {task.strip() for task in tasks if task.strip()}

    with input_csv.open("r", encoding="utf-8", newline="") as input_handle:
        sample = input_handle.read(_CSV_SAMPLE_SIZE)
        input_handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except (csv.Error, TypeError):
            dialect = csv.excel

        reader = csv.DictReader(input_handle, dialect=dialect)
        if not reader.fieldnames:
            raise ValueError("CSV must include a header")

        student_header = _find_header(reader.fieldnames, {"student"}, "student name")
        task_header = _find_header(reader.fieldnames, {"task"}, "task name")
        topic_header = _find_header(reader.fieldnames, {"topic"}, "topic")
        points_header = _find_header(reader.fieldnames, {"points_earned", "points"}, "points earned")

        output_csv.parent.mkdir(parents=True, exist_ok=True)
        with output_csv.open("w", encoding="utf-8", newline="") as output_handle:
            writer = csv.DictWriter(output_handle, fieldnames=EDUPAGE_GRADE_HEADERS, lineterminator="\n")
            writer.writeheader()

            written_rows = 0
            for row_index, row in enumerate(reader, start=2):
                task_name = (row.get(task_header) or "").strip()
                topic_name = (row.get(topic_header) or "").strip()
                if task_filter and task_name not in task_filter:
                    continue
                if topic_filter and topic_name not in topic_filter:
                    continue

                first_name, last_name = _split_student_name((row.get(student_header) or "").strip(), row_index)
                writer.writerow(
                    {
                        "jmeno": first_name,
                        "prijmeni": last_name,
                        "jmeno_ulohy": task_name,
                        "pocet_bodu": _normalize_points(row.get(points_header) or "", row_index),
                    }
                )
                written_rows += 1

    return written_rows
