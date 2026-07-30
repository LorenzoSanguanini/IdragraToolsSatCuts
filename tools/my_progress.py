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

class MyProgress:
	def __init__(self):
		pass
		
	def setConsoleInfo(self,text):
		text = text.encode('utf-8')
		print('CONSOLE_INFO: %s'%text)
		
	def error(self,text):
		text = text.encode('utf-8')
		print('ERROR: %s'%text)

	def setProgress(self,val):
		self.setPercentage(val)

	def setPercentage(self,val,printPerc = False):
		if printPerc:
			nblock = int(val/10)
			blocks = ['#']*nblock
			lines = ['_']*(10-nblock)
			bar = 'PROGRESS: '+blocks+lines
			print(bar, end="\r")

		else:
			print('PERC: %s' %int(val))

	def setText(self, text):
		text = text.encode('utf-8')
		print('TEXT: %s'%text)
		
	def setInfo(self,text, error=False):
		text = text.encode('utf-8')
		if error:
			print('ERROR: %s' %text)
		else:
			print('INFO:  %s' %text)
			
	def pushInfo(self,text, error=False):
		text = text.encode('utf-8')
		if error:
			print('ERROR: %s' %text)
		else:
			print('INFO:  %s' %text)
		
	def setCommand(self, text):
		text = text.encode('utf-8')
		print('CMD: %s'%text)

	def reportError(self,text,error=False):
		text = text.encode('utf-8')
		if error:
			print('FATAL ERROR: %s' %text)
		else:
			print('WARNING:  %s' %text)
		
		