#!/usr/bin/env python3
"""Generate a reproducible demo oil-well CSV and point shapefile for Iraq."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
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

# Lebanon's offshore exploration blocks sit west of the coastline (~lon 35.1-36.0),
# roughly between the Cyprus EEZ boundary and Lebanon's own maritime border.
# This bbox stays clear of land (max east 34.95) and within Lebanon's latitude
# span (Naqoura ~33.09N south, Aarida ~34.64N north).
LEBANON_BBOX = {
    "west": 32.90,
    "east": 34.95,
    "south": 33.05,
    "north": 34.65,
}

LEBANON_ID_PREFIX = "LB-OW-"
DEFAULT_LEBANON_COUNT = 12
DEFAULT_LEBANON_SEED = 20260711
# Combined water depth (~1000-2000m) + sub-seabed reservoir depth typical of
# East Mediterranean offshore prospects — deeper than Iraq's onshore wells.
LEBANON_DEPTH_RANGE = (3200, 6800)
# Lebanon's offshore licensing rounds began 2017/2018; exploration is ongoing.
LEBANON_DISCOVERY_RANGE = (2018, 2025)

LEBANON_FIELDS = [f"Block {i}" for i in range(1, 11)]

LEBANON_OPERATORS = [
    "TotalEnergies",
    "Eni",
    "QatarEnergy",
    "Lebanon Petroleum Administration",
    "Demo Petroleum Co",
]

DEFAULT_PRODUCTION_HOURS = 43830  # 5 years at hourly cadence (365.25 * 24 * 5)
DEFAULT_PRODUCTION_START = "2021-01-01T00:00:00"
DEFAULT_PRODUCTION_SEED = 20260812
DEFAULT_PRODUCTION_BASENAME = "OilWellProduction"

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

# Single-feature schema for the production shapefile: one point per well plus
# a pointer + summary stats for the hourly time series held in the companion
# CSV (see write_production_shapefile / README "Time-series format" section).
PROD_DBF_FIELDS = [
    ("well_id", "C", 10, 0, "well_id"),
    ("well_name", "C", 28, 0, "well_name"),
    ("field_name", "C", 28, 0, "field_name"),
    ("country", "C", 10, 0, "country"),
    ("status", "C", 10, 0, "status"),
    ("oil_type", "C", 14, 0, "oil_type"),
    ("depth_m", "N", 6, 0, "depth_m"),
    ("operator", "C", 30, 0, "operator"),
    ("lon", "N", 13, 6, "lon"),
    ("lat", "N", 12, 6, "lat"),
    ("prod_csv", "C", 40, 0, "prod_csv"),
    ("prod_strt", "C", 19, 0, "prod_strt"),
    ("prod_end", "C", 19, 0, "prod_end"),
    ("n_readng", "N", 6, 0, "n_readng"),
    ("avg_bpd", "N", 10, 2, "avg_bpd"),
    ("min_bpd", "N", 10, 2, "min_bpd"),
    ("max_bpd", "N", 10, 2, "max_bpd"),
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


def generate_lebanon_rows(count: int, seed: int) -> list[dict[str, str]]:
    """Same seeded/reproducible approach as generate_rows, offshore Lebanon variant."""
    rng = random.Random(seed)
    rows = []

    for index in range(1, count + 1):
        field_name = rng.choice(LEBANON_FIELDS)
        # Offshore blocks skew toward exploration/appraisal rather than active production.
        status = rng.choices(STATUS_VALUES, weights=[0.5, 0.2, 0.3], k=1)[0]
        lon = rng.uniform(LEBANON_BBOX["west"], LEBANON_BBOX["east"])
        lat = rng.uniform(LEBANON_BBOX["south"], LEBANON_BBOX["north"])
        well_code = f"{LEBANON_ID_PREFIX}{index:03d}"
        field_code = "".join(part[0] for part in field_name.replace("-", " ").split())

        rows.append(
            {
                "well_id": well_code,
                "well_name": f"{field_code}-{index:03d}",
                "field_name": field_name,
                "status": status,
                "oil_type": rng.choice(OIL_TYPES),
                "depth_m": str(rng.randint(*LEBANON_DEPTH_RANGE)),
                "discovery_year": str(rng.randint(*LEBANON_DISCOVERY_RANGE)),
                "operator": rng.choice(LEBANON_OPERATORS),
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


def write_dbf(rows: list[dict[str, str]], dbf_path: Path, fields=DBF_FIELDS) -> None:
    today = dt.date.today()
    header_length = 32 + (32 * len(fields)) + 1
    record_length = 1 + sum(field[2] for field in fields)

    with dbf_path.open("wb") as dbf:
        dbf.write(struct.pack("<BBBBLHH20x", 0x03, today.year - 1900, today.month, today.day, len(rows), header_length, record_length))

        for dbf_name, field_type, length, decimals, _ in fields:
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
            for _, field_type, length, decimals, csv_name in fields:
                dbf.write(_dbf_value(row[csv_name], field_type, length, decimals))

        dbf.write(b"\x1A")


def write_projection_files(basename: Path) -> None:
    basename.with_suffix(".prj").write_text(WGS84_PRJ + os.linesep, encoding="ascii")
    basename.with_suffix(".cpg").write_text("UTF-8" + os.linesep, encoding="ascii")


def write_shapefile(rows: list[dict[str, str]], shapefile_path: Path, dbf_fields=DBF_FIELDS) -> None:
    shapefile_path.parent.mkdir(parents=True, exist_ok=True)
    basename = shapefile_path.with_suffix("")
    write_shp_and_shx(rows, basename)
    write_dbf(rows, basename.with_suffix(".dbf"), fields=dbf_fields)
    write_projection_files(basename)


def generate_production_series(
    well: dict[str, str], hours: int, start: dt.datetime, seed: int
) -> list[tuple[str, dt.datetime, float]]:
    """Hourly barrels-per-day readings for one well: exponential decline curve
    with seasonal wobble, multiplicative noise, and occasional maintenance
    shutdowns (bpd=0) — all seeded for reproducibility."""
    rng = random.Random(seed)
    base_rate = rng.uniform(1800.0, 9000.0)
    decline_rate = rng.uniform(0.05, 0.20)
    seasonal_amp = rng.uniform(0.02, 0.08)
    noise_sd = rng.uniform(0.01, 0.04)
    downtime_prob = rng.uniform(0.001, 0.01)
    hours_per_year = 8766.0

    readings = []
    for h in range(hours):
        decline = math.exp(-decline_rate * (h / hours_per_year))
        seasonal = 1.0 + seasonal_amp * math.sin(2 * math.pi * h / hours_per_year)
        noise = 1.0 + rng.gauss(0.0, noise_sd)
        value = base_rate * decline * seasonal * noise
        if rng.random() < downtime_prob:
            value = 0.0
        value = max(0.0, value)
        readings.append((well["well_id"], start + dt.timedelta(hours=h), round(value, 2)))

    return readings


def write_production_csv(readings: list[tuple[str, dt.datetime, float]], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="ascii") as fh:
        writer = csv.writer(fh)
        writer.writerow(["well_id", "timestamp", "barrels_per_day"])
        for well_id, ts, bpd in readings:
            writer.writerow([well_id, ts.isoformat(), f"{bpd:.2f}"])


def write_production_shapefile(
    well: dict[str, str],
    readings: list[tuple[str, dt.datetime, float]],
    csv_filename: str,
    shapefile_path: Path,
) -> None:
    """One point feature for the well, carrying summary stats plus a pointer
    (prod_csv) to the companion CSV that holds the full hourly series."""
    values = [bpd for _, _, bpd in readings]
    start_ts = readings[0][1]
    end_ts = readings[-1][1]
    country = "Lebanon" if well["well_id"].startswith(LEBANON_ID_PREFIX) else "Iraq"

    production_row = {
        "well_id": well["well_id"],
        "well_name": well["well_name"],
        "field_name": well["field_name"],
        "country": country,
        "status": well["status"],
        "oil_type": well["oil_type"],
        "depth_m": well["depth_m"],
        "operator": well["operator"],
        "lon": well["lon"],
        "lat": well["lat"],
        "prod_csv": csv_filename,
        "prod_strt": start_ts.isoformat(),
        "prod_end": end_ts.isoformat(),
        "n_readng": str(len(readings)),
        "avg_bpd": f"{sum(values) / len(values):.2f}",
        "min_bpd": f"{min(values):.2f}",
        "max_bpd": f"{max(values):.2f}",
    }

    write_shapefile([production_row], shapefile_path, dbf_fields=PROD_DBF_FIELDS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help="Iraq well count")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Iraq generator seed")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--basename", default=DEFAULT_BASENAME)
    parser.add_argument(
        "--regions",
        default="iraq",
        help="Comma-separated regions to include: iraq, lebanon (default: iraq)",
    )
    parser.add_argument("--lebanon-count", type=int, default=DEFAULT_LEBANON_COUNT)
    parser.add_argument("--lebanon-seed", type=int, default=DEFAULT_LEBANON_SEED)
    parser.add_argument(
        "--with-production",
        action="store_true",
        help="Also generate an hourly production time series (CSV + single-point shapefile) for one well",
    )
    parser.add_argument(
        "--production-well",
        default=None,
        help="well_id to generate production data for (default: first generated well)",
    )
    parser.add_argument("--production-hours", type=int, default=DEFAULT_PRODUCTION_HOURS)
    parser.add_argument("--production-start", default=DEFAULT_PRODUCTION_START)
    parser.add_argument("--production-seed", type=int, default=DEFAULT_PRODUCTION_SEED)
    parser.add_argument("--production-basename", default=DEFAULT_PRODUCTION_BASENAME)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    regions = [r.strip().lower() for r in args.regions.split(",") if r.strip()]
    unknown = set(regions) - {"iraq", "lebanon"}
    if unknown:
        raise SystemExit(f"Unknown region(s): {', '.join(sorted(unknown))}. Choose from: iraq, lebanon")

    rows = []
    if "iraq" in regions:
        rows += generate_rows(args.count, args.seed)
    if "lebanon" in regions:
        rows += generate_lebanon_rows(args.lebanon_count, args.lebanon_seed)

    if not rows:
        raise SystemExit("No regions selected; nothing to generate.")

    csv_path = args.output_dir / f"{args.basename}.csv"
    shp_path = args.output_dir / f"{args.basename}.shp"

    write_csv(rows, csv_path)
    write_shapefile(rows, shp_path)

    print(f"Wrote CSV: {csv_path} ({len(rows)} rows)")
    print(f"Wrote shapefile: {shp_path}")
    print(f"Regions: {', '.join(regions)}")

    if args.with_production:
        if args.production_well:
            well = next((r for r in rows if r["well_id"] == args.production_well), None)
            if well is None:
                raise SystemExit(f"--production-well {args.production_well!r} not found among generated wells")
        else:
            well = rows[0]

        start_dt = dt.datetime.fromisoformat(args.production_start)
        readings = generate_production_series(well, args.production_hours, start_dt, args.production_seed)

        prod_csv_path = args.output_dir / f"{args.production_basename}.csv"
        prod_shp_path = args.output_dir / f"{args.production_basename}.shp"

        write_production_csv(readings, prod_csv_path)
        write_production_shapefile(well, readings, prod_csv_path.name, prod_shp_path)

        print(f"Wrote production CSV: {prod_csv_path} ({len(readings)} hourly readings for {well['well_id']})")
        print(f"Wrote production shapefile: {prod_shp_path}")


if __name__ == "__main__":
    main()
