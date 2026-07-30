# IdragraToolsSatCuts

A modified version of [IdragraTools](https://github.com/rita-tools/IdragraTools) that drives
alfalfa cutting dates from satellite imagery instead of a growing-degree-day calendar, and
suspends irrigation around each cutting.

Developed for Scott Valley, California, where alfalfa is irrigated mostly from groundwater and
the timing of cuttings controls both evapotranspiration and irrigation demand.

## Relationship to the original IdragraTools

This is a **derivative work**, not a replacement.

- Baseline: IdragraTools **release 0.4** of 27 February 2025, by Enrico A. Chiaradia
  (University of Milan), from [rita-tools/IdragraTools](https://github.com/rita-tools/IdragraTools).
  The first commit of this repository is that release, unmodified, so the second commit shows
  exactly what was changed.
- Modifications by Lorenzo Sanguanini (University of California, Davis), July 2026.
- Licence unchanged: GNU General Public License (see `LICENSE`).

The plugin is renamed and uses its own processing provider id (`idragrasatcuts`), so it can be
installed **alongside** the original IdragraTools in the same QGIS profile without either one
interfering with the other.

## What was changed

| Area | Change |
|---|---|
| Database schema | New `idr_forced_cuts` table (`field_id`, `year`, `cut_date`); new `irr_halt_days` column on `idr_crop_types`, default 7 |
| New algorithm | *Import satellite cuts* — loads externally detected cutting dates into `idr_forced_cuts` |
| Crop types form | `irr_halt_days` exposed for editing |
| Set simulation | *Use satellite-detected cuts* option; when off, the standard GDD calendar is used |
| Export | Writes `geodata/forced_cuts.txt` and `geodata/irr_halt_days.txt` |
| Coexistence | Own provider id, relative package imports, separate `QSettings` namespace |

Fields without a valid satellite series always fall back to the GDD-based calendar, so a partial
set of detected cuttings is a usable input.

## Requirement: the patched IdrAgra executable

`forced_cuts.txt` and `irr_halt_days.txt` are read by a **modified IdrAgra**, available at
[LorenzoSanguanini/IdragraSatCuts](https://github.com/LorenzoSanguanini/IdragraSatCuts).

The `bin/idragra.exe` shipped in this repository is the **original** executable inherited from
upstream. It ignores both files, silently: the export succeeds, the simulation runs, and the
cuttings are simply never imposed. Replace it with a build from the repository above, or point
the plugin at that executable in the plugin settings.

## Installation

1. Close QGIS.
2. Download this repository as a zip and extract it.
3. Rename the extracted folder to **`IdragraToolsSatCuts`** (capitalisation matters).
4. Copy it into the QGIS plugin folder, usually
   `C:\Users\YOURNAME\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`.
5. Start QGIS, then *Plugins* → *Manage and Install Plugins...* → *Installed*, and tick
   **Idragra Tools SatCuts**.

Tested on Windows with QGIS 3.28 or later.

## Citation

Sanguanini, L., Foglia, L., Zaccaria, D., Chiaradia, E.A., Gandolfi, C. *Field-level
evapotranspiration calibration enables estimations of alfalfa groundwater withdrawals for
irrigation in Scott Valley, CA.*

Please also cite the original IdragraTools and the IdrAgra model.
