# 💝 纪念日 & 倒计时

双人专属纪念日 Web 应用 + 桌面便签。可自定义双方名字，开箱即用。

## 功能一览

| 页面 | 功能 |
|------|------|
| 🏠 **首页** | 纪念日月历、倒计时卡片、双人留言板、恋爱相册、节假日标注 |
| ⚙️ **后台** | 管理倒计时/纪念日/相册/留言，系统设置（名字、密码、日期），密码保护 |
| 📌 **桌面便签** | Windows 原生悬浮窗，纪念日随时可见 |

## 首次使用

访问后台 `admin.html`，默认密码：`Lyx20050915@`

在 ⚙️ 设置中配置你的名字和 TA 的名字，保存后全站生效。

## 功能一览

| 页面 | 功能 |
|------|------|
| 🏠 **首页** (`index.html`) | 纪念日月历、倒计时卡片、双人留言板、恋爱相册、节假日标注 |
| ⚙️ **后台** (`admin.html`) | 管理倒计时/纪念日/相册/留言，系统设置，密码保护 |
| 📌 **桌面便签** (`desk_widget.py`) | Windows 原生悬浮窗，纪念日随时可见 |

## 快速部署

### 服务器部署（Linux / Nginx + MariaDB）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 MariaDB 数据库
#    编辑 server.py，修改 DB_CONFIG 里的密码

# 3. 启动
python server.py

# 访问: http://127.0.0.1:5000
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name 你的域名或IP;

    root /var/www/lq;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
    }
}
```

### 桌面便签（Windows）

```powershell
pip install -r requirements_widget.txt
python desk_widget.py
```

支持右键菜单刷新/关闭，自动连接服务器获取数据。

## 默认密码

后台管理默认密码：`Lyx20050915@`

登录后可在 ⚙️ 设置中修改。

## 技术栈

- **前端**: 纯 HTML/CSS/JS，毛玻璃 UI，赛博粉暖色调
- **后端**: Python Flask + MariaDB
- **桌面端**: Python PySide6
- **数据**: RESTful API，所有数据持久化到数据库

## 项目文件

```
index.html          主页面（包含所有功能 Tab）
admin.html          后台管理
server.py           Flask API 服务
requirements.txt    后端依赖
desk_widget.py      Windows 桌面便签
requirements_widget.txt  桌面便签依赖
widget.html         便签内嵌网页
widget.ps1          便签启动脚本（PowerShell）
widget.vbs          便签启动脚本（VBScript）
```
