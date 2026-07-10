' Q&L 纪念日桌面便签 - 双击运行
' 右键可关闭

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' 获取当前目录
scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
htmlPath = "file:///" & Replace(scriptDir & "\widget.html", "\", "/")

' 启动 Edge 无边框模式
cmd = "msedge --app=""" & htmlPath & """ --window-size=360,520"
objShell.Run cmd, 1, False
