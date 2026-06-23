#!/usr/bin/env python3
"""Generate a reproducible demo oil-well CSV and point shapefile for Iraq."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import random
import struct
from pathlib import Path


BBOX = {
    "west": 38.79,
    "east": 48.57,
    "south": 29.06,
    "north": 37.38,
}

DEFAULT_COUNT = 75
DEFAULT_SEED = 20260610
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DEFAULT_BASENAME = "OilWells"

CSV_FIELDS = [
    "well_id",
    "well_name",
    "field_name",
    "status",
    "oil_type",
    "depth_m",
    "discovery_year",
    "operator",
    "lon",
    "lat",
]

# DBF field names are limited to 10 bytes in shapefiles. The CSV keeps the
# requested full names; the shapefile uses this explicit, stable mapping.
DBF_FIELDS = [
    ("well_id", "C", 10, 0, "well_id"),
    ("well_name", "C", 28, 0, "well_name"),
    ("field_name", "C", 28, 0, "field_name"),
    ("status", "C", 10, 0, "status"),
    ("oil_type", "C", 14, 0, "oil_type"),
    ("depth_m", "N", 6, 0, "depth_m"),
    ("discov_yr", "N", 4, 0, "discovery_year"),
    ("operator", "C", 30, 0, "operator"),
    ("lon", "N", 13, 6, "lon"),
    ("lat", "N", 12, 6, "lat"),
]

WGS84_PRJ = (
    'GEOGCS["WGS 84",'
    'DATUM["WGS_1984",'
    'SPHEROID["WGS 84",6378137,298.257223563]],'
    'PRIMEM["Greenwich",0],'
    'UNIT["degree",0.0174532925199433],'
    'AUTHORITY["EPSG","4326"]]'
)


FIELDS = [
    "Rumaila",
    "West Qurna",
    "Kirkuk",
    "Majnoon",
    "Zubair",
    "Halfaya",
    "Bai Hassan",
    "East Baghdad",
    "Badra",
    "Gharraf",
    "Nassiriya",
    "Al-Ahdab",
    "Qayyarah",
    "Najmah",
    "Akkas",
    "Mansuriyah",
]

OPERATORS = [
    "Basra Oil Company",
    "North Oil Company",
    "Midland Oil Company",
    "Missan Oil Company",
    "Iraq Drilling Company",
    "Demo Petroleum Co",
]

OIL_TYPES = [
    "light crude",
    "medium crude",
    "heavy crude",
    "sour crude",
    "condensate",
]

STATUS_VALUES = ["active", "inactive", "planned"]


def _format_point(value: float) -> str:
    return f"{value:.6f}"


def generate_rows(count: int, seed: int) -> list[dict[str, str]]:
    rng = random.Random(seed)
    rows = []

    for index in range(1, count + 1):
        field_name = rng.choice(FIELDS)
        status = rng.choices(STATUS_VALUES, weights=[0.68, 0.17, 0.15], k=1)[0]
        lon = rng.uniform(BBOX["west"], BBOX["east"])
        lat = rng.uniform(BBOX["south"], BBOX["north"])
        well_code = f"IQ-OW-{index:03d}"
        field_code = "".join(part[0] for part in field_name.replace("-", " ").split())

        rows.append(
            {
                "well_id": well_code,
                "well_name": f"{field_code}-{index:03d}",
                "field_name": field_name,
                "status": status,
                "oil_type": rng.choice(OIL_TYPES),
                "depth_m": str(rng.randint(1200, 5200)),
                "discovery_year": str(rng.randint(1927, 2024)),
                "operator": rng.choice(OPERATORS),
                "lon": _format_point(lon),
                "lat": _format_point(lat),
            }
        )

    return rows


def write_csv(rows: list[dict[str, str]], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="ascii") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _write_main_header(fh, file_length_words: int, shape_type: int, bbox: tuple[float, float, float, float]) -> None:
    xmin, ymin, xmax, ymax = bbox
    fh.write(struct.pack(">i", 9994))
    fh.write(b"\x00" * 20)
    fh.write(struct.pack(">i", file_length_words))
    fh.write(struct.pack("<i", 1000))
    fh.write(struct.pack("<i", shape_type))
    fh.write(struct.pack("<4d", xmin, ymin, xmax, ymax))
    fh.write(struct.pack("<4d", 0.0, 0.0, 0.0, 0.0))


def write_shp_and_shx(rows: list[dict[str, str]], basename: Path) -> None:
    points = [(float(row["lon"]), float(row["lat"])) for row in rows]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    bbox = (min(xs), min(ys), max(xs), max(ys))

    shape_type = 1
    record_content_words = 10
    shp_record_bytes = 8 + (record_content_words * 2)
    shp_file_length_words = (100 + len(rows) * shp_record_bytes) // 2
    shx_file_length_words = (100 + len(rows) * 8) // 2

    with basename.with_suffix(".shp").open("wb") as shp:
        _write_main_header(shp, shp_file_length_words, shape_type, bbox)
        offset_words = 50
        for recno, (lon, lat) in enumerate(points, start=1):
            shp.write(struct.pack(">2i", recno, record_content_words))
            shp.write(struct.pack("<i2d", shape_type, lon, lat))
            offset_words += shp_record_bytes // 2

    with basename.with_suffix(".shx").open("wb") as shx:
        _write_main_header(shx, shx_file_length_words, shape_type, bbox)
        offset_words = 50
        for _ in points:
            shx.write(struct.pack(">2i", offset_words, record_content_words))
            offset_words += shp_record_bytes // 2


def _dbf_value(value: str, field_type: str, length: int, decimals: int) -> bytes:
    if field_type == "N":
        if decimals:
            text = f"{float(value):>{length}.{decimals}f}"
        else:
            text = f"{int(float(value)):>{length}d}"
    else:
        text = str(value)[:length].ljust(length)
    return text.encode("ascii")


def write_dbf(rows: list[dict[str, str]], dbf_path: Path) -> None:
    today = dt.date.today()
    header_length = 32 + (32 * len(DBF_FIELDS)) + 1
    record_length = 1 + sum(field[2] for field in DBF_FIELDS)

    with dbf_path.open("wb") as dbf:
        dbf.write(struct.pack("<BBBBLHH20x", 0x03, today.year - 1900, today.month, today.day, len(rows), header_length, record_length))

        for dbf_name, field_type, length, decimals, _ in DBF_FIELDS:
            name_bytes = dbf_name.encode("ascii")
            if len(name_bytes) > 10:
                raise ValueError(f"DBF field name is too long for shapefile: {dbf_name}")
            dbf.write(name_bytes.ljust(11, b"\x00"))
            dbf.write(field_type.encode("ascii"))
            dbf.write(b"\x00" * 4)
            dbf.write(struct.pack("BB", length, decimals))
            dbf.write(b"\x00" * 14)

        dbf.write(b"\x0D")

        for row in rows:
            dbf.write(b" ")
            for _, field_type, length, decimals, csv_name in DBF_FIELDS:
                dbf.write(_dbf_value(row[csv_name], field_type, length, decimals))

        dbf.write(b"\x1A")


def write_projection_files(basename: Path) -> None:
    basename.with_suffix(".prj").write_text(WGS84_PRJ + os.linesep, encoding="ascii")
    basename.with_suffix(".cpg").write_text("UTF-8" + os.linesep, encoding="ascii")


def write_shapefile(rows: list[dict[str, str]], shapefile_path: Path) -> None:
    shapefile_path.parent.mkdir(parents=True, exist_ok=True)
    basename = shapefile_path.with_suffix("")
    write_shp_and_shx(rows, basename)
    write_dbf(rows, basename.with_suffix(".dbf"))
    write_projection_files(basename)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--basename", default=DEFAULT_BASENAME)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = generate_rows(args.count, args.seed)
    csv_path = args.output_dir / f"{args.basename}.csv"
    shp_path = args.output_dir / f"{args.basename}.shp"

    write_csv(rows, csv_path)
    write_shapefile(rows, shp_path)

    print(f"Wrote CSV: {csv_path} ({len(rows)} rows)")
    print(f"Wrote shapefile: {shp_path}")
    print(f"Extent: west={BBOX['west']}, east={BBOX['east']}, south={BBOX['south']}, north={BBOX['north']}")


if __name__ == "__main__":
    main()
