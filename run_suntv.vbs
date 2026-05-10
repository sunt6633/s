' run_suntv.vbs - SunTV 后台启动器
' 双击运行，无窗口，关闭不影响服务

Set ws = CreateObject("WScript.Shell")
Dim env
Set env = ws.Environment("PROCESS")

' 设置环境变量
env("USERNAME") = "admin"
env("PASSWORD") = "moontv2026"
env("SITE_NAME") = "SunTV"
env("NODE_ENV") = "production"
env("HOSTNAME") = "0.0.0.0"
env("PORT") = "3000"

' 工作目录
ws.CurrentDirectory = "D:\moontv\src"

' 启动 node（0=隐藏窗口，false=不等待）
ws.Run "node .next\standalone\server.js", 0, false

' 提示（可选，会显示在任务栏通知区域）
' CreateObject("WScript.Shell").Popup "SunTV 正在后台启动...", 3, "SunTV", 64
