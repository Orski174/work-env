# oil-wells-fake-dataset

Created: 2026-06-23

## Goal

Generate a seeded, reproducible synthetic dataset of 75 oil wells in Iraq for GeoServer
demo loading. Produces a CSV and a point shapefile (WGS84), suitable for upload to any
GIS platform without requiring real well data.

## What it generates

- **`OilWells.csv`** — 75 rows, 10 columns: `well_id`, `well_name`, `field_name`,
  `status`, `oil_type`, `depth_m`, `discovery_year`, `operator`, `lon`, `lat`
- **`OilWells.shp/.shx/.dbf/.prj/.cpg`** — point shapefile, same 75 features, WGS84

Wells are randomly distributed within Iraq's bounding box:

| Edge  | Longitude / Latitude |
|-------|----------------------|
| West  | 38.79° E             |
| East  | 48.57° E             |
| South | 29.06° N             |
| North | 37.38° N             |

Default seed: **20260610** — same seed always produces the same CSV and geometry.

> **Note on the DBF:** the `.dbf` header embeds a "last modified" date that changes
> each day the file is written, so `dataset/OilWells.dbf` and a freshly generated
> `output/OilWells.dbf` will differ in the first 4 bytes of the header. All actual
> field data is identical.

## External repos / dependencies

- Copied from `$REPOS_ROOT/cams_geospatial_platform` branch `orski/oil-wells-demo-dataset`
  (`tools/gen_oil_wells.py` + `data/datasets_geoserver/OilWellsIraq/`). Not a live
  dependency — the generator is vendored here as `main.py`. Pure stdlib: no pip deps.

## How to run

```bash
./run.sh
```

Regenerates `output/OilWells.{csv,shp,shx,dbf,prj,cpg}` (gitignored). Pass extra flags
to override defaults:

```bash
./run.sh --count 200 --seed 99
```

Or call `main.py` directly:

```bash
python main.py --help
```

## Inputs

None — the generator is self-contained and deterministic from the seed.

## Outputs

`output/` (gitignored) — regenerated on each `./run.sh` run.

A committed reference copy lives in `dataset/` and is available without running anything.
