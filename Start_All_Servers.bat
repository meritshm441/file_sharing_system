@echo off
echo Starting both servers...
start "TCP Server" executables\tcp_file_server.exe
start "UDP Server" executables\udp_notification_server.exe
echo Servers started in separate windows
pause