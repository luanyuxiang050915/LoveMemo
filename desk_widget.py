import sys
import json
import os
from datetime import datetime
import requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QMenu, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QAction

SERVER_URL = "http://127.0.0.1:5000/api/data"
WIN_W, WIN_H = 300, 440

PINK = "#e87890"
PINK_LIGHT = "#fce4ec"
BG = "#fff8f9"
TEXT = "#5a3e4b"
TEXT_DIM = "#8b6b7a"


class DeskWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(WIN_W, WIN_H)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - WIN_W - 30, 60)

        self.memorials = []
        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(60 * 60 * 1000)
        QTimer.singleShot(300, self.load_data)

    def init_ui(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

        self.container = QFrame(self)
        self.container.setGeometry(0, 0, WIN_W, WIN_H)
        self.container.setStyleSheet(f"""
            QFrame {{
                background: {BG};
                border-radius: 20px;
                border: 1px solid #f0d0d8;
            }}
        """)

        top_bar = QFrame(self.container)
        top_bar.setGeometry(0, 0, WIN_W, 44)
        top_bar.setStyleSheet(f"""
            QFrame {{
                background: {PINK_LIGHT};
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)

        title = QLabel("💝 纪念日", top_bar)
        title.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        title.move(16, 12)

        self.date_label = QLabel(top_bar)
        self.date_label.setFont(QFont("Microsoft YaHei", 9))
        self.date_label.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none;")
        self.date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.date_label.setGeometry(WIN_W - 145, 12, 125, 20)

        close_btn = QLabel("✕", top_bar)
        close_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        close_btn.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none; padding: 4px;")
        close_btn.setAlignment(Qt.AlignCenter)
        close_btn.setGeometry(WIN_W - 28, 6, 20, 20)
        close_btn.mousePressEvent = lambda e: self.close()

        self.scroll = QScrollArea(self.container)
        self.scroll.setGeometry(0, 44, WIN_W, WIN_H - 44)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ width: 4px; background: transparent; }}
            QScrollBar::handle:vertical {{ background: #e0d0d5; border-radius: 2px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(f"background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 8, 12, 12)
        self.content_layout.setSpacing(6)
        self.scroll.setWidget(self.content_widget)

        self.drag_pos = None
        self.container.mousePressEvent = self.mouse_press
        self.container.mouseMoveEvent = self.mouse_move
        top_bar.mousePressEvent = self.mouse_press
        top_bar.mouseMoveEvent = self.mouse_move

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)

    def mouse_press(self, event):
        self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouse_move(self, event):
        if self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def show_menu(self, pos):
        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{ background: #fff; border: 1px solid #f0d0d8; border-radius: 8px; padding: 4px; }}
            QMenu::item {{ padding: 6px 20px; color: {TEXT}; }}
            QMenu::item:selected {{ background: {PINK_LIGHT}; border-radius: 4px; }}
        """)
        refresh_action = QAction("🔄 立即刷新", self)
        refresh_action.triggered.connect(self.load_data)
        close_action = QAction("✕ 关闭", self)
        close_action.triggered.connect(self.close)
        menu.addAction(refresh_action)
        menu.addAction(close_action)
        menu.exec_(self.mapToGlobal(pos))

    def load_data(self):
        """在主线程加载数据"""
        try:
            resp = requests.get(SERVER_URL, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.memorials = data.get('memorials', [])
                self.save_cache()
        except Exception:
            self.load_cache()
        self.build_list()

    def load_cache(self):
        try:
            cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.json")
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.memorials = data.get('memorials', [])
        except:
            self.memorials = []

    def save_cache(self):
        try:
            cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({'memorials': self.memorials}, f, ensure_ascii=False)
        except:
            pass

    def build_list(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        today = datetime.now()
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        self.date_label.setText(f"{today.month}月{today.day}日 {weekdays[today.weekday()]}")

        if not self.memorials:
            empty = QLabel("📭 还没有纪念日\n去后台添加吧~")
            empty.setFont(QFont("Microsoft YaHei", 12))
            empty.setStyleSheet(f"color: {TEXT_DIM}; padding: 60px 0;")
            empty.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(empty)
            self.content_layout.addStretch()
            return

        infos = []
        for m in self.memorials:
            d = datetime.strptime(m['date'], '%Y-%m-%d')
            years_passed = today.year - d.year
            this_year = datetime(today.year, d.month, d.day)
            if today < this_year:
                years_passed -= 1
            next_date = datetime(today.year, d.month, d.day)
            if next_date <= today:
                next_date = datetime(today.year + 1, d.month, d.day)
            days_left = (next_date - today).days
            is_today = (today.month == d.month and today.day == d.day)
            infos.append({
                'm': m, 'years_passed': years_passed, 'days_left': days_left,
                'is_today': is_today, 'month': d.month, 'day': d.day
            })

        infos.sort(key=lambda x: x['days_left'])

        today_items = [i for i in infos if i['is_today']]
        if today_items:
            item = today_items[0]
            banner = QFrame()
            banner.setStyleSheet(f"""
                QFrame {{ background: {PINK_LIGHT}; border-radius: 14px; border: 1px solid {PINK}; }}
            """)
            banner.setFixedHeight(56)
            bl = QVBoxLayout(banner)
            bl.setAlignment(Qt.AlignCenter)
            bl.setSpacing(2)
            emoji_lbl = QLabel(item['m'].get('emoji', '💝'))
            emoji_lbl.setFont(QFont("Microsoft YaHei", 28))
            emoji_lbl.setAlignment(Qt.AlignCenter)
            bl.addWidget(emoji_lbl)
            msg = QLabel(f"🎉 今天！{item['m']['title']} {item['years_passed']}周年")
            msg.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
            msg.setStyleSheet(f"color: {PINK};")
            msg.setAlignment(Qt.AlignCenter)
            bl.addWidget(msg)
            self.content_layout.addWidget(banner)

        for item in infos[:8]:
            card = QFrame()
            card.setStyleSheet("""
                QFrame { background: #fff; border-radius: 12px; border: 1px solid #f5e0e5; }
                QFrame:hover { background: #fff5f7; }
            """)
            card.setFixedHeight(48)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(12, 4, 12, 4)
            card_layout.setSpacing(8)

            emoji = QLabel(item['m'].get('emoji', '💝'))
            emoji.setFont(QFont("Microsoft YaHei", 16))
            card_layout.addWidget(emoji)

            info_layout = QVBoxLayout()
            info_layout.setSpacing(1)
            name = QLabel(item['m']['title'])
            name.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
            name.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
            info_layout.addWidget(name)
            detail = QLabel(f"每年{item['month']}月{item['day']}日 · {item['years_passed']}周年")
            detail.setFont(QFont("Microsoft YaHei", 8))
            detail.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none;")
            info_layout.addWidget(detail)
            card_layout.addLayout(info_layout, 1)

            if item['is_today']:
                badge_text, badge_bg, badge_color = "今天", PINK, "#fff"
            elif item['days_left'] <= 30:
                badge_text, badge_bg, badge_color = f"{item['days_left']}天后", PINK_LIGHT, PINK
            else:
                badge_text, badge_bg, badge_color = f"{item['days_left']}天后", "#f5f5f5", TEXT_DIM

            badge = QLabel(badge_text)
            badge.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
            badge.setAlignment(Qt.AlignCenter)
            badge.setFixedSize(50, 24)
            badge.setStyleSheet(f"""
                QLabel {{
                    background: {badge_bg}; color: {badge_color};
                    border-radius: 12px; border: none;
                }}
            """)
            card_layout.addWidget(badge)
            self.content_layout.addWidget(card)

        footer = QLabel("纪念日 · 每一天都值得")
        footer.setFont(QFont("Microsoft YaHei", 9))
        footer.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none; padding: 8px 0;")
        footer.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(footer)
        self.content_layout.addStretch()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    widget = DeskWidget()
    widget.show()
    sys.exit(app.exec())
