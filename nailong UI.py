# ================================================================
#  桌面宠物 — 情感互动桌面伙伴 (Desktop Pet)  —  PyQt6 版
#
#  功能：
#    1. 在桌面上自由移动，根据心情切换不同行为
#    2. 单击 / 双击 / 拖拽 / 右键菜单 交互
#    3. PNG/GIF 图片驱动外观，Canvas 绘制兜底
#    4. 心情和行为系统在 MOODS 字典中自由添加
#    5. QPropertyAnimation 平滑过渡，切换动作不突兀
#
#  运行方式：python "nailong UI.py"
#  依赖：PyQt6（pip install PyQt6）、tkinter 不再使用
# ================================================================

import sys
import math
import random
import os

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QMenu, QVBoxLayout,
)
from PyQt6.QtCore import (
    Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QRect,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QFont, QPixmap, QMovie,
    QCursor, QAction,
)

# ================================================================
#  🎨  心情定义区 — 在这添加/修改你的心情！
#  ================================================================
#
#  每添加一个新心情，只需在下面 MOODS 字典里加一项即可。
#  每种心情支持的字段：
#
#    name              显示名称（右键菜单中显示）
#    color             身体颜色 (#RRGGBB hex) — Canvas 兜底时使用
#    eye_style         眼睛样式: "normal" | "happy" | "closed" | "wide" | "angry"
#    mouth_style       嘴巴样式: "smile" | "neutral" | "open" | "frown" | "tongue"
#    default_behavior  默认行为: "idle" | "wander" | "follow" | "sleep" | "bounce"
#    speed             移动速度 (1=很慢, 5=中等, 10=很快)
#    auto_switch_to    多少秒后自动切换到指定心情 (None = 不自动切换)
#    auto_switch_after 自动切换的秒数
#    on_click          被点击后的反应行为
#    on_double_click   被双击后切换到哪个心情
#    particles         粒子特效: True / False
#  ================================================================

MOODS = {
    # ── 开心 ─────────────────────────────────────────────────
    "happy": {
        "name": "😊 开心",
        "color": "#FFB347",
        "eye_style": "happy",
        "mouth_style": "smile",
        "default_behavior": "wander",
        "speed": 2,
        "auto_switch_to": None,
        "auto_switch_after": 0,
        "on_click": "bounce",
        "on_double_click": "excited",
        "particles": True,
    },
    # ── 无聊 ─────────────────────────────────────────────────
    "bored": {
        "name": "😐 无聊",
        "color": "#B0B0B0",
        "eye_style": "normal",
        "mouth_style": "neutral",
        "default_behavior": "wander",
        "speed": 1,
        "auto_switch_to": "sleepy",
        "auto_switch_after": 60,
        "on_click": "bounce",
        "on_double_click": "happy",
        "particles": False,
    },
    # ── 困了 ─────────────────────────────────────────────────
    "sleepy": {
        "name": "😴 困了",
        "color": "#A0C4E8",
        "eye_style": "closed",
        "mouth_style": "open",
        "default_behavior": "sleep",
        "speed": 0,
        "auto_switch_to": "happy",
        "auto_switch_after": 30,
        "on_click": "idle",
        "on_double_click": "happy",
        "particles": False,
    },
    # ── 兴奋 ─────────────────────────────────────────────────
    "excited": {
        "name": "🤩 兴奋",
        "color": "#FF6B6B",
        "eye_style": "wide",
        "mouth_style": "tongue",
        "default_behavior": "bounce",
        "speed": 5,
        "auto_switch_to": "happy",
        "auto_switch_after": 10,
        "on_click": "spin",
        "on_double_click": "happy",
        "particles": True,
    },
    # ── 生气 ─────────────────────────────────────────────────
    "angry": {
        "name": "😡 生气",
        "color": "#C0392B",
        "eye_style": "angry",
        "mouth_style": "frown",
        "default_behavior": "flee",
        "speed": 4,
        "auto_switch_to": "bored",
        "auto_switch_after": 15,
        "on_click": "bounce",
        "on_double_click": "happy",
        "particles": False,
    },
}

DEFAULT_MOOD = "happy"

# ================================================================
#  🖼️  精灵图注册表 — 在这关联你做的 GIF/PNG 图片
#  ================================================================
#  格式：
#  SPRITE_MAP = {
#      "happy": {
#          "idle":   "sprites/happy_idle.gif",
#          "walk":   "sprites/happy_walk.gif",
#          "bounce": "sprites/happy_bounce.gif",
#          "sleep":  "sprites/happy_sleep.gif",
#      },
#      "angry": { ... },
#  }
#
#  不填（留空）则使用内置 Canvas 绘制角色
#  ================================================================

SPRITE_MAP = {}

# 精灵目录
try:
    SPRITE_DIR = os.path.join(os.path.dirname(__file__), "sprites")
except NameError:
    SPRITE_DIR = os.path.join(os.getcwd(), "sprites")
# ================================================================
#  BehaviorEngine — 屏幕位置计算 
# ================================================================

class BehaviorEngine:
    """计算宠物窗口在屏幕上的位置"""

    def __init__(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.screen_w = screen.width()
        self.screen_h = screen.height()
        self.x = self.screen_w // 2 - 125
        self.y = self.screen_h // 2 - 125
        self.target_x = self.x
        self.target_y = self.y
        self._anim_t = 0.0
        self._idle_timer = 0
        self._idle_duration = random.randint(60, 150)
        self._drag_offset_x = 0
        self._drag_offset_y = 0

        # 动画偏移量（暴露给外部用于绘制浮动/弹跳）
        self.bob_offset = 0
        self.bounce_y = 0
        self.scale = 1.0
        self.shake_x = 0

    def update(self, behavior: str, speed: int,
               mouse_x: int, mouse_y: int,
               win_x: int, win_y: int) -> tuple:
        """每帧调用，返回 (new_x, new_y)"""
        self._anim_t += 1
        t = self._anim_t

        # 重置动画参数
        self.bob_offset = 0
        self.bounce_y = 0
        self.scale = 1.0
        self.shake_x = 0

        if behavior == "idle":
            self.bob_offset = int(math.sin(t * 3) * 5)
            self._idle_timer += 1
            if self._idle_timer > self._idle_duration:
                self._idle_timer = 0
                self._idle_duration = random.randint(60, 150)

        elif behavior == "wander":
            self.bob_offset = int(math.sin(t * 3) * 5)
            dist = math.hypot(self.target_x - self.x, self.target_y - self.y)
            if dist < 10:
                angle = random.uniform(0, math.pi * 2)
                radius = random.randint(80, 300)
                self.target_x = self.x + math.cos(angle) * radius
                self.target_y = self.y + math.sin(angle) * radius
                self.target_x = max(50, min(self.screen_w - 300, self.target_x))
                self.target_y = max(50, min(self.screen_h - 300, self.target_y))
            else:
                self.x += (self.target_x - self.x) * 0.02 * speed
                self.y += (self.target_y - self.y) * 0.02 * speed

        elif behavior == "follow":
            self.bob_offset = int(math.sin(t * 3) * 5)
            tx = mouse_x - 125
            ty = mouse_y - 125
            dist = math.hypot(tx - self.x, ty - self.y)
            if dist > 60:
                self.x += (tx - self.x) * 0.03 * speed
                self.y += (ty - self.y) * 0.03 * speed

        elif behavior == "flee":
            self.bob_offset = int(math.sin(t * 6) * 3)
            self.shake_x = int(math.sin(t * 20) * 2)
            dx = self.x + 125 - mouse_x
            dy = self.y + 125 - mouse_y
            dist = max(1, math.hypot(dx, dy))
            flee_speed = max(2, 400 / dist) * speed
            self.x += (dx / dist) * flee_speed
            self.y += (dy / dist) * flee_speed

        elif behavior == "sleep":
            self.scale = 1.0 + math.sin(t * 0.8) * 0.05

        elif behavior == "bounce":
            bt = (t * 5) % 1.0
            self.bounce_y = -int(math.sin(bt * math.pi) * 40)
            self.scale = 1.0 + bt * 0.3 if bt < 0.5 else 1.3 - bt * 0.3

        elif behavior == "spin":
            self.scale = 1.0  # 旋转效果由 PetWindow 的 QPropertyAnimation 处理

        # 边界约束
        margin = 50
        self.x = max(margin - 250, min(self.screen_w - margin, self.x))
        self.y = max(margin - 250, min(self.screen_h - margin, self.y))

        return (self.x, self.y)

    def move_to(self, x: int, y: int):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y

    def window_size(self) -> int:
        return 250


# ================================================================
#  PetWindow — PyQt6 透明悬浮窗
# ================================================================

class PetWindow(QWidget):
    """桌面宠物主窗口"""

    WINDOW_SIZE = 250
    BASE_SIZE = 120

    def __init__(self):
        super().__init__()

        # ── 窗口属性 ──────────────────────────────────────────
        self.setWindowTitle("Desktop Pet")
        self.setFixedSize(self.WINDOW_SIZE, self.WINDOW_SIZE)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        # ── 初始化组件 ────────────────────────────────────────
        self.engine = BehaviorEngine()
        self._use_sprite = False
        self._sprite_cache = {}

        # ── 状态 ──────────────────────────────────────────────
        self.current_mood = DEFAULT_MOOD
        self.current_behavior = MOODS[DEFAULT_MOOD]["default_behavior"]
        self._anim_frame = 0
        self._mood_timer = 0
        self._dragging = False
        self._drag_offset = QPoint(0, 0)
        self._mouse_global = QPoint(0, 0)
        self._reaction_timer_id = None

        # ── QLabel（GIF 显示层） ──────────────────────────────
        self.sprite_label = QLabel(self)
        self.sprite_label.setFixedSize(self.WINDOW_SIZE, self.WINDOW_SIZE)
        self.sprite_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.sprite_label.hide()
        self._current_movie = None

        # ── 过渡动画 ──────────────────────────────────────────
        self._trans_anim = QPropertyAnimation(self.sprite_label, b"geometry")
        self._trans_anim.setDuration(150)
        self._trans_anim.setEasingCurve(QEasingCurve.Type.OutBack)

        # 初始位置
        self.move(self.engine.x, self.engine.y)

        # ── 右键菜单 ──────────────────────────────────────────
        self._build_menu()

        # ── 鼠标追踪 ──────────────────────────────────────────
        self.setMouseTracking(True)

        # ── 加载精灵图 ────────────────────────────────────────
        self._load_sprites()

        # ── 主循环定时器 30fps ────────────────────────────────
        self._ticker = QTimer(self)
        self._ticker.timeout.connect(self._tick)
        self._ticker.start(33)

    # ── 精灵图加载 ────────────────────────────────────────────

    def _load_sprites(self):
        """预加载 SPRITE_MAP 中的图片"""
        if not SPRITE_MAP:
            self._use_sprite = False
            return
        for mood_key, actions in SPRITE_MAP.items():
            self._sprite_cache[mood_key] = {}
            for action, filename in actions.items():
                path = os.path.join(SPRITE_DIR, filename)
                if not os.path.exists(path):
                    # 也尝试相对于当前目录
                    path = os.path.join(os.path.dirname(__file__),
                                        SPRITE_DIR, filename)
                if os.path.exists(path):
                    if path.lower().endswith('.gif'):
                        self._sprite_cache[mood_key][action] = ('gif', path)
                    else:
                        self._sprite_cache[mood_key][action] = ('png', path)
        self._use_sprite = bool(self._sprite_cache)

    def _get_sprite(self, mood: str, behavior: str) -> tuple | None:
        """获取指定心情+行为的精灵图，返回 (type, path) 或 None"""
        mood_sprites = self._sprite_cache.get(mood, {})
        # 先精确匹配，再回退到该心情的 idle
        for key in (behavior, "idle"):
            if key in mood_sprites:
                return mood_sprites[key]
        return None

    def _show_sprite(self, mood: str, behavior: str):
        """显示精灵图（GIF 或 PNG）"""
        sprite = self._get_sprite(mood, behavior)
        if sprite is None:
            self.sprite_label.hide()
            if self._current_movie:
                self._current_movie.stop()
                self._current_movie = None
            return

        stype, path = sprite

        if stype == 'gif':
            if self._current_movie:
                self._current_movie.stop()
            self._current_movie = QMovie(path)
            self._current_movie.setScaledSize(
                self.sprite_label.size())
            self.sprite_label.setMovie(self._current_movie)
            self._current_movie.start()
        else:
            if self._current_movie:
                self._current_movie.stop()
                self._current_movie = None
            pm = QPixmap(path)
            self.sprite_label.setPixmap(
                pm.scaled(self.WINDOW_SIZE, self.WINDOW_SIZE,
                          Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation))
        self.sprite_label.show()

    # ── 流畅过渡 ──────────────────────────────────────────────

    def _transition_sprite(self, mood: str, behavior: str):
        """带缩放过渡的精灵切换"""
        if not self._use_sprite or not self.sprite_label.isVisible():
            self._show_sprite(mood, behavior)
            return

        center = self.WINDOW_SIZE // 2
        small_rect = QRect(center - 10, center - 10, 20, 20)
        full_rect = QRect(0, 0, self.WINDOW_SIZE, self.WINDOW_SIZE)

        def _on_shrink():
            self._show_sprite(mood, behavior)
            self._trans_anim.stop()
            self._trans_anim.setStartValue(small_rect)
            self._trans_anim.setEndValue(full_rect)
            self._trans_anim.start()

        self._trans_anim.stop()
        self._trans_anim.setStartValue(full_rect)
        self._trans_anim.setEndValue(small_rect)
        try:
            self._trans_anim.finished.disconnect()
        except TypeError:
            pass
        self._trans_anim.finished.connect(_on_shrink)
        self._trans_anim.start()

    # ── 右键菜单 ──────────────────────────────────────────────

    def _build_menu(self):
        self._menu = QMenu(self)
        # 心情子菜单
        mood_menu = self._menu.addMenu("切换心情")
        for mood_key, mood_data in MOODS.items():
            action = QAction(mood_data["name"], self)
            action.triggered.connect(
                lambda checked, k=mood_key: self.switch_mood(k))
            mood_menu.addAction(action)
        self._menu.addSeparator()
        self._menu.addAction("隐藏", self.hide)
        self._menu.addAction("显示", self.show)
        self._menu.addSeparator()
        self._menu.addAction("退出", self._quit)

    # ── 事件处理 ──────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.pos()
        elif event.button() == Qt.MouseButton.RightButton:
            self._menu.exec(QCursor.pos())

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            target = MOODS[self.current_mood].get("on_double_click")
            if target and target in MOODS:
                self.switch_mood(target)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            if self._drag_offset.manhattanLength() < 5:
                # 微小移动 = 单击
                reaction = MOODS[self.current_mood].get("on_click", "bounce")
                if reaction in ("idle", "wander", "follow", "flee",
                                "sleep", "bounce", "spin"):
                    self.current_behavior = reaction
                    self._transition_sprite(self.current_mood, reaction)
                    # 1.5秒后恢复
                    if self._reaction_timer_id:
                        self.killTimer(self._reaction_timer_id)
                    self._reaction_timer_id = self.startTimer(1500)

    def mouseMoveEvent(self, event):
        self._mouse_global = event.globalPosition().toPoint()
        if self._dragging:
            delta = event.pos() - self._drag_offset
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()
            self.move(new_x, new_y)
            self.engine.move_to(new_x, new_y)

    def timerEvent(self, event):
        """点击反应计时器到期 → 恢复默认行为"""
        if event.timerId() == self._reaction_timer_id:
            default_bh = MOODS[self.current_mood]["default_behavior"]
            if self.current_behavior != default_bh:
                self.current_behavior = default_bh
                self._transition_sprite(self.current_mood, default_bh)
            self.killTimer(self._reaction_timer_id)
            self._reaction_timer_id = None

    # ── 心情切换 ──────────────────────────────────────────────

    def switch_mood(self, mood_key: str):
        if mood_key not in MOODS:
            return
        old_mood = self.current_mood
        self.current_mood = mood_key
        self.current_behavior = MOODS[mood_key]["default_behavior"]
        self._mood_timer = 0
        self._anim_frame = 0
        self._transition_sprite(mood_key, self.current_behavior)

    # ── 绘制（无精灵图时的兜底） ──────────────────────────────

    def paintEvent(self, event):
        if self._use_sprite and self.sprite_label.isVisible():
            return  # 用精灵图时不画 Canvas
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        mood_data = MOODS[self.current_mood]
        color = QColor(mood_data["color"])
        eye = mood_data["eye_style"]
        mouth = mood_data["mouth_style"]
        show_particles = mood_data.get("particles", False)

        cx, cy = self.WINDOW_SIZE // 2, self.WINDOW_SIZE // 2
        s = self.engine.scale
        bx = self.engine.bob_offset + self.engine.shake_x
        by = self.engine.bounce_y
        bw, bh = int(self.painter.BASE_SIZE * s), int(self.painter.BASE_SIZE * 0.8 * s)
        body_x = cx - bw // 2 + bx
        body_y = cy - bh // 2 + by + 15

        # ── 身体 ──────────────────────────────────────────────
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(body_x, body_y, bw, bh)

        # ── 耳朵 ──────────────────────────────────────────────
        ear_w, ear_h = int(30 * s), int(35 * s)
        painter.drawPolygon(
            QPoint(body_x + 10, body_y + bh - int(60 * s)),
            QPoint(body_x + 5, body_y - 10),
            QPoint(body_x + ear_w + 5, body_y + 5),
        )
        painter.drawPolygon(
            QPoint(body_x + bw - 10, body_y + bh - int(60 * s)),
            QPoint(body_x + bw - 5, body_y - 10),
            QPoint(body_x + bw - ear_w - 5, body_y + 5),
        )

        # ── 腮红 ──────────────────────────────────────────────
        if self.current_mood in ("happy", "excited"):
            blush_r = int(12 * s)
            blush_c = QColor("#FF9999") if self.current_mood == "happy" else QColor("#FF6666")
            painter.setBrush(QBrush(blush_c))
            painter.drawEllipse(
                body_x + int(12 * s), body_y + int(45 * s), blush_r * 2, blush_r * 2)
            painter.drawEllipse(
                body_x + bw - int(12 * s) - blush_r * 2, body_y + int(45 * s),
                blush_r * 2, blush_r * 2)

        # ── 眼睛 ──────────────────────────────────────────────
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.setPen(QPen(QColor("#222"), 1))
        eye_spacing = int(22 * s)
        eye_cy = body_y + int(30 * s)
        self._draw_eyes(painter, eye, cx + bx, eye_cy, eye_spacing, s)

        # ── 嘴巴 ──────────────────────────────────────────────
        mouth_y = body_y + int(52 * s)
        self._draw_mouth(painter, mouth, cx + bx, mouth_y, s)

        painter.end()

    # ── 眼睛绘制 ──────────────────────────────────────────────

    def _draw_eyes(self, p: QPainter, style: str, ecx: int, ey: int,
                   spacing: int, s: float):
        r = int(8 * s)
        lx, rx = ecx - spacing, ecx + spacing
        pen = QPen(QColor("#222"), 2)

        if style == "normal":
            for x in (lx, rx):
                p.setBrush(QBrush(Qt.GlobalColor.white))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPoint(x, ey), r, r)
                p.setBrush(QBrush(QColor("#222")))
                p.drawEllipse(QPoint(x, ey), r // 2, r // 2)
        elif style == "happy":
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(lx - r, ey, r * 2, r * 2, 0, -180 * 16)
            p.drawArc(rx - r, ey, r * 2, r * 2, 0, -180 * 16)
        elif style == "closed":
            p.setPen(pen)
            for x in (lx, rx):
                p.drawLine(x - r, ey, x + r, ey)
        elif style == "wide":
            big_r = int(12 * s)
            for x in (lx, rx):
                p.setBrush(QBrush(Qt.GlobalColor.white))
                p.setPen(QPen(QColor("#222"), 2))
                p.drawEllipse(QPoint(x, ey), big_r, big_r)
                p.setBrush(QBrush(QColor("#222")))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPoint(x, ey), int(4 * s), int(4 * s))
        elif style == "angry":
            for x in (lx, rx):
                p.setBrush(QBrush(Qt.GlobalColor.white))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPoint(x, ey), r, r)
                p.setBrush(QBrush(QColor("#C0392B")))
                p.drawEllipse(QPoint(x, ey), r // 2, r // 2)
                p.setPen(QPen(QColor("#222"), 3))
                p.drawLine(x - r - 5, ey - r - 3, x + r + 5, ey - r + 4)

    # ── 嘴巴绘制 ──────────────────────────────────────────────

    def _draw_mouth(self, p: QPainter, style: str, cx: int, my: int, s: float):
        mw = int(18 * s)
        pen = QPen(QColor("#222"), 3)

        if style == "smile":
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(cx - mw, my - int(10 * s), mw * 2, int(20 * s), 0, -180 * 16)
        elif style == "neutral":
            p.setPen(QPen(QColor("#666"), 2))
            p.drawLine(cx - mw, my, cx + mw, my)
        elif style == "open":
            p.setBrush(QBrush(QColor("#C0392B")))
            p.setPen(QPen(QColor("#222"), 1))
            p.drawEllipse(QPoint(cx, my + int(2 * s)), mw // 2, int(8 * s))
        elif style == "frown":
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(cx - mw, my, mw * 2, int(15 * s), 0, 180 * 16)
        elif style == "tongue":
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(cx - mw, my - int(8 * s), mw * 2, int(10 * s), 0, -180 * 16)
            p.setBrush(QBrush(QColor("#FF6B8A")))
            p.setPen(QPen(QColor("#222"), 1))
            p.drawEllipse(QPoint(cx, my + int(4 * s)), int(6 * s), int(10 * s))

    # ── 主循环 ────────────────────────────────────────────────

    def _tick(self):
        mood_data = MOODS[self.current_mood]
        speed = mood_data["speed"]
        behavior = self.current_behavior

        # ── 鼠标追踪 ──────────────────────────────────────────
        self._mouse_global = QCursor.pos()

        # ── 行为引擎 ──────────────────────────────────────────
        new_x, new_y = self.engine.update(
            behavior, speed,
            self._mouse_global.x(), self._mouse_global.y(),
            self.x(), self.y(),
        )
        if not self._dragging:
            self.move(int(new_x), int(new_y))

        # ── 精灵图更新 ────────────────────────────────────────
        if self._use_sprite:
            sprite = self._get_sprite(self.current_mood, behavior)
            if sprite:
                if not self.sprite_label.isVisible():
                    self._show_sprite(self.current_mood, behavior)
                # 对于弹跳/浮动效果，移动 QLabel 在窗口内的位置
                sx = (self.engine.bob_offset + self.engine.shake_x)
                sy = self.engine.bounce_y
                sz = self.engine.scale
                self.sprite_label.move(int(sx), int(sy))
                # 缩放由 QPropertyAnimation 处理，引擎层不做持续缩放避免抖动

        # ── 重绘 ──────────────────────────────────────────────
        self._anim_frame += 1
        self.update()

        # ── 自动切换心情 ──────────────────────────────────────
        auto_to = mood_data.get("auto_switch_to")
        auto_after = mood_data.get("auto_switch_after", 0)
        if auto_to and auto_after > 0:
            self._mood_timer += 1
            if self._mood_timer > auto_after * 30:
                self.switch_mood(auto_to)

    # ── 退出 ──────────────────────────────────────────────────

    def _quit(self):
        if self._reaction_timer_id:
            self.killTimer(self._reaction_timer_id)
        self._ticker.stop()
        self.close()
        QApplication.quit()


# ================================================================
#  Main
# ================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  桌面宠物 (PyQt6) - 启动中...")
    print("=" * 50)
    print()
    print("  右键宠物 -> 切换心情")
    print("  单击     -> 互动反应")
    print("  双击     -> 切换心情")
    print("  拖拽     -> 移动宠物")
    print()
    print("  SPRITE_MAP 中关联你的 GIF -> 自动切换为你的角色")
    print("  没有 GIF -> 用 Canvas 绘制猫型角色兜底")
    print("=" * 50)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    pet = PetWindow()
    pet.show()

    sys.exit(app.exec())
