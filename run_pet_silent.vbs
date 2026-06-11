' Silent launch script - hides console window
' 静默启动脚本 - 隐藏控制台窗口

Set oFS = CreateObject("Scripting.FileSystemObject")
strScriptPath = WScript.ScriptFullName
strProjectDir = oFS.GetParentFolderName(strScriptPath)

' Build command to run the pet app. Requires conda to be available on PATH.
strCmd = "cmd /c cd /d """ & strProjectDir & """ && call conda activate desktop-pet && set PYTHONPATH=src && python -m pet_app.main"

' Execute command hidden (window style 0)
Set oShell = CreateObject("WScript.Shell")
oShell.Run strCmd, 0, False
