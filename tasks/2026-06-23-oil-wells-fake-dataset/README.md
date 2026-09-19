# oil-wells-fake-dataset

Created: 2026-06-23

Closes out the 3 remaining checklist items on scds#207 (Vikunja Work #338): a production
time-series shapefile, hypothetical Lebanon offshore wells, and a GeoServer workspace yml.

## Goal

Generate a seeded, reproducible synthetic dataset of oil wells for GeoServer demo loading.
Produces a CSV and a point shapefile (WGS84), suitable for upload to any GIS platform
without requiring real well data.

## What it generates

### `OilWells.csv` / `OilWells.shp{,.shx,.dbf,.prj,.cpg}`

87 point features, 10 columns: `well_id`, `well_name`, `field_name`, `status`, `oil_type`,
`depth_m`, `discovery_year`, `operator`, `lon`, `lat`.

- **75 onshore wells in Iraq** (`well_id` prefix `IQ-OW-`), randomly distributed within
  Iraq's bounding box (west 38.79°E, east 48.57°E, south 29.06°N, north 37.38°N).
  Seed **20260610**.
- **12 hypothetical offshore wells in Lebanon** (`well_id` prefix `LB-OW-`), distributed
  within a bbox west of the Lebanese coastline and inside Lebanon's approximate
  latitude span (west 32.90°E, east 34.95°E, south 33.05°N, north 34.65°N) — clear of
  land (coast runs ~35.1–36.0°E). Seed **20260711**.
  - `field_name` draws from `Block 1`..`Block 10`, mirroring Lebanon's real offshore
    exploration block numbering (public knowledge — no real well/discovery data used).
  - `operator` draws from real-world offshore consortium members
    (TotalEnergies, Eni, QatarEnergy) plus the existing demo entries, for flavor only.
  - `depth_m` uses a deeper range (3200–6800m) than Iraq's onshore wells (1200–5200m),
    reflecting combined water depth + sub-seabed reservoir depth typical of East
    Mediterranean prospects.
  - `discovery_year` is restricted to 2018–2025 (Lebanon's offshore licensing rounds
    began 2017/2018).
  - `status` is weighted toward `planned`/`inactive` over `active` (offshore blocks are
    mostly at exploration/appraisal stage, unlike Iraq's mostly-active onshore fields).
  - There's no separate `country` column — Iraq vs. Lebanon is distinguishable by the
    `well_id`/`well_name` prefix and by `field_name`, keeping the existing 10-column
    schema unchanged for backward compatibility with anything already consuming it.
- Only the Iraq wells are produced by default (`./run.sh` with no flags, or bare
  `main.py`); Lebanon wells are additive via `--regions iraq,lebanon` (see below).
  The committed `dataset/` reference and the demo's `./run.sh` both include both regions.

### `OilWellProduction.csv` / `OilWellProduction.shp{,.shx,.dbf,.prj,.cpg}` — time-series format

One well (`IQ-OW-001` by default) with 5 years of hourly oil-production data —
43,830 readings (365.25 × 24 × 5).

**Format decision:** a plain point shapefile isn't a natural fit for ~44k time-series
readings against a single feature — shapefiles model one set of attributes per geometry,
not a one-to-many relationship. So this splits into two files, the same pattern used for
sensor/SCADA time series joined onto GIS features in most platforms:

- **`OilWellProduction.csv`** — the actual time series, keyed by `well_id` + `timestamp`
  (columns: `well_id`, `timestamp` [ISO 8601], `barrels_per_day`). 43,830 rows for one
  well; the `well_id` key means more wells' series could be appended later without a
  schema change.
- **`OilWellProduction.shp`** — a single point feature for the well, carrying its core
  attributes (`well_id`, `well_name`, `field_name`, `country`, `status`, `oil_type`,
  `depth_m`, `operator`, `lon`, `lat`) plus:
  - `prod_csv` — filename of the companion CSV (`OilWellProduction.csv`), so anything
    reading the shapefile's attribute table can find the linked time series
  - `prod_strt` / `prod_end` — ISO timestamps of the series' first/last reading
  - `n_readng` — reading count (43830)
  - `avg_bpd` / `min_bpd` / `max_bpd` — summary stats, so a quick look at the shapefile
    alone gives a sense of the data without opening the CSV

Production values follow an exponential decline curve (5–20%/year) with seasonal
variation, multiplicative noise, and occasional maintenance shutdowns (bpd=0),
seeded per well for reproducibility.

**GeoServer note:** the shapefile alone is enough for a WMS point layer showing where
the well is and its summary stats. To make the full hourly series queryable (e.g. WFS
time filtering, charts), the natural next step is importing `OilWellProduction.csv` into
a database table (e.g. via `ogr2ogr` into PostGIS) and exposing it as a SQL view joined
on `well_id` — out of scope for this demo, not done here.

## External repos / dependencies

- Copied from `$REPOS_ROOT/cams_geospatial_platform` branch `orski/oil-wells-demo-dataset`
  (`tools/gen_oil_wells.py` + `data/datasets_geoserver/OilWellsIraq/`). Not a live
  dependency — the generator is vendored here as `main.py`. Pure stdlib: no pip deps.
- `geoserver_workspace.yml` follows the schema of
  `$REPOS_ROOT/cams_geospatial_platform/src/workspaces.yml` (documented in
  `src/workspaces_spec.yml`, consumed by `src/create_workspaces_geoserver.py`) — the
  same config format used for the existing GeoServer demo workspaces. Only the
  GeoServer-provisioning fields are included (not GeoNetwork metadata / feature
  catalogue, which are a separate concern in that pipeline and weren't requested here).

## How to run

```bash
./run.sh
```

Regenerates `output/OilWells.{csv,shp,shx,dbf,prj,cpg}` and
`output/OilWellProduction.{csv,shp,shx,dbf,prj,cpg}`. Pass extra flags to override
defaults — `run.sh` already passes `--regions iraq,lebanon --with-production`, so most
overrides only need `--count`/`--seed` etc.:

```bash
./run.sh --count 200 --seed 99
```

Or call `main.py` directly for full control:

```bash
python main.py --help
python main.py --output-dir output --regions iraq          # Iraq only, original 75 wells
python main.py --output-dir output --regions iraq,lebanon --lebanon-count 20
python main.py --output-dir output --with-production --production-well IQ-OW-002
```

Key flags: `--regions` (comma-separated `iraq`,`lebanon`; default `iraq`),
`--lebanon-count`/`--lebanon-seed`, `--with-production` (adds the production
CSV+shapefile), `--production-well`/`--production-hours`/`--production-start`/`--production-seed`.

## Inputs

None — the generator is self-contained and deterministic from the seed.

## Outputs

`output/` — regenerated on each `./run.sh` run. Both `output/` and the committed
reference copy in `dataset/` are tracked in this repo (there's no `.gitignore` here);
`dataset/` is kept in sync with `output/` after each run so it's usable without running
anything.

## GeoServer workspace config

`geoserver_workspace.yml` — provisioning config for the `oil_wells_demo` workspace
(store `oil_wells_store`, layers `OilWells` + `OilWellProduction`). Expects the six
shapefile component files for both layers to be placed under `data/OilWells/` inside
GeoServer's data directory before running `create_workspaces_geoserver.py` against it —
see comments in the file for details.

> **Note on the DBF:** the `.dbf` header embeds a "last modified" date that changes
> each day the file is written, so a freshly regenerated `.dbf` will differ from the
> committed one in the first 4 bytes of the header. All actual field data is identical.
