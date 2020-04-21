REM Created 03/05/2020
REM Author Mike McGrail
REM Usage: .bat wrapper to call python script with arguments
REM Source: https://serverfault.com/questions/22443/do-windows-batch-files-have-a-construction/22541#22541
set args=%1
shift
:start
if [%1] == [] goto done
set args=%args% %1
shift
goto start

:done
REM uncomment the following line to log the arguments received:
REM echo %DATE% %TIME% "file=alert.bat" %args% >> log\test.log
"C:\Program Files\Python37\python.exe" D:\solarwinds_to_splunk\test_alert.py %args%