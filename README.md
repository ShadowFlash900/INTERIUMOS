# 🧭 INTERIUM OS — Полная и подробная справочная документация

<img width="266" height="266" alt="intlogo1020205" src="https://github.com/user-attachments/assets/6a658d62-f21e-4f8b-a111-98dfa2d63d65" /> <img width="641" height="207" alt="Frame 2" src="https://github.com/user-attachments/assets/67a530e6-ed3c-4610-b681-70b2261b996e" />



Этот файл — максимально подробное руководство по всем встроенным командам, аргументам и возможностям кастомизации ядра/среды Interium OS. Документ написан на русском языке, содержит примеры использования каждой команды, описание конфигурационных файлов и практическое руководство по расширению через boot-скрипты и модульную архитектуру. Он предназначен для разработчиков и пользователей, которые хотят глубоко кастомизировать систему.

---

## Содержание
1. Обозначения и предварительные понятия  
2. Полный справочник команд (синтаксис → подробное описание → примеры)  
3. Конфигурационные файлы и где их менять  
4. Как кастомизировать ядро и среду: шаги, примеры, лучшие практики  
5. Пример boot-плагина (полный код)  
6. Безопасность, шифрование, ключи и рекомендации  
7. Отладка, логирование и типичные ошибки

---

## 1. Обозначения и предварительные понятия
- sudo — внутренний префикс оболочки Interium: помечает команду как привилегированную. Это НЕ системный sudo и не повышает права процесса. Для реального доступа к файловой системе запускайте Python или launcher.bat с правами администратора/root.  
- AdaptiveNetwork — служба, которая отвечает за разрешение/блокировку сетевых операций. Если статус != `"running"`, сетевые команды вернут ошибку и не выполнятся.  
- Colorize — служба, управляющая цветным выводом. Если выключена, цветовые коды игнорируются.  
- Файловая система проекта располагается внутри корня репозитория: `home/`, `etc/`, `usr/apps/`, `tmp/`, `boot/` и `logs/` (последние создаёт launcher.bat).

---

## 2. Полный справочник команд (подробно)

Каждая команда описана в формате: СИНТАКСИС → ПАРАМЕТРЫ → ПОВЕДЕНИЕ → ПРИМЕР.

- help  
  - Синтаксис: `help`  
  - Аргументы: нет  
  - Поведение: выводит краткий список команд и их назначение.  
  - Пример: `help`

- sys  
  - Синтаксис: `sys`  
  - Возвращает: имя системы, версию, текущего пользователя, профиль, RAM/ROM, ОС, текущую директорию.  
  - Пример: `sys`

- cls  
  - Синтаксис: `cls`  
  - Поведение: очищает экран терминала.  
  - Пример: `cls`

- fm  
  - Синтаксис: `fm`  
  - Внутри: команды `ls`, `cd <dir>`, `mkdir <dir>`, `touch <file.ext>`, `rm <file>`, `mv <src> <dst>`, `cp <src> <dst>`, `cat <file>`, `run <cmd>`, `nano <file>`, `exit`.  
  - Поведение: интерактивный файловый менеджер.  
  - Пример: `fm` → затем `ls`

- nano  
  - Синтаксис: `nano <file>`  
  - Аргументы: `<file>` — путь к файлу; если файла не существует — создаётся.  
  - Управление: `:w` сохранить, `:q` выйти.  
  - Пример: `nano README.md`

- apps  
  - Синтаксис: `apps`  
  - Описание: перечисляет `.py` файлы в `usr/apps/`. (Локальные приложения.)  
  - Пример: `apps`

- run  
  - Синтаксис: `run <app>`  
  - Аргументы: `app` — имя приложения (можно без `.py`)  
  - Поведение: запускает `python usr/apps/<app>.py` в отдельном процессе.  
  - Пример: `run mytool`

- clone  
  - Синтаксис: `clone <git-url>`  
  - Аргументы: URL git-репозитория (https/ssh)  
  - Условие: `AdaptiveNetwork` должен быть `"running"`. Требуется `git` установленный в системе.  
  - Пример: `clone https://github.com/owner/repo.git`

- zip  
  - Синтаксис: `zip <source> <target.zip>`  
  - Поведение: создаёт zip-архив; если source — директория, добавляет рекурсивно.  
  - Пример: `zip myproject project.zip`

- unzip  
  - Синтаксис: `unzip <file.zip> [target_dir]`  
  - Поведение: распаковывает архив в target_dir или в директорию архива по умолчанию.  
  - Пример: `unzip release.zip ./apps`

- getfrom  
  - Синтаксис: `getfrom <repo_url> [release]`  
  - Аргументы: `repo_url` — полный GitHub URL (например `https://github.com/owner/repo`); `release` — необязательное имя релиза/tag.  
  - Поведение: использует GitHub API `/releases` чтобы получить assets; скачивает `.py`, `.zip`, `.exe`, `.sh` и помещает/распаковывает в `usr/apps/`. Записывает метаданные в `usr/installed_apps.json`.  
  - Требование: AdaptiveNetwork = running.  
  - Пример: `getfrom https://github.com/owner/repo v1.0.0`

- getlist  
  - Синтаксис: `getlist <repo_url>`  
  - Поведение: показывает релизы репозитория, их метаданные (name, tag, published_at, author, кол-во файлов) — полезно для выбора релиза при установке.  
  - Пример: `getlist https://github.com/owner/repo`

- getupdate  
  - Синтаксис:  
    - `getupdate interium --check` — проверяет наличие обновления ядра.  
    - `sudo getupdate interium [version]` — скачивает новый `interium.py` из релиза (или latest), делает `interium.py.bak` перед заменой.  
    - `getupdate <repo_name>` — обновляет приложение в `installed_apps.json`.  
    - `getupdate all` — обновляет все установленные приложения.  
  - Требование: AdaptiveNetwork = running для сетевых операций.  
  - Пример: `sudo getupdate interium v1.7`

- installed  
  - Синтаксис: `installed`  
  - Поведение: выводит `installed_apps.json` с указанными версиями и датой установки.  
  - Пример: `installed`

- uninstall  
  - Синтаксис:  
    - `uninstall <app_file>` — удаляет конкретный файл в `usr/apps/`.  
    - `uninstall <repo_name> [version]` — удаляет записи в `installed_apps.json` и связанные файлы (если присутствуют).  
    - `uninstall --list` — показывает локальные `.py` файлы, которые можно удалить.  
  - Пример: `uninstall myapp.py` или `uninstall owner_repo v1.0`

- getapp (QDUGUI)  
  - Синтаксис: `sudo getapp <AppName>`  
  - Поведение: скачивает релиз из QDUGUI репозитория `QDUGUI_URL`, ищет asset с префиксом `<AppName>` и сохраняет в `usr/apps/`. Регистрирует запись в installed_apps.json.  
  - Требование: AdaptiveNetwork = running и права записи в `usr/apps/`.  
  - Пример: `sudo getapp QuickEditor`

- service  
  - Синтаксис: `sudo service <service> <start|stop|restart|status>`  
  - Аргументы: `<service>` — имя службы, `<action>` — действие.  
  - Поведение: управляет `os_system.services`. `status` выводит состояние и автозапуск.  
  - Пример: `sudo service AdaptiveNetwork start`

- systemctl  
  - Синтаксис: `sudo systemctl <start|stop|restart|enable|disable> <service>`  
  - Поведение: аналог `service`, но `enable`/`disable` переключают флаг `enabled`.  
  - Пример: `sudo systemctl enable Colorize`

- settings  
  - Синтаксис: `settings`  
  - Поведение: интерактивное меню для изменения `system_name`, создания пользователей, изменения пароля, управления профилями, языка и приватности.  
  - Пример: `settings`

- history  
  - Синтаксис: `history`  
  - Поведение: показывает последние 20 команд (если не включён private_mode).  
  - Пример: `history`

- find  
  - Синтаксис: `find <dir> <name>`  
  - Поведение: рекурсивный поиск файлов, где `<name>` содержится в имени файла.  
  - Пример: `find ./ src`

- grep  
  - Синтаксис: `grep <text> <file>`  
  - Поведение: ищет текст в файле и печатает `filepath:line:content`.  
  - Пример: `grep TODO src/main.py`

- search  
  - Синтаксис: `search <app>`  
  - Поведение: демонстрационная функция (имитация поиска приложений).  
  - Пример: `search editor`

- clean  
  - Синтаксис: `clean`  
  - Поведение: очищает `tmp/`.  
  - Пример: `clean`

- vault  
  - Синтаксис: `vault add <name> <value>` | `vault get <name>` | `vault list` | `vault remove <name>`  
  - Поведение: `home/.vault` хранит `{name: encrypted_value}`; используется Fernet (etc/secret.key). При `add` значение шифруется; при `get` — расшифровывается.  
  - Пример: `vault add db_password S3cret!` → `vault get db_password`

- bookmark  
  - Синтаксис: `bookmark add <name> <path>` | `bookmark go <name>` | `bookmark list` | `bookmark remove <name>`  
  - Поведение: сохраняет пути в `home/.bookmarks` и позволяет переходить между каталогами.  
  - Пример: `bookmark add proj /home/user/projects` → `bookmark go proj`

- convert  
  - Синтаксис: `convert <file> <format>`  
  - Поддерживаемые: `CSV -> XLSX` (требует `pandas`), `MD -> HTML` (требует `markdown`), `TXT -> PDF` (имитация по умолчанию).  
  - Пример: `convert data.csv XLSX`

- temp  
  - Синтаксис: `temp`  
  - Поведение: возвращает температуру CPU (если `psutil` и платформа поддерживается).  
  - Пример: `temp`

- server  
  - Синтаксис: `server [port]`  
  - Поведение: поднимает HTTP-сервер на указанном порту (по умолчанию 8000).  
  - Пример: `server 8080`

- ping  
  - Синтаксис: `ping <host>`  
  - Поведение: вызывает системную команду `ping`. На Windows используется `-n`, на Unix — `-c`.  
  - Пример: `ping 8.8.8.8`

- echo  
  - Синтаксис: `echo <msg>`  
  - Поведение: выводит сообщение без интерпретации.  
  - Пример: `echo Hello world`

- quit / exit  
  - Синтаксис: `quit` или `exit`  
  - Поведение: завершает работу приложения (0/exit code).  
  - Пример: `exit`

---

## 3. Конфигурационные файлы — где и что менять

- `etc/system_config.json`  
  - Поля: `version`, `ram`, `rom`, `system_name`, `default_profile`, `language`, `autoupdate`, `private_mode`. Изменения применяются после перезапуска (или через `settings`).

- `etc/users.json`  
  - Формат: `{ "username": { "password": "<FERNET token>", "permissions": "user|full", "home_dir": "<path>" } }`  
  - При редактировании вручную убедитесь, что пароли либо зашифрованы Fernet, либо в явном виде — код при загрузке пытается дешифровать и в случае ошибки оставляет строку.

- `etc/services.json`  
  - Определяет список служб и их `status` и `enabled`. При старте `start_services()` поднимает службы с `enabled=true`.

- `usr/installed_apps.json`  
  - Структура: `{ "owner_repo": { "repo_url": "...", "versions": { "v1.0": { "files": [...], "installed_at": "...", "latest_version": "v1.0" } } } }`

- `etc/secret.key`  
  - Бинарный файл Fernet. Крайне важно хранить его в безопасности. Если ключ потерян — расшифровать старые значения невозможно.

- `home/.vault` и `home/.bookmarks`  
  - JSON-файлы для хранилища и закладок.

---

## 4. Как кастомизировать ядро и среду — пошагово

1. Настройки конфигурации (быстро): редактируйте `etc/system_config.json` и `etc/services.json`. Перезапустите interium.py.

2. Добавление новых команд (рекомендуемый путь — без правки `interium_core.py`):
   - Создайте файл в `boot/`, например `boot/mycmd.py`.
   - Реализуйте функцию `register_commands(command_registry, os_system, command_args_info)` и зарегистрируйте ваш обработчик в `command_registry`.
   - Пример регистрации: `command_registry['hello'] = hello_handler`.

3. Расширение логики служб:
   - Добавьте запись в `etc/services.json`.
   - Реализуйте отдельный модуль-интерпретатор, который будет запускаться внутри `InteriumOS.start_services()` (поддержка потоков или subprocess по желанию).

4. Расширение менеджера приложений:
   - Файл `interium_apps.py` содержит `download_release`, `get_releases_list` и `get_app_from_qdugui`. Добавьте обработку других архивов (tar.gz), подписи (sha256) и валидацию.

5. Переопределение цветовой схемы:
   - Измените `Colors` в `interium_utils.py` или добавьте конфиг, где хранятся цветовые коды, и загружайте их в runtime.

6. Пакетизация:
   - Перенесите код в пакет `interium/`, добавьте `setup.py`/`pyproject.toml` и установите `pip install -e .` для разработки. Это упростит импорт и тестирование.

---

## 5. Пример boot-плагина (копируйте в `boot/sample_cmd.py`)

```python
# boot/sample_cmd.py
def hello_handler(command_line, os_system):
    parts = command_line.split()
    if len(parts) > 1:
        print("Hello,", " ".join(parts[1:]))
    else:
        print("Hello! Использование: hello <name>")

def register_commands(command_registry, os_system, command_args_info):
    command_registry['hello'] = hello_handler
    command_args_info['hello'] = "<name> — выводит приветствие"
```

После перезапуска `hello <name>` будет доступна как обычная команда CLI.

---

## 6. Безопасность и шифрование — важные указания
- `etc/secret.key` должен быть в `.gitignore` и защищён. Если ключ скомпрометирован — регенерируйте и мигрируйте данные.
- Vault и пароли шифруются через `cryptography.fernet.Fernet`. Пароли дешифруются в памяти при запуске — будьте аккуратны с окружением и дампами памяти.
- Перед установкой приложений из интернета проверяйте репозитории и содержимое релизов. Запуск произвольного `.py` в `usr/apps` — рискован.
- Для production: используйте внешние секрет-менеджеры и подписи релизов (GPG/sha256).

---

## 7. Отладка и логирование
- Используйте `launcher.bat` Debug Mode для подробных трассировок. Логи сохраняются в `logs/interium_YYYYMMDD_HHMMSS.log`.
- При ошибках с сетевыми командами сначала проверьте `AdaptiveNetwork`:
  - `sudo service AdaptiveNetwork start`
  - `sudo systemctl enable AdaptiveNetwork`
- Ошибки записи в `usr/apps` обычно означают проблемы с правами: запускайте процесс с правами администратора/root или исправьте права/владельца директории.

---
