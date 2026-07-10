# Q&L 桌面纪念日便签
# 右键 widget.html → "创建快捷方式"，然后把这个改名 widget.ps1
# 也可以直接命令行运行：powershell -ExecutionPolicy Bypass -File widget.ps1

$htmlPath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "widget.html"
$url = "file:///" + ($htmlPath -replace '\\', '/')

# 用 Edge app 模式打开
$edge = Start-Process "msedge" -ArgumentList "--app=`"$url`"","--window-size=360,520","--hide-crash-restore-bubble" -PassThru

# 等待窗口出现
Start-Sleep -Seconds 2

# 用 C# 去边框
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinAPI {
    [DllImport("user32.dll")] public static extern IntPtr FindWindow(string className, string windowName);
    [DllImport("user32.dll")] public static extern int SetWindowLong(IntPtr hWnd, int nIndex, int dwNewLong);
    [DllImport("user32.dll")] public static extern int GetWindowLong(IntPtr hWnd, int nIndex);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
    public const int GWL_STYLE = -16;
    public const int WS_CAPTION = 0x00C00000;
    public const int WS_THICKFRAME = 0x00040000;
    public static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
    public const uint SWP_NOSIZE = 0x0001;
    public const uint SWP_NOMOVE = 0x0002;
    public const uint SWP_FRAMECHANGED = 0x0020;
}
"@

Get-Process | Where-Object { $_.ProcessName -eq "msedge" } | ForEach-Object {
    $h = $_.MainWindowHandle
    if ($h -ne [IntPtr]::Zero) {
        $style = [WinAPI]::GetWindowLong($h, [WinAPI]::GWL_STYLE)
        $newStyle = $style -band -bnot ([WinAPI]::WS_CAPTION -bor [WinAPI]::WS_THICKFRAME)
        [WinAPI]::SetWindowLong($h, [WinAPI]::GWL_STYLE, $newStyle) > $null
        [WinAPI]::SetWindowPos($h, [WinAPI]::HWND_TOPMOST, 0, 0, 0, 0, [WinAPI]::SWP_NOSIZE -bor [WinAPI]::SWP_NOMOVE -bor [WinAPI]::SWP_FRAMECHANGED) > $null
    }
}
