import os
import sys
import sounddevice as sd
import vosk
import queue
import json
import pyautogui
from pycaw.pycaw import AudioUtilities
from comtypes import CLSCTX_ALL
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QComboBox, QHBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QTimer
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QSettings  # Добавлен импорт

def get_audio_processes():
    """Возвращает список активных процессов, воспроизводящих звук."""
    sessions = AudioUtilities.GetAllSessions()
    processes = set()
    for session in sessions:
        if session.Process:
            processes.add(session.Process.name())
    return list(processes)

def get_volume_control_for_process(process_name):
    """Возвращает объект громкости для указанного процесса."""
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process and session.Process.name().lower() == process_name.lower():
            return session.SimpleAudioVolume
    return None

class VoiceAssistant(QThread):
    recognized_signal = pyqtSignal(str)

    def __init__(self, device_index=None, target_process=None):
        super().__init__()
        self.running = False
        vosk.SetLogLevel(-1)
        # Путь к модели Vosk
        if getattr(sys, 'frozen', False):
            model_path = os.path.join(sys._MEIPASS, "vosk-model-small-ru-0.22")
        else:
            model_path = "vosk-model-small-ru-0.22"

        self.model = vosk.Model(model_path)
        self.q = queue.Queue()
        self.device_index = device_index
        self.target_process = target_process

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(f"Audio Status: {status}")
        self.q.put(bytes(indata))

    def run(self):
        try:
            self.running = True
            device_info = sd.query_devices(self.device_index)
            channels = min(1, device_info['max_input_channels'])
            if channels < 1:
                raise ValueError(f"Устройство {self.device_index} не поддерживает входные каналы")
                
            with sd.RawInputStream(samplerate=16000, blocksize=1024, dtype='int16', 
                                   channels=channels, callback=self.audio_callback, 
                                   device=self.device_index):
                rec = vosk.KaldiRecognizer(self.model, 16000)
                activator_words = ["помощник", "ассистент", "бот"]
                print("Слушаю команды...")
                while self.running:
                    data = self.q.get()
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        command = result.get("text", "").lower()
                        if any(word in command for word in activator_words):
                            command = command.split(max(activator_words, key=command.find), 1)[-1].strip()
                            if command:
                                self.process_commands(command)
        except Exception as e:
            print(f"Ошибка работы голосового ассистента: {e}")

    def process_commands(self, command):
        command_words = {
            "запуск": ["запуск", "воспроизвести", "включить", "продолжить"],
            "стоп": ["пауза", "стоп", "остановить", "прекратить"],
            "следующий": ["следующий", "вперёд", "дальше", "новый"],
            "предыдущий": ["предыдущий", "назад", "обратно", "раньше"],
            "громче": ["громче", "увеличь громкость", "прибавь звук"],
            "тише": ["тише", "уменьши громкость", "убавь звук"]
        }
        
        if any(word in command for word in command_words["стоп"]):
            self.play_pause()
        elif any(word in command for word in command_words["следующий"]):
            self.next_track()
        elif any(word in command for word in command_words["предыдущий"]):
            self.prev_track()
        elif any(word in command for word in command_words["запуск"]):
            self.play_pause()
        elif any(word in command for word in command_words["громче"]):
            self.change_volume(0.1)
        elif any(word in command for word in command_words["тише"]):
            self.change_volume(-0.1)
        elif "громкость" in command:
            self.set_volume_from_command(command)
        else:
            print(f"Неизвестная команда: {command}")

    def set_volume_from_command(self, command):
        words = command.split()
        for word in words:
            if word.isdigit():
                volume_level = int(word)
                if 0 <= volume_level <= 100:
                    volume_control = get_volume_control_for_process(self.target_process)
                    if volume_control:
                        volume_control.SetMasterVolume(volume_level / 100, None)
                        print(f"Громкость {self.target_process} установлена на {volume_level}%")
                break

    def change_volume(self, step):
        volume_control = get_volume_control_for_process(self.target_process)
        if volume_control:
            current_volume = volume_control.GetMasterVolume()
            new_volume = max(0, min(1, current_volume + step))
            volume_control.SetMasterVolume(new_volume, None)
            print(f"Громкость {self.target_process} изменена на {int(new_volume * 100)}%")
        else:
            print(f"Не найден процесс {self.target_process}")

    def stop(self):
        self.running = False
        self.wait()

    def play_pause(self):
        pyautogui.press('playpause')

    def next_track(self):
        pyautogui.press('nexttrack')

    def prev_track(self):
        pyautogui.press('prevtrack')

class VoiceAssistantApp(QWidget):
    def __init__(self):
        super().__init__()
        self.drag_position = None
        self.voice_assistant = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("VoiseAsistent")
        self.resize(400, 350)
        self.setWindowFlag(Qt.FramelessWindowHint)  # Убираем стандартный заголовок
        self.setAttribute(Qt.WA_TranslucentBackground)  # Прозрачный фон для эффектов
        self.setWindowIcon(QIcon("resources/icon.png"))  # Установка иконки

        # Основной макет
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Кастомный заголовок
        self.create_title_bar()
        main_layout.addWidget(self.title_bar)

        # Основные элементы
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(30, 20, 30, 20)

        self.status_label = QLabel("Ожидание...")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        self.device_selector = self.create_styled_combobox()
        self.player_selector = self.create_styled_combobox()
        self.toggle_button = QPushButton("▶ Запустить")
        self.toggle_button.setObjectName("toggle_button")
        self.toggle_button.clicked.connect(self.toggle_assistant)

        content_layout.addWidget(QLabel("🎤 Микрофон:"))
        content_layout.addWidget(self.device_selector)
        content_layout.addWidget(QLabel("🎵 Проигрыватель:"))
        content_layout.addWidget(self.player_selector)
        content_layout.addWidget(self.status_label)
        content_layout.addWidget(self.toggle_button)
        
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)
        self.setLayout(main_layout)

        # Загрузка сохраненных настроек
        self.load_settings()

        # Обновляем список проигрывателей
        self.update_player_list()

        # Применение стилей
        self.setStyleSheet(self.get_stylesheet())

    def closeEvent(self, event):
        """Сохранение настроек при закрытии"""
        self.save_settings()
        super().closeEvent(event)

    def load_settings(self):
        """Загрузка сохраненных настроек"""
        settings = QSettings("MyCompany", "VoiceAssistant")
        
        # Загрузка микрофона
        saved_device = settings.value("device_name", "")
        if saved_device:
            index = self.device_selector.findText(saved_device)
            if index >= 0:
                self.device_selector.setCurrentIndex(index)
        
        # Загрузка проигрывателя
        saved_player = settings.value("player_name", "")
        if saved_player:
            index = self.player_selector.findText(saved_player)
            if index >= 0:
                self.player_selector.setCurrentIndex(index)

    def save_settings(self):
        """Сохранение текущих настроек"""
        settings = QSettings("MyCompany", "VoiceAssistant")
        settings.setValue("device_name", self.device_selector.currentText())
        settings.setValue("player_name", self.player_selector.currentText())

    def create_title_bar(self):
        """Создает кастомный заголовок окна"""
        self.title_bar = QWidget()
        self.title_bar.setObjectName("title_bar")
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 0, 0, 0)
        title_layout.setSpacing(0)

        # Иконка приложения
        self.icon_label = QLabel()
        self.icon_label.setPixmap(QPixmap("resources/icon.png").scaled(24, 24))
        title_layout.addWidget(self.icon_label)

        # Название приложения
        self.title_label = QLabel("VoiseAsistent")
        self.title_label.setObjectName("title_label")
        title_layout.addWidget(self.title_label)

        # Растяжка для правого выравнивания кнопок
        title_layout.addStretch()

        # Кнопки управления
        self.btn_minimize = QPushButton("—")
        self.btn_minimize.setObjectName("title_button")
        self.btn_minimize.setFixedSize(30, 30)
        
        self.btn_close = QPushButton("×")
        self.btn_close.setObjectName("title_button_close")
        self.btn_close.setFixedSize(30, 30)

        for btn in [self.btn_minimize, self.btn_close]:
            title_layout.addWidget(btn)

        self.title_bar.setLayout(title_layout)

        # Подключение сигналов кнопок заголовка
        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_close.clicked.connect(self.close)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def create_styled_combobox(self):
        combobox = QComboBox()
        combobox.setCursor(Qt.PointingHandCursor)
        combobox.setMinimumHeight(30)
        combobox.setEditable(False)
        combobox.setStyleSheet("""
            QComboBox {
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 5px 10px;
                background-color: rgba(255, 255, 255, 0.05);
                color: #ffffff;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
                width: 30px;
            }
            QComboBox::down-arrow {
                text-align: right;
                padding-right: 5px;
                font-size: 16px;
                color: #9b59b6;
            }
            QComboBox QAbstractItemView {
                outline: 0px;
                background-color: rgba(30, 30, 47, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                selection-background-color: rgba(142, 68, 173, 0.8);
                padding: 5px;
            }
        """)
        return combobox

    def get_microphone_list(self):
        """Получает список доступных микрофонов."""
        try:
            devices = sd.query_devices()
            return [device["name"] for device in devices if device["max_input_channels"] > 0]
        except Exception as e:
            print(f"Ошибка получения списка микрофонов: {e}")
            return ["Нет доступных микрофонов"]

    def update_player_list(self):
        """Обновляет список активных плееров."""
        self.player_selector.clear()
        self.player_selector.addItems(get_audio_processes())

    def toggle_assistant(self):
        """Переключает состояние ассистента между запущенным и остановленным"""
        if not self.voice_assistant or not self.voice_assistant.isRunning():
            self.start_assistant()
        else:
            self.stop_assistant()

    def start_assistant(self):
        """Запускает голосового ассистента с выбранными настройками."""
        if self.voice_assistant and self.voice_assistant.isRunning():
            return
            
        self.update_player_list()  # Обновляем список проигрывателей перед запуском
        
        device_index = self.device_selector.currentIndex()
        target_process = self.player_selector.currentText()

        self.voice_assistant = VoiceAssistant(device_index, target_process)
        self.voice_assistant.recognized_signal.connect(self.update_status)
        
        self.status_label.setText("Слушаю...")
        self.update_toggle_button_state(True)
        self.voice_assistant.start()

    def stop_assistant(self):
        """Останавливает ассистента."""
        if self.voice_assistant:
            self.voice_assistant.stop()
            self.voice_assistant = None
            self.status_label.setText("Остановлено")
            self.update_toggle_button_state(False)

    def update_toggle_button_state(self, is_running):
        """Обновляет состояние кнопки переключения"""
        if is_running:
            self.toggle_button.setText("■ Остановить")
            self.toggle_button.setStyleSheet("""
                QPushButton#toggle_button {
                    background-color: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #e74c3c, stop:1 #c0392b
                    );
                }
                QPushButton#toggle_button:hover {
                    background-color: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ff5a45, stop:1 #d64534
                    );
                }
            """)
        else:
            self.toggle_button.setText("▶ Запустить")
            self.toggle_button.setStyleSheet("""
                QPushButton#toggle_button {
                    background-color: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #9b59b6, stop:1 #8e44ad
                    );
                }
                QPushButton#toggle_button:hover {
                    background-color: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #a95bc4, stop:1 #974eb9
                    );
                }
            """)

    def update_status(self, text):
        """Обновляет статус с анимацией"""
        self.status_label.setText(text)
        self.status_label.setStyleSheet("""
            background-color: rgba(142, 68, 173, 0.2);
            border: 1px solid rgba(142, 68, 173, 0.3);
            border-radius: 10px;
            padding: 15px;
            font-size: 16px;
            text-align: center;
            margin: 10px 0;
        """)
        QTimer.singleShot(1500, lambda: self.status_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            font-size: 16px;
            text-align: center;
            margin: 10px 0;
        """))

    def get_stylesheet(self):
        """Возвращает стили для приложения"""
        return """
        QWidget {
            background-color: #12121D;
            font-family: 'Segoe UI', sans-serif;
            color: #ffffff;
        }
        
        /* Стили для кастомного заголовка */
        #title_bar {
            background-color: #12121D;
            height: 40px;
        }
        
        #title_label {
            padding-left: 10px;
            font-size: 16px;
            font-weight: bold;
            color: white;
        }
        
        #title_button {
            background-color: transparent;
            border: none;
            color: white;
            font-size: 16px;
        }
        
        #title_button:hover {
            background-color: #9b59b6;
        }
        
        #title_button:pressed {
            background-color: #7d3c98;
        }
        
        #title_button_close {
            background-color: transparent;
            border: none;
            color: white;
            font-size: 16px;
        }
        
        #title_button_close:hover {
            background-color: #e74c3c;
        }
        
        #title_button_close:pressed {
            background-color: #c0392b;
        }
        
        QLabel {
            color: #c0c0c0;
            font-size: 14px;
            padding: 5px 0;
        }
        
        QComboBox {
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 5px 10px;
            background-color: rgba(255, 255, 255, 0.05);
            color: #ffffff;
            font-size: 14px;
        }
        
        QComboBox::drop-down {
            border: none;
            background-color: transparent;
        }
        
        QPushButton#toggle_button {
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #9b59b6, stop:1 #8e44ad
            );
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            text-align: center;
            min-height: 40px;
            border: none;
        }
        
        #status_label {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            font-size: 16px;
            text-align: center;
            margin: 10px 0;
        }
        """

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VoiceAssistantApp()
    
    # Инициализация списков после создания окна
    window.device_selector.addItems(window.get_microphone_list())
    window.update_player_list()
    
    window.show()
    sys.exit(app.exec_())