@echo off
echo Welcome to pyphe for Windows. Running pyphe-growthcurves using the following command:
set a=python %~dp0%0 
:argactionstart
if -%1-==-- goto argactionend
set a=%a% %1 & REM Or do any other thing with the argument
shift
goto argactionstart
:argactionend
echo %a%
%a%

