# VoiseAsistent

## Описание Проекта
VoiseAsistent - это настольное голосовое приложение с графическим интерфейсом пользователя, разработанное для управления воспроизведением мультимедиа и громкостью аудио для выбранного процесса с помощью голосовых команд. Приложение использует библиотеку Vosk для распознавания речи и позволяет пользователю выбирать входной микрофон и целевой аудиопроигрыватель через интуитивно понятный интерфейс на PyQt5.
## Назначение
Основная цель проекта - предоставить удобный способ управления аудио воспроизведением на компьютере без необходимости прямого взаимодействия с клавиатурой или мышью. Это может быть полезно во время игры, работы или любой другой активности, когда руки заняты, но есть возможность отдавать голосовые команды.
## Возможности
*   Голосовое управление воспроизведением (пауза/воспроизведение, следующий/предыдущий трек).
*   Голосовое управление громкостью для выбранного аудио процесса.
*   Графический интерфейс для выбора микрофона и целевого аудио проигрывателя.
*   Сохранение выбранных настроек между сессиями.
*   Работа в фоновом режиме после запуска.
## Использование
1.  **Запуск приложения:** Запустите исполняемый файл приложения.
2.  **Выбор устройств:** В главном окне выберите ваш микрофон из списка доступных и целевой аудио проигрыватель, громкостью которого вы хотите управлять.
3.  **Запуск ассистента:** Нажмите кнопку "▶ Запустить". Статус изменится на "Слушаю...".
4.  **Голосовые команды:** Произнесите **одно из активационных слов** (по умолчанию: "помощник", "ассистент", "бот"), а затем команду.
    *   **Управление воспроизведением:** Например, "**помощник** пауза", "**ассистент** следующий трек".
    *   **Управление громкостью:**
        *   Для пошагового изменения: "**бот** громче", "**помощник** тише".
        *   Для установки конкретного уровня (от 0 до 100): "**ассистент** громкость 50".
5.  **Остановка ассистента:** Нажмите кнопку "■ Остановить".

> *Для активации голосового ассистента есть ключевые слова, такие как: бот, помощник, ассистент*
## Технологии и Стек
*   **Python:** Основной язык разработки.
*   **PyQt5:** Для создания графического пользовательского интерфейса.
*   **Vosk:** Оффлайн библиотека для распознавания речи (используется модель `vosk-model-small-ru-0.22`).
*   **sounddevice:** Для работы с аудиоустройствами (микрофоном).
*   **pyautogui:** Для симуляции нажатий медиа-клавиш (Play/Pause, Next, Previous).
*   **pycaw:** Для управления аудио сессиями и громкостью процессов на Windows.
*   **comtypes:** Зависимость для `pycaw`.
*   **QSettings:** Для сохранения и загрузки настроек приложения.
## Установка (для пользователей)
Для установки на пк скачайте папку (или файл из папки) с названием [VoiseAsistent_installer](https://disk.yandex.ru/d/Lf_pkSrHY-i8yQ) и запустите, далее следуйте инструкции установщика.
## Установка (для разработчиков)
Для локального запуска проекта вам потребуется установить следующие зависимости Python:

```bash

pip install PyQt5 vosk sounddevice pyautogui pycaw comtypes

```

Также необходимо скачать русскую модель Vosk (`vosk-model-small-ru-0.22`) и поместить её в директорию рядом с исполняемым файлом скрипта или в `sys._MEIPASS` при сборке исполняемого файла.

После установки зависимостей, вы можете запустить приложение, выполнив скрипт:

```bash

python VoiseAsistent.py

```
