import csv
from pathlib import Path
from typing import Iterable, List, Sequence


def read_csv(path: Path) -> List[dict]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_header(path: Path) -> List[str]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle))


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fieldnames),
            extrasaction="ignore",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)
