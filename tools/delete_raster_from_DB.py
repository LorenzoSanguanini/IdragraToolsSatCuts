# -*- coding: utf-8 -*-

"""
/***************************************************************************
 IdrAgraTools
 A QGIS plugin to manage water demand simulation with IdrAgra model
 The plugin shares user interfaces and tools to manage water in irrigation districts
-------------------
		begin				: 2020-12-01
		copyright			: (C) 2020 by Enrico A. Chiaradia
		email				    : enrico.chiaradia@unimi.it
 ***************************************************************************/

/***************************************************************************
 *																		   *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or	   *
 *   (at your option) any later version.								   *
 *																		   *
 ***************************************************************************/
"""
__author__ = 'Enrico A. Chiaradia'
__date__ = '2020-12-01'
__copyright__ = '(C) 2020 by Enrico A. Chiaradia'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

def deleteRasterFromDB(tableName, DBM):
    tableList = DBM.getTablesList()
    msg = ''
    if tableName in tableList:
        sql = "delete from gpkg_tile_matrix_set where table_name='%s'; " % tableName
        sql += "delete from gpkg_tile_matrix where table_name='%s'; " % tableName

        sql += "delete from gpkg_2d_gridded_coverage_ancillary where tile_matrix_set_name='%s';" % tableName
        sql += "delete from gpkg_2d_gridded_tile_ancillary where tpudt_name='%s';" % tableName

        # sql += "delete from gpkg_metadata_reference where table_name='%s'; "%tableName

        sql += "delete from gpkg_contents where table_name='%s'; " % tableName
        sql += "delete from gpkg_extensions where table_name='%s'; " % tableName
        sql += "delete from sqlite_sequence where name='%s'; " % tableName

        sql += "drop table if exists %s;" % tableName

        sql += "drop trigger if exists %s_tile_column_insert;" % tableName
        sql += "drop trigger if exists %s_tile_column_update;" % tableName
        sql += "drop trigger if exists %s_tile_row_insert;" % tableName
        sql += "drop trigger if exists %s_tile_row_update;" % tableName
        sql += "drop trigger if exists %s_zoom_insert;" % tableName
        sql += "drop trigger if exists %s_zoom_update;" % tableName

        sql += "VACUUM;"

        msg = DBM.executeSQL(sql)

    return msg
