rem Batch script to simplify using run-comp-match on Windows

set WEBOTS_EXECUTABLE=%WEBOTS_HOME%\msys64\mingw64\bin
python %~dp0\run-comp-match %*
