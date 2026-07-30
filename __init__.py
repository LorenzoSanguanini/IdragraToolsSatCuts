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

import os
import sys
import inspect

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
	# NOTE (SatCuts): the plugin folder is NOT inserted in sys.path any more.
	# All internal imports are relative, so nothing is needed here; injecting the
	# folder would make the generic package names "tools"/"forms" resolve to this
	# plugin also for the original IdragraTools, breaking it when both are installed.
	
	from .idragratools_plugin import IdrAgraTools
	return IdrAgraTools(iface)
