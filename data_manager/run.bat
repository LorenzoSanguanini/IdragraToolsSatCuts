REM Change OSGeo4W_ROOT to point to your install of QGIS.

SET OSGEO4W_ROOT=C:\Program Files\QGIS 3.10

CALL "%OSGEO4W_ROOT%\bin\o4w_env.bat"
CALL "%OSGEO4W_ROOT%\bin\qt5_env.bat"
CALL "%OSGEO4W_ROOT%\bin\py3_env.bat"

"C:\Program Files\QGIS 3.10\apps\Python37\python.exe" "data_manager_mainwindow.py"