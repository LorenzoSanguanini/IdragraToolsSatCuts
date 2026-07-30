# -*- coding: utf-8 -*-

"""
/***************************************************************************
 IdrAgraTools — Satellite-detected cuts support
 -------------------
 Gestisce i tagli (sfalci) rilevati da immagini satellitari:

   * schema      : crea/aggiorna le strutture nel geopackage
                   - tabella idr_forced_cuts (field_id, year, cut_date)
                   - colonna idr_crop_types.irr_halt_days
   * import      : legge i CSV {anno}_alfalfa_cuts.csv prodotti dallo script
                   esterno "cuts_recognizer" e li scrive in idr_forced_cuts
   * export      : converte i tagli (che sono proprieta' del POLIGONO) nelle
                   celle della griglia ALLA RISOLUZIONE CORRENTE e scrive
                   - forced_cuts.txt          (row col year doy)
                   - irrigation_blackout.txt  (row col year doy_start doy_end)

 NOTA IMPORTANTE SULLA RISOLUZIONE
 ---------------------------------
 I tagli sono memorizzati per id di poligono, MAI per cella. La conversione
 poligono -> cella avviene solo in fase di export, usando l'estensione e la
 dimensione di cella correnti. Cambiando la risoluzione del dominio da
 IdragraTools, i tagli seguono automaticamente le celle giuste senza dover
 reimportare nulla.
 ***************************************************************************/
"""

__author__ = 'Idragra Tools - satellite cuts extension'

import os
import glob
import csv
from datetime import datetime


# =============================================================================
#  SCHEMA
# =============================================================================
def ensureSchema(DBM, feedback=None):
    """Crea le strutture necessarie se mancanti (funziona anche su geopackage
    gia' esistenti, creati da versioni precedenti del plugin)."""
    msgs = []

    # tabella dei tagli forzati
    sql = """CREATE TABLE IF NOT EXISTS idr_forced_cuts (
                fid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                field_id integer NOT NULL,
                year integer NOT NULL,
                cut_date text NOT NULL);"""
    msgs.append(DBM.executeSQL(sql))

    # colonna irr_halt_days in idr_crop_types (se non c'e' gia')
    if not _hasColumn(DBM, 'idr_crop_types', 'irr_halt_days'):
        msgs.append(DBM.executeSQL(
            "ALTER TABLE idr_crop_types ADD COLUMN irr_halt_days integer;"))
        msgs.append(DBM.executeSQL(
            "UPDATE idr_crop_types SET irr_halt_days = 7 WHERE irr_halt_days IS NULL;"))
        if feedback:
            feedback.pushInfo('Added column irr_halt_days to idr_crop_types (default 7)')

    return [m for m in msgs if m]


def _hasColumn(DBM, tableName, colName):
    try:
        return colName in (DBM.getFieldsList(tableName) or [])
    except Exception:
        return False


# =============================================================================
#  IMPORT dei CSV prodotti da cuts_recognizer
# =============================================================================
def importCutsFromFolder(DBM, folder, yearList=None, replace=True, feedback=None, tr=None):
    """Importa tutti i file {anno}_alfalfa_cuts.csv presenti in `folder`.

    Ritorna un dizionario di riepilogo {anno: n_tagli}.
    `replace=True` cancella i tagli gia' presenti per gli anni importati.
    """
    if tr is None:
        tr = lambda x: x

    ensureSchema(DBM, feedback)

    pattern = os.path.join(folder, '*_alfalfa_cuts.csv')
    fileList = sorted(glob.glob(pattern))
    if not fileList:
        raise Exception(tr('No "*_alfalfa_cuts.csv" file found in %s') % folder)

    summary = {}
    for f in fileList:
        base = os.path.basename(f)
        try:
            year = int(base.split('_')[0])
        except Exception:
            if feedback:
                feedback.reportError(tr('Skipped (cannot read year from name): %s') % base)
            continue
        if yearList and year not in yearList:
            continue

        n = importCutsFromCSV(DBM, f, year, replace, feedback, tr)
        summary[year] = n
        if feedback:
            feedback.pushInfo(tr('Imported %s cuts for year %s from %s') % (n, year, base))

    return summary


def importCutsFromCSV(DBM, filename, year=None, replace=True, feedback=None, tr=None):
    """Importa un singolo CSV (colonne: field_id, cut_date [, year]).
    Ritorna il numero di tagli importati."""
    if tr is None:
        tr = lambda x: x

    ensureSchema(DBM, feedback)

    rows = []
    with open(filename, 'r', newline='', encoding='utf-8-sig') as fh:
        reader = csv.DictReader(fh)
        cols = [c.strip().lower() for c in (reader.fieldnames or [])]
        if 'field_id' not in cols or 'cut_date' not in cols:
            raise Exception(tr('File %s must contain the columns "field_id" and "cut_date"')
                            % os.path.basename(filename))
        for rec in reader:
            rec = { (k.strip().lower() if k else k): v for k, v in rec.items() }
            try:
                fid = int(str(rec['field_id']).strip())
            except Exception:
                continue
            cdate = str(rec['cut_date']).strip()
            if not cdate:
                continue
            # anno: dalla colonna se c'e', altrimenti dal nome file, altrimenti dalla data
            if rec.get('year'):
                try:
                    y = int(str(rec['year']).strip())
                except Exception:
                    y = year
            else:
                y = year
            if y is None:
                try:
                    y = datetime.strptime(cdate[:10], '%Y-%m-%d').year
                except Exception:
                    continue
            rows.append((fid, y, cdate[:10]))

    if not rows:
        return 0

    years = sorted(set(r[1] for r in rows))
    if replace:
        for y in years:
            DBM.executeSQL("DELETE FROM idr_forced_cuts WHERE year = %s;" % y)

    # inserimento a blocchi (piu' veloce di una query per riga)
    CHUNK = 500
    for i in range(0, len(rows), CHUNK):
        chunk = rows[i:i + CHUNK]
        values = ', '.join("(%s, %s, '%s')" % (r[0], r[1], r[2]) for r in chunk)
        DBM.executeSQL("INSERT INTO idr_forced_cuts (field_id, year, cut_date) VALUES %s;" % values)

    return len(rows)


# =============================================================================
#  LETTURA dal database
# =============================================================================
def getForcedCuts(DBM, yearList=None):
    """Ritorna {(field_id, year): [date 'YYYY-MM-DD', ...]}"""
    flt = None
    if yearList:
        flt = "year IN (%s)" % ', '.join(str(int(y)) for y in yearList)
    try:
        res = DBM.getDataFromTable(tableName='idr_forced_cuts',
                                   fieldList=['field_id', 'year', 'cut_date'],
                                   filter=flt)
    except Exception:
        return {}
    cuts = {}
    for row in (res or []):
        try:
            key = (int(row[0]), int(row[1]))
        except Exception:
            continue
        cuts.setdefault(key, []).append(str(row[2])[:10])
    return cuts


def getHaltDaysByCrop(DBM, default=7):
    """Ritorna {crop_id: irr_halt_days}. Se la colonna manca, dizionario vuoto."""
    if not _hasColumn(DBM, 'idr_crop_types', 'irr_halt_days'):
        return {}
    try:
        res = DBM.getDataFromTable(tableName='idr_crop_types',
                                   fieldList=['id', 'irr_halt_days'])
    except Exception:
        return {}
    out = {}
    for row in (res or []):
        try:
            cid = int(row[0])
        except Exception:
            continue
        try:
            out[cid] = int(row[1]) if row[1] is not None else default
        except Exception:
            out[cid] = default
    return out


# =============================================================================
#  EXPORT: poligono -> celle -> file di testo per IdrAgra
# =============================================================================
def dateToDoy(dateStr):
    d = datetime.strptime(str(dateStr)[:10], '%Y-%m-%d')
    return d.timetuple().tm_yday


def exportForcedCuts(cutsByCell, outFile):
    """Scrive forced_cuts.txt.
    cutsByCell: lista di tuple (row, col, year, doy) — 1-based, come cells.txt.
    """
    rows = sorted(set(cutsByCell))
    with open(outFile, 'w') as f:
        f.write('%s\n' % len(rows))
        f.write('row\tcol\tyear\tdoy\n')
        for r in rows:
            f.write('%s\t%s\t%s\t%s\n' % r)
    return len(rows)


def exportIrrHaltDays(haltDaysByCrop, outFile):
    """Scrive irr_halt_days.txt: i giorni di sospensione dell'irrigazione per COLTURA.

    E' il valore della colonna irr_halt_days di idr_crop_types, quello che si imposta
    in Crop types. IdrAgra lo applica attorno a OGNI taglio della coltura, sia che le
    date vengano dal satellite sia che vengano dal calendario a gradi-giorno: due campi
    della stessa coltura devono ricevere lo stesso trattamento, altrimenti la differenza
    di acqua fra loro dipende da quanto bene ha funzionato il riconoscitore satellitare
    invece che dall'agronomia.

    Sostituisce irrigation_blackout.txt, che elencava le finestre cella per cella e
    poteva quindi coprire solo le celle con tagli satellitari.

    Le colture non elencate non sospendono l'irrigazione.
    """
    rows = []
    for cid in sorted(haltDaysByCrop or {}):
        days = haltDaysByCrop[cid]
        if days is None:
            continue
        try:
            days = int(days)
        except (TypeError, ValueError):
            continue
        if days > 0:
            rows.append((int(cid), days))

    with open(outFile, 'w') as f:
        f.write('%s\n' % len(rows))
        f.write('crop_id\tdays\n')
        for r in rows:
            f.write('%s\t%s\n' % r)
    return len(rows)


def exportIrrigationBlackout(cutsByCell, haltDaysByCell, outFile, defaultHalt=7,
                             yearLength=None):
    """Scrive irrigation_blackout.txt: una finestra +/- halt giorni per ogni taglio.

    cutsByCell     : lista di (row, col, year, doy)
    haltDaysByCell : dizionario {(row, col): halt_days} (da irr_halt_days della
                     coltura di quella cella); se assente si usa defaultHalt.
    """
    windows = []
    for (r, c, y, doy) in cutsByCell:
        halt = haltDaysByCell.get((r, c), defaultHalt)
        if halt is None or halt <= 0:
            continue
        maxDoy = yearLength if yearLength else (366 if _isLeap(y) else 365)
        start = max(1, doy - halt)
        end = min(maxDoy, doy + halt)
        windows.append((r, c, y, start, end))

    windows = sorted(set(windows))
    with open(outFile, 'w') as f:
        f.write('%s\n' % len(windows))
        f.write('row\tcol\tyear\tdoy_start\tdoy_end\n')
        for w in windows:
            f.write('%s\t%s\t%s\t%s\t%s\n' % w)
    return len(windows)


def _isLeap(year):
    year = int(year)
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


# =============================================================================
#  Lettura di un raster ASCII grid (.asc)
# =============================================================================
def readAsciiGrid(filename):
    """Ritorna (header_dict, data) con data[row][col], row 0 = riga in alto.
    Gli indici riga/colonna 1-based usati nei file di IdrAgra sono row+1, col+1."""
    header = {}
    data = []
    with open(filename, 'r') as f:
        for _ in range(6):
            parts = f.readline().split()
            header[parts[0].lower()] = float(parts[1])
        for line in f:
            line = line.strip()
            if not line:
                continue
            data.append([float(v) for v in line.split()])
    return header, data


# =============================================================================
#  Costruzione dei file per IdrAgra a partire dai tagli per poligono
# =============================================================================
def buildCellCuts(fieldIdGridFile, cutsByFieldYear, year, soiluseGridFile=None,
                  haltDaysByCrop=None, defaultHalt=7, feedback=None):
    """Converte i tagli del POLIGONO nelle celle della griglia corrente.

    fieldIdGridFile : raster .asc con l'id del poligono di idr_usemap per cella
    cutsByFieldYear : {(field_id, year): ['YYYY-MM-DD', ...]} da getForcedCuts()
    soiluseGridFile : raster .asc con il codice coltura per cella (per irr_halt_days)
    haltDaysByCrop  : {crop_id: giorni di sospensione irrigazione}

    Ritorna (cutsByCell, haltDaysByCell):
        cutsByCell     : lista di (row, col, year, doy)   [1-based]
        haltDaysByCell : {(row, col): halt_days}
    """
    header, grid = readAsciiGrid(fieldIdGridFile)
    nodata = header.get('nodata_value', -9999)

    soilGrid = None
    if soiluseGridFile and haltDaysByCrop and os.path.exists(soiluseGridFile):
        try:
            _, soilGrid = readAsciiGrid(soiluseGridFile)
        except Exception:
            soilGrid = None

    # doy dei tagli per ogni poligono, solo per l'anno richiesto
    doyByField = {}
    for (fid, y), dates in cutsByFieldYear.items():
        if int(y) != int(year):
            continue
        doys = []
        for d in dates:
            try:
                doys.append(dateToDoy(d))
            except Exception:
                continue
        if doys:
            doyByField[int(fid)] = sorted(set(doys))

    if not doyByField:
        return [], {}

    cutsByCell = []
    haltDaysByCell = {}
    for r, rowVals in enumerate(grid):
        for c, val in enumerate(rowVals):
            if val == nodata:
                continue
            fid = int(val)
            doys = doyByField.get(fid)
            if not doys:
                continue
            rr = r + 1          # 1-based, come cells.txt e i file di IdrAgra
            cc = c + 1
            for doy in doys:
                cutsByCell.append((rr, cc, int(year), doy))
            if soilGrid is not None:
                try:
                    cropId = int(soilGrid[r][c])
                    haltDaysByCell[(rr, cc)] = haltDaysByCrop.get(cropId, defaultHalt)
                except Exception:
                    pass

    if feedback:
        feedback.pushInfo('Year %s: %s cuts mapped on %s cells'
                          % (year, len(cutsByCell), len(set((a, b) for a, b, _, _ in cutsByCell))))

    return cutsByCell, haltDaysByCell
