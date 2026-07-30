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

import numpy as np
from osgeo import gdal
import os

def myPrint(x):
	print(x)

def getRasterInfos(laySource):
	raster = gdal.Open(laySource)
	ncols = raster.RasterXSize
	nrows = raster.RasterYSize
	ncells = raster.RasterCount
	proj = raster.GetProjection()
	geotransform = raster.GetGeoTransform()
	xll = geotransform[0]
	yul = geotransform[3]
	dx = geotransform[1]
	dy = geotransform[5]
	yll = yul+dy*nrows
	return {'ncols': ncols, 'nrows':nrows, 'ncells':ncells, 'proj':proj, 'xllcorner':xll, 'yllcorner':yll, 'dx':dx, 'dy':dy, 'cellsize':dx, 'nodata':-9999.0}
	

# loop in list of loaded raster
# 		read matrix
def convertRasterToNumpyArray(laySource): #Input: QgsRasterLayer
	raster = gdal.Open(laySource)
	srcband = raster.GetRasterBand(1)
	nodata = srcband.GetNoDataValue()
	data = srcband.ReadAsArray()
	#make uniform nodata
	data[data == nodata] = -9999.0
	data = data.flatten()
	nValues = len(data)
	data = data.reshape([nValues, 1 ]) 
	return data
	
def save2idragra(data, filepath, type ='REAL', ncols = 1, nrows = 1, xllcorner = -1, yllcorner = -1, cellsize = 250, nodata=-9999.):
	dict = {'REAL': '%.10f', 'DOUBLE': "%.19f", 'INTEGER':'%d'}
	numformat = dict[type]
	
	# get all data
	idx = np.where(np.isnan(data))
	dataToPrint = data[data!=nodata]
	dataToPrint = [numformat % d for d in dataToPrint]
	ndata = len(dataToPrint)
	
	nodata2print = numformat % nodata
	
	f = open(filepath,'w')
	try:
		f.write('ncols ' + str(ncols) + '\n')
		f.write('nrows ' + str(nrows) + '\n')
		f.write('xllcorner ' + str(xllcorner) + '\n')
		f.write('yllcorner ' + str(yllcorner) + '\n')
		f.write('cellsize ' + str(cellsize) + '\n')
		f.write('nodata_value ' + nodata2print+ '\n')
		s = '\n'.join(dataToPrint) + '\n'
		f.write(s)
	except IOError:
		print('Cannot save file: %s' %filepath)
	finally:
		f.close()
		
def exportDataSet(layers, outputPath, logPrinter = None, tr = None):
	if not logPrinter: logPrinter = myPrint
	if not tr: tr = lambda x: x
	c=0
	# Loop through layer and run algorithm
	allData = ''
	nameList = []
	for layer in layers:
		logPrinter(tr('Loading layer: %s')%layer.name())
		nameList.append(layer.name())
		if c == 0:
			# get raster header
			hData = getRasterInfos(layer.source())
			# get data
			allData = convertRasterToNumpyArray(layer.source())
		else:
			allData = np.hstack((allData,convertRasterToNumpyArray(layer.source())))
			
		c +=1
		
	n,r= allData.shape
	logPrinter(tr('n. of cells: %s - n. of layers: %s')%(n,r ))
	
	# make a list zero based indexes
	pos = np.array(range(0,n),np.int32)
		
	minByRow = np.array(allData.min(axis=1))
	
	# n,r = minByRow.shape
	# print('minbyRow shape: %s %s'%(n,r ))
	
	validData = allData[minByRow!=-9999.,:]
	selPos = pos[minByRow!=-9999.]
	
	nrows, ncols =validData.shape
	
	n,r = validData.shape
	logPrinter(tr('n. of valid cells: %s - n. of layers: %s')%(n,r ))
	
	intRaster = ['domain','hydr_cond','hydr_group','soiluse','irr_distr','irr_meth']
	logPrinter(tr('The maps with the folowing names will be considered as integer: %s')%('; '.join(intRaster)))
	
	# save index of valid cells from source raster 
	save2idragra(selPos,  os.path.join(outputPath,'validcell.asc'), \
						'INTEGER', hData['ncols'], hData['nrows'], hData['xllcorner'], hData['yllcorner'], hData['cellsize'], hData['nodata'])
	
	logPrinter(tr('%s array is saved!')%'validcell')
	
	
	# make a dummy raster with cell area (squared units)
	cellArea = hData['cellsize']*hData['cellsize']
	save2idragra(np.array([cellArea]*n),  os.path.join(outputPath,'cellarea.asc'),\
						'REAL', 1, n, hData['xllcorner'], hData['yllcorner'], hData['cellsize'], hData['nodata'])
						
	logPrinter(tr('%s array is saved!')%'cellsize')
	
	c = 0
	for name in nameList:
		type = 'REAL'
		if name in intRaster:
			type = 'INTEGER'
		
		save2idragra(validData[:,c],  os.path.join(outputPath,name+'.asc'),\
							type, 1, n, hData['xllcorner'], hData['yllcorner'], hData['cellsize'], hData['nodata'])
							
		logPrinter(tr('%s array is saved!')%name)
		c+=1
		
	return c+2


if __name__ == '__console__':
	layers = QgsProject.instance().mapLayers().values()
	exportDataSet(layers, 'C:/idragra_code/dataset/rid_data_base', None)
	print('OK')
	