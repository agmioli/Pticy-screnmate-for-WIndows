import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QSlider,
                               QSystemTrayIcon, QMenu)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPixmap, QAction, QIcon, QPainter
from PySide6.QtNetwork import QLocalServer, QLocalSocket


# ============================================================
#   УТИЛИТА ДЛЯ РАБОТЫ С РЕСУРСАМИ В EXE
# ============================================================
def resource_path(relative_path):
    """Возвращает абсолютный путь к ресурсу. Работает и для .py, и для .exe."""
    try:
        base_path = sys._MEIPASS  # Папка, куда PyInstaller распаковывает данные
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ============================================================
#   КЛАСС СКРИНМЕЙТА (АНИМИРОВАННЫЙ СПРАЙТ)
# ============================================================
class AnimatedSprite(QWidget):
    def __init__(self, image_paths, main_window):
        super().__init__()
        self.main_window = main_window

        # Окно без рамок, поверх всех окон, не отображается в панели задач
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.image_paths = image_paths
        self.current_frame = 0

        # Загружаем изображения
        self.pixmaps = [QPixmap(path) for path in image_paths]
        self.current_size = 100

        # Таймер для анимации (чередование кадров каждые 500 мс)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.timer.start(500)

        self.drag_position = QPoint()
        self.resize(self.current_size, self.current_size)

    def next_frame(self):
        self.current_frame = (self.current_frame + 1) % len(self.pixmaps)
        self.update()

    def set_sprite_size(self, size):
        self.current_size = size
        self.resize(size, size)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.pixmaps and not self.pixmaps[self.current_frame].isNull():
            pixmap = self.pixmaps[self.current_frame].scaled(
                self.current_size, self.current_size,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            x = (self.width() - pixmap.width()) // 2
            y = (self.height() - pixmap.height()) // 2
            painter.drawPixmap(x, y, pixmap)

    # --- Управление мышью (перетаскивание и контекстное меню) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def show_context_menu(self, pos):
        menu = QMenu(self)

        action_remove = QAction("Убрать", self)
        action_remove.triggered.connect(self.remove_sprite)

        action_props = QAction("Свойства", self)
        action_props.triggered.connect(self.main_window.bring_to_front)

        menu.addAction(action_remove)
        menu.addAction(action_props)
        menu.exec(pos)

    def remove_sprite(self):
        self.timer.stop()
        self.close()
        self.main_window.on_sprite_closed(self)


# ============================================================
#   ГЛАВНОЕ ОКНО ПРИЛОЖЕНИЯ
# ============================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Скринмейт Птички")
        self.resize(400, 600)

        self.ptica1 = None
        self.ptica2 = None

        # Иконка приложения
        self.app_icon = QIcon(resource_path("images/nawidget.png"))
        self.setWindowIcon(self.app_icon)

        self.init_ui()
        self.init_tray()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Блок 1: Красная птица ---
        layout1 = QHBoxLayout()
        icon1 = QLabel()
        icon1.setPixmap(QPixmap(resource_path("images/anim1.png")).scaled(
            40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.btn_ptica1 = QPushButton('Добавить "Красную птицу"')
        self.btn_ptica1.clicked.connect(self.toggle_ptica1)
        layout1.addWidget(icon1)
        layout1.addWidget(self.btn_ptica1)
        layout1.addStretch()
        main_layout.addLayout(layout1)

        slider_layout1 = QHBoxLayout()
        slider_layout1.addWidget(QLabel("Размер скринмейта:"))
        self.slider1 = QSlider(Qt.Horizontal)
        self.slider1.setRange(50, 300)
        self.slider1.setValue(100)
        self.slider1.valueChanged.connect(self.resize_ptica1)
        slider_layout1.addWidget(self.slider1)
        main_layout.addLayout(slider_layout1)

        main_layout.addSpacing(20)

        # --- Блок 2: Зеленая птица ---
        layout2 = QHBoxLayout()
        icon2 = QLabel()
        icon2.setPixmap(QPixmap(resource_path("images/personaz1.png")).scaled(
            40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.btn_ptica2 = QPushButton('Добавить "Зеленую птицу"')
        self.btn_ptica2.clicked.connect(self.toggle_ptica2)
        layout2.addWidget(icon2)
        layout2.addWidget(self.btn_ptica2)
        layout2.addStretch()
        main_layout.addLayout(layout2)

        slider_layout2 = QHBoxLayout()
        slider_layout2.addWidget(QLabel("Размер скринмейта:"))
        self.slider2 = QSlider(Qt.Horizontal)
        self.slider2.setRange(50, 300)
        self.slider2.setValue(100)
        self.slider2.valueChanged.connect(self.resize_ptica2)
        slider_layout2.addWidget(self.slider2)
        main_layout.addLayout(slider_layout2)

        main_layout.addStretch()

        # --- Футер ---
        footer_layout = QHBoxLayout()
        footer_icon = QLabel()
        footer_icon.setPixmap(QPixmap(resource_path("images/nawidget.png")).scaled(
            30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        footer_text = QLabel("Скринмейт Птички\nАвтор - Милан Агмиоли. 2026.")
        footer_layout.addWidget(footer_icon)
        footer_layout.addWidget(footer_text)
        footer_layout.addStretch()
        main_layout.addLayout(footer_layout)

        main_layout.addSpacing(10)

        # --- Нижние кнопки ---
        bottom_layout = QHBoxLayout()
        btn_minimize = QPushButton("Свернуть")
        btn_minimize.clicked.connect(self.minimize_to_tray)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close_app)
        bottom_layout.addWidget(btn_minimize)
        bottom_layout.addWidget(btn_close)
        main_layout.addLayout(bottom_layout)

    # --- Логика скринмейтов ---
    def toggle_ptica1(self):
        if self.ptica1 is None:
            self.ptica1 = AnimatedSprite(
                [resource_path("images/anim1.png"), resource_path("images/anim2.png")], self)
            self.ptica1.set_sprite_size(self.slider1.value())

            btn_pos = self.btn_ptica1.mapToGlobal(QPoint(0, 0))
            self.ptica1.move(btn_pos.x() + 250, btn_pos.y() + 50)

            self.ptica1.show()
            self.btn_ptica1.setText('Убрать "Красную птицу"')
        else:
            self.ptica1.remove_sprite()

    def resize_ptica1(self, value):
        if self.ptica1:
            self.ptica1.set_sprite_size(value)

    def toggle_ptica2(self):
        if self.ptica2 is None:
            self.ptica2 = AnimatedSprite(
                [resource_path("images/personaz1.png"), resource_path("images/personaz2.png")], self)
            self.ptica2.set_sprite_size(self.slider2.value())

            btn_pos = self.btn_ptica2.mapToGlobal(QPoint(0, 0))
            self.ptica2.move(btn_pos.x() + 250, btn_pos.y() + 50)

            self.ptica2.show()
            self.btn_ptica2.setText('Убрать "Зеленую птицу"')
        else:
            self.ptica2.remove_sprite()

    def resize_ptica2(self, value):
        if self.ptica2:
            self.ptica2.set_sprite_size(value)

    def on_sprite_closed(self, sprite):
        """Вызывается, когда скринмейт закрывается через контекстное меню."""
        if sprite == self.ptica1:
            self.ptica1 = None
            self.btn_ptica1.setText('Добавить "Красную птицу"')
        elif sprite == self.ptica2:
            self.ptica2 = None
            self.btn_ptica2.setText('Добавить "Зеленую птицу"')

    # --- Трей ---
    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.app_icon)

        tray_menu = QMenu()
        show_action = QAction("Открыть", self)
        show_action.triggered.connect(self.bring_to_front)
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self.close_app)

        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)

        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.show()

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick or reason == QSystemTrayIcon.Trigger:
            self.bring_to_front()

    def minimize_to_tray(self):
        self.hide()
        self.tray_icon.showMessage(
            "Скринмейт Птички",
            "Приложение свернуто в трей.",
            QSystemTrayIcon.Information,
            2000
        )

    def close_app(self):
        if self.ptica1:
            self.ptica1.close()
        if self.ptica2:
            self.ptica2.close()
        self.tray_icon.hide()
        QApplication.quit()

    # --- ФОРСИРОВАННЫЙ ВЫВОД ОКНА И ПТИЦ ПОВЕРХ ВСЕХ ---
    def bring_to_front(self):
        """Вытаскивает главное окно и всех птиц поверх остальных окон (Windows-safe)."""
        # 1. Разворачиваем главное окно, если оно свёрнуто или скрыто в трее
        if self.isMinimized():
            self.showNormal()
        if not self.isVisible():
            self.show()

        # 2. Форсированный вывод главного окна на передний план:
        #    временно ставим флаг "поверх всех окон" — Windows обязан это выполнить
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.show()          # переприменяем флаги
        self.raise_()
        self.activateWindow()

        # Через 250 мс снимаем флаг, чтобы окно вело себя как обычно
        QTimer.singleShot(250, self._drop_topmost)

        # 3. Поднимаем птиц (у них уже стоит флаг TopMost)
        for sprite in (self.ptica1, self.ptica2):
            if sprite:
                if not sprite.isVisible():
                    sprite.show()
                sprite.raise_()
                sprite.activateWindow()

        # 4. Ещё раз главное окно поверх птиц
        self.raise_()
        self.activateWindow()

    def _drop_topmost(self):
        """Снимает флаг 'поверх всех окон' с главного окна после форсированного поднятия."""
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show()  # переприменяем флаги


# ============================================================
#   ЗАЩИТА ОТ ПОВТОРНОГО ЗАПУСКА
# ============================================================
APP_KEY = "Skrinmeyt_Ptichki_SingleInstance_Key"


def notify_running_instance():
    """Если копия уже запущена — посылает ей сигнал и возвращает True."""
    socket = QLocalSocket()
    socket.connectToServer(APP_KEY)
    if socket.waitForConnected(500):
        socket.write(b"SHOW")
        socket.flush()
        socket.waitForBytesWritten(500)
        socket.disconnectFromServer()
        return True
    return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Приложение живёт в трее, поэтому не закрываемся при закрытии окон
    app.setQuitOnLastWindowClosed(False)

    # === ПРОВЕРКА НА ВТОРОЙ ЗАПУСК ===
    if notify_running_instance():
        # Копия уже работает — выходим, а она сама себя покажет
        sys.exit(0)

    # === СОЗДАЁМ ЛОКАЛЬНЫЙ СЕРВЕР ДЛЯ ПРИЁМА СИГНАЛОВ ===
    # Удаляем "зависший" сервер от предыдущей аварийной сессии
    QLocalServer.removeServer(APP_KEY)

    local_server = QLocalServer()

    window = MainWindow()

    def handle_new_instance():
        """Срабатывает, когда кто-то пытается запустить вторую копию."""
        connection = local_server.nextPendingConnection()
        if connection:
            connection.waitForReadyRead(500)
            connection.readAll()
            connection.disconnectFromServer()

        # Вытаскиваем всё поверх остальных окон
        window.bring_to_front()

    local_server.newConnection.connect(handle_new_instance)
    local_server.listen(APP_KEY)

    window.show()
    sys.exit(app.exec())