@echo off
setlocal
set SCRIPT_DIR=%~dp0
pushd %SCRIPT_DIR%\..\..
python -m student_app.interface.cli_interface %*
popd

