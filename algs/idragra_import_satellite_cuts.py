# -*- coding: utf-8 -*-

"""
/***************************************************************************
 IdrAgraTools
 A QGIS plugin to manage water demand simulation with IdrAgra model
 -------------------
 Import satellite-detected cuts (harvest dates) produced by the external
 "cuts_recognizer" script into the simulation database.

 The script produces one CSV per year, named {year}_alfalfa_cuts.csv, with
 columns: field_id, cut_date. Only the fields whose satellite series was
 recognised as VALID (at least two detected cuts) are listed; all the other
 fields keep using the standard GDD-based calendar of IdrAgra.

 The dates already include the -7 days offset applied by the external script
 (the NDVI drop follows the actual cut by about a week).
 ***************************************************************************/
"""

__author__ = 'Idragra Tools - satellite cuts extension'

import os

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterString,
                       QgsProject)

from ..tools.sqlite_driver import SQLiteDriver
from ..tools.satellite_cuts import importCutsFromFolder


class IdragraImportSatelliteCuts(QgsProcessingAlgorithm):
    DB_FILENAME = 'DB_FILENAME'
    FILE_DIR = 'FILE_DIR'
    YEARS = 'YEARS'
    REPLACE = 'REPLACE'
    FEEDBACK = None
    DBM = None

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdragraImportSatelliteCuts()

    def name(self):
        return 'IdragraImportSatelliteCuts'

    def displayName(self):
        return self.tr('Satellite-detected cuts')

    def group(self):
        return self.tr('Import')

    def groupId(self):
        return 'IdragraImport'

    def shortHelpString(self):
        helpStr = """
                        The algorithm imports the alfalfa cut dates detected from satellite images.
                        Files are produced by the external "cuts_recognizer" script and must be named
                        {year}_alfalfa_cuts.csv, with the columns "field_id" and "cut_date".
                        Only fields with a valid satellite series are listed in those files: all other
                        fields will keep using the standard GDD-based calendar of IdrAgra.
                        <b>Parameters:</b>
                        DB filename: the file path to the database [DB_FILENAME]
                        Files directory: the folder with the {year}_alfalfa_cuts.csv files [FILE_DIR]
                        Years: optional space separated list of years to import (empty = all) [YEARS]
                        Replace existing: delete the cuts already stored for the imported years [REPLACE]
                        """
        return self.tr(helpStr)

    def icon(self):
        self.alg_dir = os.path.dirname(__file__)
        return QIcon(os.path.join(self.alg_dir, 'idragra_satcuts_tool.png'))

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(self.DB_FILENAME, self.tr('DB filename'),
                                                     QgsProcessingParameterFile.Behavior.File, '*.*', '', False,
                                                     self.tr('Geopackage (*.gpkg);;All files (*.*)')))

        self.addParameter(QgsProcessingParameterFile(self.FILE_DIR, self.tr('Files directory'),
                                                     QgsProcessingParameterFile.Behavior.Folder))

        self.addParameter(QgsProcessingParameterString(self.YEARS, self.tr('Years (empty = all)'),
                                                       '', False, True))

        self.addParameter(QgsProcessingParameterBoolean(self.REPLACE,
                                                        self.tr('Replace existing cuts of the imported years'),
                                                        True))

    def processAlgorithm(self, parameters, context, feedback):
        self.FEEDBACK = feedback
        dbFilename = self.parameterAsFile(parameters, self.DB_FILENAME, context)
        fileDir = self.parameterAsFile(parameters, self.FILE_DIR, context)
        yearsStr = self.parameterAsString(parameters, self.YEARS, context)
        replace = self.parameterAsBoolean(parameters, self.REPLACE, context)

        yearList = []
        if yearsStr and yearsStr.strip():
            for tok in yearsStr.replace(',', ' ').split():
                try:
                    yearList.append(int(tok))
                except Exception:
                    pass

        # open db connection
        self.DBM = SQLiteDriver(dbFilename, False, None, self.FEEDBACK, self.tr, QgsProject.instance())

        summary = importCutsFromFolder(self.DBM, fileDir,
                                       yearList if yearList else None,
                                       replace, self.FEEDBACK, self.tr)

        total = sum(summary.values()) if summary else 0
        self.FEEDBACK.pushInfo(self.tr('Imported %s cuts over %s year(s).')
                               % (total, len(summary)))
        self.FEEDBACK.pushInfo(self.tr('Remember to enable "Use satellite-detected cuts" '
                                       'in Set simulation, then export the simulation again.'))

        return {self.DB_FILENAME: dbFilename, 'IMPORTED': total}
