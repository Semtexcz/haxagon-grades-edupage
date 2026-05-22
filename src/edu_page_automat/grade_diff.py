"""Create fillable grade CSV diffs between EduPage export and source-of-truth CSV files."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, TextIO

EDUPAGE_DIFF_HEADERS = ["jmeno", "prijmeni", "jmeno_ulohy", "pocet_bodu"]
_CSV_SAMPLE_SIZE = 2048


@dataclass(frozen=True)
class GradeRow:
    """Normalized grade row keyed by student and task."""

    first_name: str
    last_name: str
    task_name: str
    points: str

    @property
    def key(self) -> tuple[str, str, str]:
        """Return the stable comparison key for one student-task grade."""
        return (self.first_name, self.last_name, self.task_name)

    def as_edupage_row(self) -> dict[str, str]:
        """Return the row in the CSV shape accepted by `fill-grades`."""
        return {
            "jmeno": self.first_name,
            "prijmeni": self.last_name,
            "jmeno_ulohy": self.task_name,
            "pocet_bodu": self.points,
        }


@dataclass(frozen=True)
class GradeDiffSummary:
    """Summary of a grade diff CSV generation run."""

    written_rows: int
    equal_rows: int
    skipped_empty_target_rows: int
    missing_current_rows: int
    extra_current_rows: int


def _normalize_header(header: str) -> str:
    """Normalize CSV headers for case-insensitive lookup."""
    return header.strip().casefold().replace(" ", "_").replace("-", "_")


def _find_header(fieldnames: Sequence[str], accepted_names: set[str], label: str) -> str:
    """Return the source header matching one of the accepted normalized names."""
    for fieldname in fieldnames:
        if _normalize_header(fieldname) in accepted_names:
            return fieldname
    raise ValueError(f"CSV header must contain a column for {label}")


def _has_header(fieldnames: Sequence[str], accepted_names: set[str]) -> bool:
    """Return whether fieldnames include one of the accepted normalized names."""
    return any(_normalize_header(fieldname) in accepted_names for fieldname in fieldnames)


def _split_student_name(student_name: str, row_index: int) -> tuple[str, str]:
    """Split a Google Classroom student display name into first and last name."""
    name_parts = student_name.split()
    if len(name_parts) < 2:
        raise ValueError(f"Row {row_index}: student name must contain first and last name")
    return name_parts[0], " ".join(name_parts[1:])


def _normalize_points(points: str, row_index: int, *, empty_value: str = "") -> str:
    """Normalize a grade value supported by `fill-grades`."""
    normalized_points = points.strip()
    if not normalized_points:
        return empty_value
    if normalized_points.casefold() == "m":
        return "m"
    if normalized_points.isdecimal():
        return normalized_points
    raise ValueError(f"Row {row_index}: points must be a whole number, m, or empty")


def _csv_reader(handle: TextIO) -> csv.DictReader:
    """Return a DictReader using the detected CSV dialect."""
    sample = handle.read(_CSV_SAMPLE_SIZE)
    handle.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except (csv.Error, TypeError):
        dialect = csv.excel
    return csv.DictReader(handle, dialect=dialect)


def _validate_unique_row(grade_row: GradeRow, row_index: int, seen_keys: set[tuple[str, str, str]]) -> None:
    """Validate a normalized grade row and update the duplicate guard."""
    if not grade_row.first_name:
        raise ValueError(f"Row {row_index}: missing first name")
    if not grade_row.last_name:
        raise ValueError(f"Row {row_index}: missing last name")
    if not grade_row.task_name:
        raise ValueError(f"Row {row_index}: missing task name")
    if grade_row.key in seen_keys:
        raise ValueError(
            f"Row {row_index}: duplicate grade for {grade_row.first_name} "
            f"{grade_row.last_name} in task {grade_row.task_name}"
        )
    seen_keys.add(grade_row.key)


def _load_classroom_grade_rows(reader: csv.DictReader) -> list[GradeRow]:
    """Load normalized grade rows from a raw Google Classroom export."""
    if not reader.fieldnames:
        raise ValueError("CSV must include a header")

    student_header = _find_header(reader.fieldnames, {"student"}, "student name")
    task_name_header = _find_header(reader.fieldnames, {"task"}, "task name")
    points_header = _find_header(reader.fieldnames, {"points_earned", "points"}, "points earned")

    rows: list[GradeRow] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for row_index, row in enumerate(reader, start=2):
        first_name, last_name = _split_student_name((row.get(student_header) or "").strip(), row_index)
        grade_row = GradeRow(
            first_name=first_name,
            last_name=last_name,
            task_name=(row.get(task_name_header) or "").strip(),
            points=_normalize_points(row.get(points_header) or "", row_index, empty_value="m"),
        )
        _validate_unique_row(grade_row, row_index, seen_keys)
        rows.append(grade_row)

    return rows


def _load_edupage_grade_rows(reader: csv.DictReader) -> list[GradeRow]:
    """Load normalized grade rows from a Czech or English EduPage-style CSV."""
    if not reader.fieldnames:
        raise ValueError("CSV must include a header")

    first_name_header = _find_header(reader.fieldnames, {"first_name", "jmeno", "name"}, "first name")
    last_name_header = _find_header(reader.fieldnames, {"last_name", "prijmeni", "surname"}, "last name")
    task_name_header = _find_header(
        reader.fieldnames,
        {"task_name", "task", "uloha", "jmeno_ulohy", "nazev_ulohy"},
        "task name",
    )
    points_header = _find_header(reader.fieldnames, {"points", "point", "score", "body", "pocet_bodu"}, "points")

    rows: list[GradeRow] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for row_index, row in enumerate(reader, start=2):
        grade_row = GradeRow(
            first_name=(row.get(first_name_header) or "").strip(),
            last_name=(row.get(last_name_header) or "").strip(),
            task_name=(row.get(task_name_header) or "").strip(),
            points=_normalize_points(row.get(points_header) or "", row_index),
        )
        _validate_unique_row(grade_row, row_index, seen_keys)
        rows.append(grade_row)

    return rows


def _load_grade_rows(csv_path: Path) -> list[GradeRow]:
    """Load normalized grade rows from an EduPage-style or Google Classroom CSV."""
    if not csv_path.exists():
        raise ValueError(f"CSV file {csv_path} does not exist")

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = _csv_reader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV must include a header")

        if _has_header(reader.fieldnames, {"student"}):
            rows = _load_classroom_grade_rows(reader)
        else:
            rows = _load_edupage_grade_rows(reader)

    if not rows:
        raise ValueError("CSV file did not contain any grade rows")

    return rows


def write_grade_diff_csv(current_csv: Path, truth_csv: Path, output_csv: Path) -> GradeDiffSummary:
    """Write rows whose truth grade should be saved to EduPage.

    The generated CSV contains only rows present in both files where the source
    value is non-empty and differs from the current EduPage value. Source files
    may use EduPage-style grade headers or raw Google Classroom export headers.
    """
    current_rows = _load_grade_rows(current_csv)
    truth_rows = _load_grade_rows(truth_csv)
    current_by_key = {row.key: row for row in current_rows}
    truth_keys = {row.key for row in truth_rows}

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    written_rows = 0
    equal_rows = 0
    skipped_empty_target_rows = 0
    missing_current_rows = 0

    with output_csv.open("w", encoding="utf-8", newline="") as output_handle:
        writer = csv.DictWriter(output_handle, fieldnames=EDUPAGE_DIFF_HEADERS, lineterminator="\n")
        writer.writeheader()

        for truth_row in truth_rows:
            current_row = current_by_key.get(truth_row.key)
            if current_row is None:
                missing_current_rows += 1
                continue
            if not truth_row.points:
                skipped_empty_target_rows += 1
                continue
            if current_row.points == truth_row.points:
                equal_rows += 1
                continue

            writer.writerow(truth_row.as_edupage_row())
            written_rows += 1

    return GradeDiffSummary(
        written_rows=written_rows,
        equal_rows=equal_rows,
        skipped_empty_target_rows=skipped_empty_target_rows,
        missing_current_rows=missing_current_rows,
        extra_current_rows=len({row.key for row in current_rows} - truth_keys),
    )
