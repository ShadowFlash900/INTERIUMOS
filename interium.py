import os
import time
import sys
import shutil
import zipfile
import json
from datetime import datetime
import subprocess
import platform
import getpass
import requests
import tempfile
from urllib.parse import urlparse
import re
import base64
from cryptography.fernet import Fernet
import psutil
import webbrowser
import csv
import pandas as pd
import markdown
import http.server
import socketserver
import importlib.util
import time

# Цвета ANSI
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    LIGHTBLUE = '\033[38;5;39m'
    YELLOW = '\033[38;5;226m'
    GREY = '\033[38;5;243m'

def color(text, c):
    # Проверяем состояние службы Colorize
    global global_os_system
    try:
        if global_os_system and global_os_system.services.get("Colorize", {}).get("status", "stopped") != "running":
            return text  # Цвета выключены
    except Exception:
        pass  # На старте или при ошибке выводим без цвета
    return f"{c}{text}{Colors.ENDC}"

# ---------------- Файловая система ----------------
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
FS = {
    "HOME_DIR": os.path.join(ROOT_DIR, "home"),
    "ETC_DIR": os.path.join(ROOT_DIR, "etc"),
    "TMP_DIR": os.path.join(ROOT_DIR, "tmp"),
    "BOOT_DIR": os.path.join(ROOT_DIR, "boot"),
    "ROOT_HOME": os.path.join(ROOT_DIR, "root"),
    "USR_DIR": os.path.join(ROOT_DIR, "usr"),
    "VAR_DIR": os.path.join(ROOT_DIR, "var"),
    "LOG_DIR": os.path.join(ROOT_DIR, "var", "log"),
}
APPS_DIR = os.path.join(FS["USR_DIR"], "apps")
INSTALLED_APPS_FILE = os.path.join(FS["USR_DIR"], "installed_apps.json")
CONFIG_FILE = os.path.join(FS["ETC_DIR"], "system_config.json")
USER_FILE = os.path.join(FS["ETC_DIR"], "users.json")
PROFILES_FILE = os.path.join(FS["ETC_DIR"], "profiles.json")
SERVICES_FILE = os.path.join(FS["ETC_DIR"], "services.json")
HISTORY_FILE = os.path.join(FS["HOME_DIR"], ".history")
VAULT_FILE = os.path.join(FS["HOME_DIR"], ".vault")
BOOKMARKS_FILE = os.path.join(FS["HOME_DIR"], ".bookmarks")
INTERIUM_UPDATE_URL = "https://github.com/ShadowFlash900/INTERIUMOS"
QDUGUI_URL = "https://github.com/ShadowFlash900/QDUGUI"

command_args_info = {
    "calculate": "<выражение> — строка, которую нужно вычислить, например: calculate 2+2",
    "echo": "<текст> — текст для вывода",
    "ping": "<адрес> — адрес для проверки сети",
    "clone": "<git-url> — адрес репозитория для клонирования",
    "zip": "<источник> <zip-архив> — что архивировать и как назвать архив",
    "unzip": "<zip-архив> [папка] — архив и (необязательно) папка для распаковки",
    "getfrom": "<url> [релиз] — установка приложения из репозитория",
    "getlist": "<url> — показать релизы репозитория",
    "getupdate": "interium [версия] — обновить ядро системы",
    "installed": "— список установленных приложений",
    "uninstall": "<имя_файла> — удалить приложение из usr/apps",
    "getapp": "<AppName> — установить приложение из QDUGUI",
    "service": "<service> <start|stop|restart|status> — управление службой",
    "systemctl": "<start|stop|restart|enable|disable> <service> — автозапуск службы",
    "settings": "— настройки системы",
    "cls": "— очистить экран",
    "fm": "— файловый менеджер",
    "sys": "— информация о системе",
    "help": "— список команд",
    "exit/quit": "— выход"
}

# Генерация ключа шифрования
def generate_key():
    key = Fernet.generate_key()
    with open(os.path.join(FS["ETC_DIR"], "secret.key"), "wb") as key_file:
        key_file.write(key)

def load_key():
    try:
        with open(os.path.join(FS["ETC_DIR"], "secret.key"), "rb") as f:
            return f.read()
    except FileNotFoundError:
        generate_key()
        return open(os.path.join(FS["ETC_DIR"], "secret.key"), "rb").read()

def encrypt_data(data):
    f = Fernet(load_key())
    return f.encrypt(data.encode()).decode()

def decrypt_data(data):
    f = Fernet(load_key())
    return f.decrypt(data.encode()).decode()

def create_fs():
    for d in FS.values():
        os.makedirs(d, exist_ok=True)
    os.makedirs(APPS_DIR, exist_ok=True)
    if not os.path.exists(os.path.join(FS["ETC_DIR"], "secret.key")):
        generate_key()

def load_services():
    default = {
        "AdaptiveNetwork": {"status": "running", "enabled": True},
        "LoggingService": {"status": "running", "enabled": True},
        "UpdateChecker": {"status": "stopped", "enabled": False},
        "Firewall": {"status": "stopped", "enabled": False},
        "BackupService": {"status": "stopped", "enabled": False},
        "TaskScheduler": {"status": "stopped", "enabled": False},
        "WebServer": {"status": "stopped", "enabled": False},
        "SSHService": {"status": "stopped", "enabled": False},
        "DNSService": {"status": "stopped", "enabled": False},
        "NotificationService": {"status": "stopped", "enabled": False},
        "ClipboardService": {"status": "stopped", "enabled": False},
        "Colorize": {"status": "running", "enabled": True}
    }
    if os.path.exists(SERVICES_FILE):
        try:
            with open(SERVICES_FILE, "r") as f:
                services = json.load(f)
                # Гарантируем наличие Colorize
                if "Colorize" not in services:
                    services["Colorize"] = default["Colorize"]
                if "AdaptiveNetwork" not in services:
                    services["AdaptiveNetwork"] = default["AdaptiveNetwork"]
                return services
        except:
            return default.copy()
    return default.copy()

def save_services(services):
    with open(SERVICES_FILE, "w") as f:
        json.dump(services, f, indent=4)

def adaptive_network_required(os_system):
    return os_system.services.get("AdaptiveNetwork", {}).get("status", "stopped") != "running"

def load_boot_scripts(os_system, command_registry, command_args_info):
    boot_dir = FS["BOOT_DIR"]
    if not os.path.exists(boot_dir):
        return
    for filename in os.listdir(boot_dir):
        if filename.endswith(".py"):
            script_path = os.path.join(boot_dir, filename)
            try:
                spec = importlib.util.spec_from_file_location(f"boot_{filename}", script_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "register_commands"):
                    # Теперь передаём третий аргумент!
                    module.register_commands(command_registry, os_system, command_args_info)
                    print(color(f"Загружен скрипт boot/{filename} и зарегистрированы команды.", Colors.OKGREEN))
                else:
                    print(color(f"Скрипт {filename} не содержит функцию register_commands!", Colors.WARNING))
            except Exception as e:
                print(color(f"Ошибка при загрузке скрипта {filename}: {e}", Colors.FAIL))

class InteriumOS:
    def __init__(self):
        create_fs()
        self.current_user = None
        self.current_profile = None
        self.system_config = self.load_config()
        self.users = self.load_users()
        self.profiles = self.load_profiles()
        self.installed_apps = self.load_installed_apps()
        self.current_dir = os.getcwd()
        self.is_root = False
        self.services = load_services()
        self.boot_time = time.time()
        self.command_history = self.load_history()
        self.clipboard = ""
        self.create_dirs([FS["HOME_DIR"], APPS_DIR, FS["ETC_DIR"], FS["TMP_DIR"], FS["BOOT_DIR"], FS["ROOT_HOME"], FS["USR_DIR"]])
        self.first_run_check()
        self.start_services()

    def start_services(self):
        for service, config in self.services.items():
            if config["enabled"] and config["status"] != "running":
                self.services[service]["status"] = "running"
        save_services(self.services)

    def create_dirs(self, dirs):
        for directory in dirs:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

    def load_config(self):
        default_config = {
            "version": "1.6",
            "ram": "1VGB",
            "rom": "1VGB",
            "system_name": "Interium OS",
            "created_at": str(datetime.now()),
            "default_profile": "default",
            "language": "en",
            "autoupdate": False,
            "private_mode": False,
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except:
                return default_config
        return default_config

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.system_config, f, indent=4)

    def load_users(self):
        default_users = {
            "admin": {
                "password": encrypt_data("admin"),
                "permissions": "full",
                "home_dir": FS["ROOT_HOME"]
            }
        }
        if os.path.exists(USER_FILE):
            try:
                with open(USER_FILE, "r") as f:
                    users = json.load(f)
                    # Дешифруем пароли
                    for user, data in users.items():
                        try:
                            data["password"] = decrypt_data(data["password"])
                        except:
                            # Если не удается дешифровать, оставляем как есть
                            pass
                        user_dir = data.get("home_dir", os.path.join(FS["HOME_DIR"], user))
                        if not os.path.exists(user_dir):
                            os.makedirs(user_dir, exist_ok=True)
                    return users
            except:
                return default_users
        return default_users

    def save_users(self):
        # Шифруем пароли перед сохранением
        users_to_save = self.users.copy()
        for user, data in users_to_save.items():
            data["password"] = encrypt_data(data["password"])
        with open(USER_FILE, "w") as f:
            json.dump(users_to_save, f, indent=4)

    def load_profiles(self):
        default_profiles = {
            "default": {
                "description": "Стандартный профиль",
                "created_at": str(datetime.now()),
                "settings": {
                    "theme": "light",
                    "language": "ru"
                }
            }
        }
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, "r") as f:
                    return json.load(f)
            except:
                return default_profiles
        return default_profiles

    def save_profiles(self):
        with open(PROFILES_FILE, "w") as f:
            json.dump(self.profiles, f, indent=4)

    def load_installed_apps(self):
        if os.path.exists(INSTALLED_APPS_FILE):
            try:
                with open(INSTALLED_APPS_FILE, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_installed_apps(self):
        with open(INSTALLED_APPS_FILE, "w") as f:
            json.dump(self.installed_apps, f, indent=4)

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    return f.read().splitlines()
            except:
                return []
        return []

    def save_history(self):
        if not self.system_config.get("private_mode", False):
            with open(HISTORY_FILE, "w") as f:
                f.write("\n".join(self.command_history[-100:]))

    def first_run_check(self):
        if len(self.users) == 1 and list(self.users.keys())[0] == "admin":
            print(color("Похоже, это первый запуск системы.", Colors.OKCYAN))
            print(color("Создайте свой аккаунт для дальнейшей работы.", Colors.OKCYAN))
            while True:
                username = input("Введите имя пользователя: ")
                if not username or username in self.users:
                    print(color("Имя занято или некорректно!", Colors.FAIL))
                    continue
                password = getpass.getpass("Пароль: ")
                confirm = getpass.getpass("Подтвердите пароль: ")
                if password != confirm:
                    print(color("Пароли не совпадают!", Colors.FAIL))
                    continue
                self.users[username] = {
                    "password": password,
                    "permissions": "user",
                    "home_dir": os.path.join(FS["HOME_DIR"], username)
                }
                self.save_users()
                os.makedirs(os.path.join(FS["HOME_DIR"], username), exist_ok=True)
                print(color(f"Пользователь {username} создан!", Colors.OKGREEN))
                break

    def login(self):
        cls()
        print(color(f"{self.system_config['system_name']} v{self.system_config['version']}", Colors.HEADER))
        print(color("Для выхода введите 'exit'", Colors.GREY))
        while True:
            username = input("Имя пользователя: ")
            if username == "exit":
                sys.exit(0)
            if username in self.users:
                password = getpass.getpass("Пароль: ")
                if password == self.users[username]["password"]:
                    self.current_user = username
                    self.is_root = (username == "admin")
                    user_dir = self.users[username].get("home_dir", os.path.join(FS["HOME_DIR"], username))
                    if not os.path.exists(user_dir):
                        os.makedirs(user_dir, exist_ok=True)
                    os.chdir(user_dir)
                    self.current_dir = user_dir
                    self.current_profile = self.system_config.get("default_profile", "default")
                    print(color(f"Добро пожаловать, {username} (профиль: {self.current_profile})!", Colors.OKGREEN))
                    time.sleep(1)
                    return
                else:
                    print(color("Неверный пароль!", Colors.FAIL))
            else:
                print(color("Пользователь не найден!", Colors.FAIL))

def cls():
    os.system("cls" if os.name == "nt" else "clear")

def list_py_apps():
    apps = []
    if os.path.exists(APPS_DIR):
        for file in os.listdir(APPS_DIR):
            if file.endswith(".py"):
                apps.append(file)
    return apps

def run_py_app(app_name):
    if not app_name.endswith(".py"):
        app_name += ".py"
    app_path = os.path.join(APPS_DIR, app_name)
    if os.path.exists(app_path):
        try:
            subprocess.run([sys.executable, app_path], check=True)
        except subprocess.CalledProcessError as e:
            print(color(f"Ошибка при запуске приложения: {e}", Colors.FAIL))
    else:
        print(color(f"Приложение {app_name} не найдено!", Colors.FAIL))

def animate_loading(message, seconds=3):
    spinner = ['|', '/', '-', '\\']
    print(color(message, Colors.LIGHTBLUE), end=' ')
    for i in range(seconds*4):
        print(color(spinner[i % 4], Colors.LIGHTBLUE), end='\r')
        time.sleep(0.25)
    print(' '*10, end='\r')

def clone_repo(url, os_system):
    if adaptive_network_required(os_system):
        print(color("Сетевая функция отключена! Включите AdaptiveNetwork.", Colors.FAIL))
        return False
    try:
        if not shutil.which("git"):
            print(color("Git не установлен в системе!", Colors.FAIL))
            return False
        repo_name = url.split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        clone_dir = os.path.join(FS["HOME_DIR"], repo_name)
        if os.path.exists(clone_dir):
            print(color(f"Директория {clone_dir} уже существует!", Colors.WARNING))
            return False
        animate_loading("Клонирование репозитория...")
        subprocess.run(["git", "clone", url, clone_dir], check=True)
        print(color(f"Репозиторий успешно клонирован в {clone_dir}", Colors.OKGREEN))
        return True
    except subprocess.CalledProcessError as e:
        print(color(f"Ошибка при клонировании репозитория: {e}", Colors.FAIL))
        return False
    except Exception as e:
        print(color(f"Ошибка: {e}", Colors.FAIL))
        return False

def extract_zip(zip_file, target_dir=None):
    if not target_dir:
        target_dir = os.path.dirname(zip_file)
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        print(color(f"Архив {zip_file} успешно распакован в {target_dir}", Colors.OKGREEN))
        return True
    except Exception as e:
        print(color(f"Ошибка при распаковке архива: {e}", Colors.FAIL))
        return False

def create_zip(source, zip_name):
    try:
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.isdir(source):
                for root, dirs, files in os.walk(source):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(source))
                        zipf.write(file_path, arcname)
            else:
                zipf.write(source, os.path.basename(source))
        print(color(f"Архив {zip_name} успешно создан", Colors.OKGREEN))
        return True
    except Exception as e:
        print(color(f"Ошибка при создании архива: {e}", Colors.FAIL))
        return False

def ping(host, os_system):
    if adaptive_network_required(os_system):
        print(color("Сетевая функция отключена! Включите AdaptiveNetwork.", Colors.FAIL))
        return
    try:
        print(color(f"Пинг {host}...", Colors.OKBLUE))
        result = subprocess.run(["ping", "-c", "4" if os.name != "nt" else "-n", "4", host], capture_output=True, text=True)
        print(color(result.stdout, Colors.GREY))
    except Exception as e:
        print(color(f"Ошибка: {e}", Colors.FAIL))

def file_manager():
    cls()
    current_dir = os.getcwd()
    print(color(f"Файловый менеджер (текущая директория: {current_dir})", Colors.OKGREEN))
    print(color("Команды: ls, cd <dir>, mkdir <dir>, touch <file.ext>, rm <file>, mv <src> <dst>, cp <src> <dst>, cat <file>, run <cmd>, nano <file>, exit", Colors.YELLOW))
    while True:
        cmd = input(color("fm> ", Colors.OKBLUE)).strip().split()
        if not cmd:
            continue
        if cmd[0] == "exit":
            break
        elif cmd[0] == "ls":
            print(color("\nСодержимое директории:", Colors.YELLOW))
            for item in os.listdir(current_dir):
                print(f"{color('[DIR]', Colors.OKCYAN) if os.path.isdir(os.path.join(current_dir, item)) else color('[FILE]', Colors.OKGREEN)} {item}")
            print()
        elif cmd[0] == "cd" and len(cmd) > 1:
            new_dir = cmd[1]
            try:
                if new_dir == "..":
                    os.chdir("..")
                else:
                    os.chdir(new_dir)
                current_dir = os.getcwd()
                print(color(f"Текущая директория: {current_dir}", Colors.OKBLUE))
            except Exception as e:
                print(color(f"Ошибка: {e}", Colors.FAIL))
        elif cmd[0] == "mkdir" and len(cmd) > 1:
            try:
                os.mkdir(cmd[1])
                print(color(f"Директория {cmd[1]} создана", Colors.OKGREEN))
            except Exception as e:
                print(color(f"Ошибка: {e}", Colors.FAIL))
        elif cmd[0] == "touch" and len(cmd) > 1:
            try:
                filename = cmd[1]
                if "." not in filename:
                    print(color("Укажите расширение файла, например file.py, file.txt, file.cpp", Colors.WARNING))
                    continue
                with open(os.path.join(current_dir, filename), 'w') as f:
                    content = input(color("Введите содержимое файла (оставьте пустым для создания пустого файла): ", Colors.GREY))
                    f.write(content)
                print(color(f"Файл {filename} успешно создан", Colors.OKGREEN))
            except Exception as e:
                print(color(f"Ошибка при создании файла: {e}", Colors.FAIL))
        elif cmd[0] == "rm" and len(cmd) > 1:
            try:
                target = cmd[1]
                if os.path.isdir(target):
                    shutil.rmtree(target)
                else:
                    os.remove(target)
                print(color(f"{target} удален", Colors.OKGREEN))
            except Exception as e:
                print(color(f"Ошибка: {e}", Colors.FAIL))
        elif cmd[0] == "mv" and len(cmd) > 2:
            try:
                shutil.move(cmd[1], cmd[2])
                print(color(f"{cmd[1]} перемещён в {cmd[2]}", Colors.OKGREEN))
            except Exception as e:
                print(color(f"Ошибка при перемещении: {e}", Colors.FAIL))
        elif cmd[0] == "cp" and len(cmd) > 2:
            try:
                if os.path.isdir(cmd[1]):
                    shutil.copytree(cmd[1], cmd[2])
                else:
                    shutil.copy2(cmd[1], cmd[2])
                print(color(f"{cmd[1]} скопирован в {cmd[2]}", Colors.OKGREEN))
            except Exception as e:
                print(color(f"Ошибка при копировании: {e}", Colors.FAIL))
        elif cmd[0] == "cat" and len(cmd) > 1:
            try:
                with open(cmd[1], 'r', encoding="utf-8") as f:
                    print(color(f.read(), Colors.GREY))
            except Exception as e:
                print(color(f"Ошибка при чтении файла: {e}", Colors.FAIL))
        elif cmd[0] == "run" and len(cmd) > 1:
            try:
                result = subprocess.run(' '.join(cmd[1:]), shell=True, capture_output=True, text=True)
                print(color(result.stdout, Colors.OKGREEN))
                if result.stderr:
                    print(color(result.stderr, Colors.FAIL))
            except Exception as e:
                print(color(f"Ошибка: {e}", Colors.FAIL))
        elif cmd[0] == "nano" and len(cmd) > 1:
            nano_editor(cmd[1])
        else:
            print(color("Неизвестная команда", Colors.WARNING))

def nano_editor(filename):
    lines = []
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
    print(color(f"Редактор nano: {filename}. Для сохранения введите :w, для выхода :q", Colors.YELLOW))
    print(color("Текущее содержимое файла:", Colors.GREY))
    for l in lines:
        print(l)
    buffer = lines[:]
    while True:
        inp = input(color("nano> ", Colors.OKBLUE))
        if inp == ":w":
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(buffer))
            print(color("Файл сохранён", Colors.OKGREEN))
        elif inp == ":q":
            print(color("Выход из редактора", Colors.OKCYAN))
            break
        else:
            buffer.append(inp)

def system_settings(os_system):
    cls()
    print(color("Настройки системы", Colors.HEADER))
    print(color("1. Изменить имя системы", Colors.YELLOW))
    print(color("2. Добавить пользователя", Colors.YELLOW))
    print(color("3. Изменить пароль", Colors.YELLOW))
    print(color("4. Управление профилями", Colors.YELLOW))
    print(color("5. Настройки языка", Colors.YELLOW))
    print(color("6. Настройки приватности", Colors.YELLOW))
    print(color("7. Вернуться", Colors.YELLOW))
    choice = input("Выберите действие: ")
    if choice == "1":
        new_name = input("Новое имя системы: ")
        os_system.system_config["system_name"] = new_name
        os_system.save_config()
        print(color("Имя системы изменено!", Colors.OKGREEN))
    elif choice == "2":
        username = input("Новое имя пользователя: ")
        if username in os_system.users:
            print(color("Пользователь уже существует!", Colors.FAIL))
        else:
            password = getpass.getpass("Пароль: ")
            confirm = getpass.getpass("Подтвердите пароль: ")
            if password == confirm:
                os_system.users[username] = {
                    "password": password,
                    "permissions": "user",
                    "home_dir": os.path.join(FS["HOME_DIR"], username)
                }
                os_system.save_users()
                os.makedirs(os.path.join(FS["HOME_DIR"], username), exist_ok=True)
                print(color("Пользователь создан!", Colors.OKGREEN))
            else:
                print(color("Пароли не совпадают!", Colors.FAIL))
    elif choice == "3":
        if not os_system.current_user:
            print(color("Сначала войдите в систему!", Colors.FAIL))
            return
        old_pass = getpass.getpass("Текущий пароль: ")
        if old_pass != os_system.users[os_system.current_user]["password"]:
            print(color("Неверный пароль!", Colors.FAIL))
            return
        new_pass = getpass.getpass("Новый пароль: ")
        confirm = getpass.getpass("Подтвердите пароль: ")
        if new_pass == confirm:
            os_system.users[os_system.current_user]["password"] = new_pass
            os_system.save_users()
            print(color("Пароль изменен!", Colors.OKGREEN))
        else:
            print(color("Пароли не совпадают!", Colors.FAIL))
    elif choice == "4":
        manage_profiles(os_system)
    elif choice == "5":
        language = input("Выберите язык (ru/en): ").lower()
        if language in ["ru", "en"]:
            os_system.system_config["language"] = language
            os_system.save_config()
            print(color(f"Язык изменен на {language}", Colors.OKGREEN))
        else:
            print(color("Неподдерживаемый язык", Colors.FAIL))
    elif choice == "6":
        private = input("Включить приватный режим (история команд не сохраняется)? (y/n): ").lower()
        os_system.system_config["private_mode"] = private == "y"
        os_system.save_config()
        print(color(f"Приватный режим {'включен' if os_system.system_config['private_mode'] else 'выключен'}", Colors.OKGREEN))

def manage_profiles(os_system):
    while True:
        cls()
        print(color("Управление профилями", Colors.HEADER))
        print(color(f"Текущий профиль: {os_system.current_profile}", Colors.OKBLUE))
        print(color("1. Создать новый профиль", Colors.YELLOW))
        print(color("2. Переключить профиль", Colors.YELLOW))
        print(color("3. Изменить настройки профиля", Colors.YELLOW))
        print(color("4. Удалить профиль", Colors.YELLOW))
        print(color("5. Назначить профиль по умолчанию", Colors.YELLOW))
        print(color("6. Вернуться", Colors.YELLOW))
        choice = input("Выберите действие: ")
        if choice == "1":
            profile_name = input("Имя нового профиля: ")
            if profile_name in os_system.profiles:
                print(color("Профиль с таким именем уже существует!", Colors.FAIL))
            else:
                os_system.profiles[profile_name] = {
                    "description": input("Описание профиля: "),
                    "created_at": str(datetime.now()),
                    "settings": {
                        "theme": "light",
                        "language": "ru"
                    }
                }
                os_system.save_profiles()
                print(color(f"Профиль {profile_name} создан!", Colors.OKGREEN))
            time.sleep(1)
        elif choice == "2":
            print("Доступные профили:")
            for profile in os_system.profiles:
                print(f"- {profile}")
            profile_name = input("Выберите профиль: ")
            if profile_name in os_system.profiles:
                os_system.current_profile = profile_name
                print(color(f"Профиль изменен на {profile_name}", Colors.OKGREEN))
            else:
                print(color("Профиль не найден!", Colors.FAIL))
            time.sleep(1)
        elif choice == "3":
            print("Текущие настройки профиля:")
            profile = os_system.profiles[os_system.current_profile]
            for key, value in profile["settings"].items():
                print(f"{key}: {value}")
            setting = input("Какое свойство изменить? (theme/language): ")
            if setting in ["theme", "language"]:
                new_value = input(f"Новое значение для {setting}: ")
                profile["settings"][setting] = new_value
                os_system.save_profiles()
                print(color("Настройка изменена!", Colors.OKGREEN))
            else:
                print(color("Недопустимое свойство", Colors.FAIL))
            time.sleep(1)
        elif choice == "4":
            print("Доступные профили:")
            for profile in os_system.profiles:
                print(f"- {profile}")
            profile_name = input("Какой профиль удалить? (нельзя удалить текущий): ")
            if profile_name == os_system.current_profile:
                print(color("Нельзя удалить текущий профиль!", Colors.FAIL))
            elif profile_name in os_system.profiles:
                del os_system.profiles[profile_name]
                os_system.save_profiles()
                print(color(f"Профиль {profile_name} удален!", Colors.OKGREEN))
            else:
                print(color("Профиль не найден!", Colors.FAIL))
            time.sleep(1)
        elif choice == "5":
            print("Доступные профили:")
            for profile in os_system.profiles:
                print(f"- {profile}")
            profile_name = input("Какой профиль сделать профилем по умолчанию? ")
            if profile_name in os_system.profiles:
                os_system.system_config["default_profile"] = profile_name
                os_system.save_config()
                print(color(f"Профиль {profile_name} теперь используется по умолчанию!", Colors.OKGREEN))
            else:
                print(color("Профиль не найден!", Colors.FAIL))
            time.sleep(1)
        elif choice == "6":
            return
        else:
            print(color("Неверный выбор!", Colors.FAIL))
            time.sleep(1)

def get_repo_name_from_url(url):
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) >= 2:
        return f"{path_parts[0]}_{path_parts[1]}"
    return None

def get_latest_release_version(repo_url):
    try:
        api_url = repo_url.replace("github.com", "api.github.com/repos").replace("/releases", "")
        releases_url = f"{api_url}/releases/latest"
        response = requests.get(releases_url)
        response.raise_for_status()
        return response.json()["tag_name"]
    except:
        return None

def download_release(os_system, repo_url, release_name=None):
    if adaptive_network_required(os_system):
        print(color("Сетевая функция отключена! Включите AdaptiveNetwork.", Colors.FAIL))
        return False
    try:
        if "github.com" not in repo_url:
            print(color("Поддерживаются только GitHub репозитории", Colors.FAIL))
            return False
        repo_name = get_repo_name_from_url(repo_url)
        if not repo_name:
            print(color("Неверный URL репозитория", Colors.FAIL))
            return False
        api_url = repo_url.replace("github.com", "api.github.com/repos").replace("/releases", "")
        releases_url = f"{api_url}/releases"
        animate_loading("Получение информации о релизах...")
        response = requests.get(releases_url)
        response.raise_for_status()
        releases = response.json()
        if not releases:
            print(color("В репозитории нет релизов", Colors.WARNING))
            return False
        if release_name is None:
            release = releases[0]
            release_name = release['name']
        else:
            release = next((r for r in releases if r['name'].lower() == release_name.lower()), None)
            if not release:
                print(color(f"Релиз {release_name} не найден", Colors.FAIL))
                return False
        if repo_name in os_system.installed_apps and release_name in os_system.installed_apps[repo_name]['versions']:
            print(color(f"Версия {release_name} уже установлена", Colors.WARNING))
            return False
        if not release['assets']:
            print(color("В релизе нет файлов для скачивания", Colors.WARNING))
            return False
        with tempfile.TemporaryDirectory() as temp_dir:
            installed_files = []
            for asset in release['assets']:
                if asset['name'].endswith(('.py', '.zip', '.exe', '.sh')):
                    print(color(f"Скачивание {asset['name']}...", Colors.LIGHTBLUE))
                    animate_loading(f"Загрузка {asset['name']}...", 4)
                    download_url = asset['browser_download_url']
                    file_path = os.path.join(temp_dir, asset['name'])
                    with requests.get(download_url, stream=True) as r:
                        r.raise_for_status()
                        with open(file_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                    if asset['name'].endswith('.zip'):
                        if extract_zip(file_path, APPS_DIR):
                            installed_files.append(f"zip:{asset['name']}")
                    else:
                        target_path = os.path.join(APPS_DIR, asset['name'])
                        shutil.move(file_path, target_path)
                        installed_files.append(asset['name'])
            if repo_name not in os_system.installed_apps:
                os_system.installed_apps[repo_name] = {
                    "repo_url": repo_url,
                    "versions": {}
                }
            os_system.installed_apps[repo_name]['versions'][release_name] = {
                "files": installed_files,
                "installed_at": str(datetime.now()),
                "latest_version": release_name
            }
            os_system.save_installed_apps()
        print(color(f"Релиз {release_name} успешно установлен", Colors.OKGREEN))
        return True
    except Exception as e:
        print(color(f"Ошибка при скачивании релиза: {e}", Colors.FAIL))
        return False

def get_releases_list(repo_url, os_system):
    if adaptive_network_required(os_system):
        print(color("Сетевая функция отключена! Включите AdaptiveNetwork.", Colors.FAIL))
        return False
    try:
        if "github.com" not in repo_url:
            print(color("Поддерживаются только GitHub репозитории", Colors.FAIL))
            return False
        api_url = repo_url.replace("github.com", "api.github.com/repos").replace("/releases", "")
        releases_url = f"{api_url}/releases"
        animate_loading("Получение списка релизов...")
        response = requests.get(releases_url)
        response.raise_for_status()
        releases = response.json()
        if not releases:
            print(color("В репозитории нет релизов", Colors.WARNING))
            return False
        print(color(f"\nСписок релизов в {repo_url}:", Colors.HEADER))
        print(color("-" * 50, Colors.GREY))
        for i, release in enumerate(releases, 1):
            print(color(f"\n{i}. {release['name']} ({release['tag_name']})", Colors.YELLOW))
            print(f"   {color('Дата:', Colors.GREY)} {release['published_at']}")
            print(f"   {color('Автор:', Colors.GREY)} {release['author']['login']}")
            print(f"   {color('Описание:', Colors.GREY)} {release.get('body', 'нет описания')[:100]}...")
            print(f"   {color('Файлов:', Colors.GREY)} {len(release['assets'])}")
            print(color("-" * 50, Colors.GREY))
        return True
    except Exception as e:
        print(color(f"Ошибка при получении списка релизов: {e}", Colors.FAIL))
        return False

def check_for_updates(os_system):
    if adaptive_network_required(os_system):
        print(color("Сетевая функция отключена! Включите AdaptiveNetwork.", Colors.FAIL))
        return None
    try:
        api_url = INTERIUM_UPDATE_URL.replace("github.com", "api.github.com/repos")
        releases_url = f"{api_url}/releases/latest"
        animate_loading("Проверка обновлений...")
        response = requests.get(releases_url)
        response.raise_for_status()
        latest_release = response.json()
        current_version = os_system.system_config["version"]
        latest_version = latest_release["tag_name"]
        if latest_version > current_version:
            print(color(f"Доступно обновление: {latest_version} (текущая версия: {current_version})", Colors.WARNING))
            return latest_version
        else:
            print(color("У вас установлена последняя версия системы", Colors.OKGREEN))
            return None
    except Exception as e:
        print(color(f"Ошибка при проверке обновлений: {e}", Colors.FAIL))
        return None

def update_interium(os_system, version=None):
    if adaptive_network_required(os_system):
        print(color("Сетевая функция отключена! Включите AdaptiveNetwork.", Colors.FAIL))
        return False
    try:
        api_url = INTERIUM_UPDATE_URL.replace("github.com", "api.github.com/repos")
        if version:
            releases_url = f"{api_url}/releases/tags/{version}"
        else:
            releases_url = f"{api_url}/releases/latest"
        animate_loading("Загрузка обновления ядра...", 4)
        response = requests.get(releases_url)
        response.raise_for_status()
        release = response.json()
        with tempfile.TemporaryDirectory() as temp_dir:
            for asset in release["assets"]:
                if asset["name"] == "interium.py":
                    print(color("Скачивание нового ядра системы...", Colors.OKBLUE))
                    animate_loading("Загрузка interium.py...", 4)
                    download_url = asset["browser_download_url"]
                    file_path = os.path.join(temp_dir, asset["name"])
                    with requests.get(download_url, stream=True) as r:
                        r.raise_for_status()
                        with open(file_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                    current_path = os.path.abspath(__file__)
                    backup_path = current_path + ".bak"
                    shutil.copyfile(current_path, backup_path)
                    print(color(f"Создана резервная копия: {backup_path}", Colors.OKCYAN))
                    shutil.move(file_path, current_path)
                    print(color("Ядро системы успешно обновлено!", Colors.OKGREEN))
                    os_system.system_config["version"] = release["tag_name"]
                    os_system.save_config()
                    return True
        print(color("Файл ядра (interium.py) не найден в релизе", Colors.WARNING))
        return False
    except Exception as e:
        print(color(f"Ошибка при обновлении системы: {e}", Colors.FAIL))
        return False

def list_installed_apps(os_system, check_updates=False):
    if not os_system.installed_apps:
        print(color("Нет установленных приложений", Colors.WARNING))
        return
    print(color("Установленные приложения:", Colors.HEADER))
    for repo, data in os_system.installed_apps.items():
        print(f"\n{color('Репозиторий:', Colors.OKCYAN)} {repo}")
        print(f"{color('URL:', Colors.LIGHTBLUE)} {data['repo_url']}")
        print(color('Версии:', Colors.YELLOW))
        for version, info in data['versions'].items():
            status = color("Актуально", Colors.OKGREEN)
            if check_updates:
                latest_version = get_latest_release_version(data['repo_url'])
                if latest_version and latest_version != version:
                    status = color(f"Обновление доступно: {latest_version}", Colors.WARNING)
                    info['latest_version'] = latest_version
                else:
                    info['latest_version'] = version
                os_system.save_installed_apps()
            print(color(f"  {version} (установлено {info['installed_at']}) {status}", Colors.OKGREEN))

def uninstall_app(os_system, repo_name, version=None):
    if repo_name == "--list":
        # Показываем список установленных приложений, которые можно удалить
        if not os_system.installed_apps:
            print(color("Нет установленных приложений для удаления", Colors.WARNING))
            return False
        print(color("Установленные приложения, доступные для удаления:", Colors.HEADER))
        for repo in os_system.installed_apps.keys():
            print(color(f"- {repo}", Colors.OKGREEN))
        return True

    if repo_name not in os_system.installed_apps:
        print(color(f"Репозиторий {repo_name} не найден в установленных приложениях", Colors.WARNING))
        return False
    versions = os_system.installed_apps[repo_name]['versions']
    if version is None:
        for ver, info in versions.items():
            for file in info['files']:
                if file.startswith("zip:"):
                    print(color(f"Файлы из архива {file[4:]} нужно удалить вручную", Colors.WARNING))
                else:
                    file_path = os.path.join(APPS_DIR, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(color(f"Удален файл {file}", Colors.OKGREEN))
        del os_system.installed_apps[repo_name]
    else:
        if version not in versions:
            print(color(f"Версия {version} не найдена для репозитория {repo_name}", Colors.WARNING))
            return False
        for file in versions[version]['files']:
            if file.startswith("zip:"):
                print(color(f"Файлы из архива {file[4:]} нужно удалить вручную", Colors.WARNING))
            else:
                file_path = os.path.join(APPS_DIR, file)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(color(f"Удален файл {file}", Colors.OKGREEN))
        del versions[version]
        if not versions:
            del os_system.installed_apps[repo_name]
    os_system.save_installed_apps()
    print(color("Удаление завершено", Colors.OKGREEN))
    return True

    try:
        repo_url = QDUGUI_URL
        api_url = repo_url.replace("github.com", "api.github.com/repos")
        releases_url = f"{api_url}/releases/latest"
        animate_loading("Получение релиза QDUGUI...")
        response = requests.get(releases_url)
        response.raise_for_status()
        release = response.json()
        for asset in release['assets']:
            if asset['name'].startswith(app_name):
                print(color(f"Скачивание {asset['name']}...", Colors.LIGHTBLUE))
                animate_loading(f"Загрузка {asset['name']}...", 4)
                download_url = asset['browser_download_url']
                file_path = os.path.join(APPS_DIR, asset['name'])
                with requests.get(download_url, stream=True) as r:
                    r.raise_for_status()
                    with open(file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                print(color(f"{app_name} успешно установлен из QDUGUI!", Colors.OKGREEN))
                repo_name = get_repo_name_from_url(repo_url)
                if repo_name not in os_system.installed_apps:
                    os_system.installed_apps[repo_name] = {
                        "repo_url": repo_url,
                        "versions": {}
                    }
                os_system.installed_apps[repo_name]['versions'][release['name']] = {
                    "files": [asset['name']],
                    "installed_at": str(datetime.now()),
                    "latest_version": release['name']
                }
                os_system.save_installed_apps()
                return True
        print(color("Приложение не найдено в QDUGUI!", Colors.FAIL))
        return False
    except Exception as e:
        print(color(f"Ошибка: {e}", Colors.FAIL))
        return False

def sudo_required(cmd):
    sudo_cmds = [
        "getfrom", "getapp", "uninstall", "getupdate", "clone", "zip", "unzip", "exit", "quit",
        "service", "systemctl", "history", "clean", "search", "find", "grep", "vault", "bookmark"
    ]
    return any(cmd.startswith(c) for c in sudo_cmds)

UNKNOWN_SOURCES_FILE = os.path.join(FS["ETC_DIR"], "unknown_sources.json")

def load_unknown_sources():
    if os.path.exists(UNKNOWN_SOURCES_FILE):
        try:
            with open(UNKNOWN_SOURCES_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_unknown_sources(sources):
    with open(UNKNOWN_SOURCES_FILE, "w") as f:
        json.dump(sources, f, indent=4)

def check_unknown_sources(os_system):
    known_apps = set()
    for repo, data in os_system.installed_apps.items():
        for version in data["versions"].values():
            for f in version["files"]:
                if f.startswith("zip:"):
                    known_apps.add(f[4:])
                else:
                    known_apps.add(f)
    apps_in_dir = set(os.listdir(APPS_DIR))
    unknown_sources = load_unknown_sources()
    unknown = [app for app in apps_in_dir if app not in known_apps and app not in unknown_sources]
    if unknown:
        print(color("Обнаружены приложения из неизвестных источников:", Colors.WARNING))
        keep_list = []
        for app in unknown:
            while True:
                resp = input(f"Оставить {app}? (y/n): ").lower()
                if resp == "y":
                    keep_list.append(app)
                    break
                elif resp == "n":
                    try:
                        os.remove(os.path.join(APPS_DIR, app))
                        print(color(f"{app} удален.", Colors.OKGREEN))
                    except Exception as e:
                        print(color(f"Ошибка при удалении {app}: {e}", Colors.FAIL))
                    break
        if keep_list:
            unknown_sources_now = load_unknown_sources()
            unknown_sources_now.extend([a for a in keep_list if a not in unknown_sources_now])
            save_unknown_sources(unknown_sources_now)

def service_command(cmd_args, os_system):
    if len(cmd_args) < 3:
        print(color("Пример: sudo service <service> <start|stop|restart|status>", Colors.WARNING))
        return
    _, service, action = cmd_args[:3]
    services = os_system.services
    if service not in services:
        print(color("Служба не найдена!", Colors.FAIL))
        return
    if action == "start":
        services[service]["status"] = "running"
        print(color(f"Служба {service} запущена.", Colors.OKGREEN))
    elif action == "stop":
        services[service]["status"] = "stopped"
        print(color(f"Служба {service} остановлена.", Colors.WARNING))
    elif action == "restart":
        services[service]["status"] = "running"
        print(color(f"Служба {service} перезапущена.", Colors.OKGREEN))
    elif action == "status":
        st = services[service]["status"]
        enabled = "автозапуск: " + ("включен" if services[service]["enabled"] else "отключен")
        print(color(f"Статус службы {service}: {st} ({enabled})", Colors.OKBLUE))
    else:
        print(color("Неизвестное действие", Colors.WARNING))
    save_services(services)

def systemctl_command(cmd_args, os_system):
    if len(cmd_args) < 3:
        print(color("Пример: sudo systemctl <start|stop|restart|enable|disable> <service>", Colors.WARNING))
        return
    _, action, service = cmd_args[:3]
    services = os_system.services
    if service not in services:
        print(color("Служба не найдена!", Colors.FAIL))
        return
    if action == "start":
        services[service]["status"] = "running"
        print(color(f"Служба {service} запущена.", Colors.OKGREEN))
    elif action == "stop":
        services[service]["status"] = "stopped"
        print(color(f"Служба {service} остановлена.", Colors.WARNING))
    elif action == "restart":
        services[service]["status"] = "running"
        print(color(f"Служба {service} перезапущена.", Colors.OKGREEN))
    elif action == "enable":
        services[service]["enabled"] = True
        print(color(f"Автозапуск для {service} включен.", Colors.OKGREEN))
    elif action == "disable":
        services[service]["enabled"] = False
        print(color(f"Автозапуск для {service} отключен.", Colors.WARNING))
    else:
        print(color("Неизвестное действие", Colors.WARNING))
    save_services(services)

def show_history(os_system):
    if not os_system.command_history:
        print(color("История команд пуста", Colors.WARNING))
        return
    print(color("История команд:", Colors.HEADER))
    for i, cmd in enumerate(os_system.command_history[-20:], 1):
        print(f"{i}. {cmd}")

def clean_temp_files():
    temp_dir = FS["TMP_DIR"]
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(color(f"Ошибка при удалении {file_path}: {e}", Colors.FAIL))
    print(color(f"Временные файлы в {temp_dir} очищены", Colors.OKGREEN))

def find_files(directory, pattern):
    matches = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if pattern in filename:
                matches.append(os.path.join(root, filename))
    return matches

def grep_text(pattern, filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if pattern in line:
                    print(f"{filepath}:{i}: {line.strip()}")
    except Exception as e:
        print(color(f"Ошибка при чтении файла {filepath}: {e}", Colors.FAIL))

def search_apps(app_name):
    # Имитация поиска приложений
    print(color(f"Поиск приложений с именем '{app_name}'...", Colors.OKBLUE))
    print(color("1. App1 - Описание приложения 1", Colors.YELLOW))
    print(color("2. App2 - Описание приложения 2", Colors.YELLOW))
    print(color("3. App3 - Описание приложения 3", Colors.YELLOW))
    print(color("(Это демо-функция, реальный поиск не реализован)", Colors.GREY))

def update_app(os_system, repo_name):
    if repo_name not in os_system.installed_apps:
        print(color(f"Приложение {repo_name} не найдено", Colors.FAIL))
        return False
    
    repo_url = os_system.installed_apps[repo_name]["repo_url"]
    current_version = next(iter(os_system.installed_apps[repo_name]["versions"]))
    
    latest_version = get_latest_release_version(repo_url)
    if not latest_version:
        print(color("Не удалось получить информацию о последней версии", Colors.FAIL))
        return False
    
    if latest_version == current_version:
        print(color(f"Приложение {repo_name} уже обновлено до последней версии", Colors.OKGREEN))
        return True
    
    print(color(f"Найдено обновление для {repo_name}: {current_version} -> {latest_version}", Colors.WARNING))
    if download_release(os_system, repo_url, latest_version):
        print(color(f"Приложение {repo_name} успешно обновлено до версии {latest_version}", Colors.OKGREEN))
        return True
    else:
        print(color(f"Не удалось обновить приложение {repo_name}", Colors.FAIL))
        return False

def update_all_apps(os_system):
    if not os_system.installed_apps:
        print(color("Нет установленных приложений для обновления", Colors.WARNING))
        return
    
    updated = 0
    for repo_name in os_system.installed_apps:
        if update_app(os_system, repo_name):
            updated += 1
    
    if updated == 0:
        print(color("Все приложения уже обновлены", Colors.OKGREEN))
    else:
        print(color(f"Обновлено {updated} приложений", Colors.OKGREEN))

def manage_vault(action, *args):
    if not os.path.exists(VAULT_FILE):
        with open(VAULT_FILE, 'w') as f:
            json.dump({}, f)
    
    with open(VAULT_FILE, 'r') as f:
        vault = json.load(f)
    
    if action == "add":
        if len(args) < 2:
            print(color("Использование: vault add <name> <value>", Colors.WARNING))
            return
        name, value = args[0], ' '.join(args[1:])
        vault[name] = encrypt_data(value)
        print(color(f"Запись '{name}' добавлена в хранилище", Colors.OKGREEN))
    elif action == "get":
        if len(args) < 1:
            print(color("Использование: vault get <name>", Colors.WARNING))
            return
        name = args[0]
        if name in vault:
            print(f"{name}: {decrypt_data(vault[name])}")
        else:
            print(color(f"Запись '{name}' не найдена", Colors.FAIL))
    elif action == "list":
        if not vault:
            print(color("Хранилище пусто", Colors.WARNING))
            return
        print(color("Содержимое хранилища:", Colors.HEADER))
        for name in vault:
            print(f"- {name}")
    elif action == "remove":
        if len(args) < 1:
            print(color("Использование: vault remove <name>", Colors.WARNING))
            return
        name = args[0]
        if name in vault:
            del vault[name]
            print(color(f"Запись '{name}' удалена", Colors.OKGREEN))
        else:
            print(color(f"Запись '{name}' не найдена", Colors.FAIL))
    else:
        print(color("Неизвестное действие. Используйте add/get/list/remove", Colors.WARNING))
        return
    
    with open(VAULT_FILE, 'w') as f:
        json.dump(vault, f, indent=4)

def manage_bookmarks(action, *args):
    if not os.path.exists(BOOKMARKS_FILE):
        with open(BOOKMARKS_FILE, 'w') as f:
            json.dump({}, f)
    
    with open(BOOKMARKS_FILE, 'r') as f:
        bookmarks = json.load(f)
    
    if action == "add":
        if len(args) < 2:
            print(color("Использование: bookmark add <name> <path>", Colors.WARNING))
            return
        name, path = args[0], args[1]
        if not os.path.exists(path):
            print(color(f"Путь {path} не существует", Colors.FAIL))
            return
        bookmarks[name] = path
        print(color(f"Закладка '{name}' добавлена", Colors.OKGREEN))
    elif action == "go":
        if len(args) < 1:
            print(color("Использование: bookmark go <name>", Colors.WARNING))
            return
        name = args[0]
        if name in bookmarks:
            os.chdir(bookmarks[name])
            print(color(f"Переход в {bookmarks[name]}", Colors.OKGREEN))
        else:
            print(color(f"Закладка '{name}' не найдена", Colors.FAIL))
    elif action == "list":
        if not bookmarks:
            print(color("Нет сохраненных закладок", Colors.WARNING))
            return
        print(color("Сохраненные закладки:", Colors.HEADER))
        for name, path in bookmarks.items():
            print(f"{name}: {path}")
    elif action == "remove":
        if len(args) < 1:
            print(color("Использование: bookmark remove <name>", Colors.WARNING))
            return
        name = args[0]
        if name in bookmarks:
            del bookmarks[name]
            print(color(f"Закладка '{name}' удалена", Colors.OKGREEN))
        else:
            print(color(f"Закладка '{name}' не найдена", Colors.FAIL))
    else:
        print(color("Неизвестное действие. Используйте add/go/list/remove", Colors.WARNING))
        return
    
    with open(BOOKMARKS_FILE, 'w') as f:
        json.dump(bookmarks, f, indent=4)

def convert_file(input_file, output_format):
    try:
        if not os.path.exists(input_file):
            print(color(f"Файл {input_file} не найден", Colors.FAIL))
            return False
        
        output_file = os.path.splitext(input_file)[0] + f".{output_format.lower()}"
        
        if input_file.endswith('.csv') and output_format.upper() == 'XLSX':
            df = pd.read_csv(input_file)
            df.to_excel(output_file, index=False)
            print(color(f"Файл преобразован: {output_file}", Colors.OKGREEN))
            return True
        elif input_file.endswith('.md') and output_format.upper() == 'HTML':
            with open(input_file, 'r') as f:
                md_text = f.read()
            html = markdown.markdown(md_text)
            with open(output_file, 'w') as f:
                f.write(html)
            print(color(f"Файл преобразован: {output_file}", Colors.OKGREEN))
            return True
        elif input_file.endswith('.txt') and output_format.upper() == 'PDF':
            # Имитация преобразования, так как для реального PDF нужна дополнительная библиотека
            print(color(f"Файл {input_file} будет преобразован в PDF (имитация)", Colors.WARNING))
            return False
        else:
            print(color("Неподдерживаемый формат преобразования", Colors.FAIL))
            return False
    except Exception as e:
        print(color(f"Ошибка при преобразовании файла: {e}", Colors.FAIL))
        return False

def uninstall_app_file(app_file):
    """
    Удаляет указанный файл приложения из папки usr/apps
    """
    file_path = os.path.join(APPS_DIR, app_file)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(color(f"Приложение {app_file} успешно удалено.", Colors.OKGREEN))
        return True
    else:
        print(color(f"Файл {app_file} не найден в usr/apps.", Colors.FAIL))
        return False

def get_cpu_temp():
    try:
        if platform.system() == "Linux":
            temp = psutil.sensors_temperatures()['coretemp'][0].current
            return f"{temp}°C"
        else:
            return "Недоступно на этой платформе"
    except:
        return "Неизвестно"

def start_web_server(port=8000):
    try:
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(color(f"HTTP сервер запущен на порту {port}", Colors.OKGREEN))
            print(color("Откройте http://localhost:8000 в браузере", Colors.OKBLUE))
            print(color("Для остановки сервера нажмите Ctrl+C", Colors.WARNING))
            httpd.serve_forever()
    except Exception as e:
        print(color(f"Ошибка при запуске сервера: {e}", Colors.FAIL))

global_os_system = None

def main():

    global global_os_system
    
    

    os_system = InteriumOS()

    global_os_system = os_system
    
    
    print(color(f"{os_system.system_config['system_name']} загружается...", Colors.HEADER))
    time.sleep(0.5)
    print(color(f"Версия: {os_system.system_config['version']}", Colors.OKCYAN))
    time.sleep(0.3)
    print(color(f"RAM: {os_system.system_config['ram']}", Colors.OKCYAN))
    print(color(f"ROM: {os_system.system_config['rom']}", Colors.OKCYAN))
    time.sleep(0.5)
    print(color(f"Текущая директория: {os_system.current_dir}", Colors.GREY))
    time.sleep(1)
    check_unknown_sources(os_system)
    command_registry = {}
    load_boot_scripts(os_system, command_registry, command_args_info)

    os_system.login()

    cls()
    while True:
        try:
            prompt = f"{color(os_system.current_user, Colors.OKGREEN)}@{color(os_system.system_config['system_name'], Colors.OKCYAN)} $ "
            command = input(prompt).strip()
            if not command:
                continue
            
            # Добавляем команду в историю
            os_system.command_history.append(command)
            os_system.save_history()

            cmd_name = command.split()[0]
            if cmd_name in command_registry:
                # Передаем всю строку в обработчик
                command_registry[cmd_name](command, os_system)
                continue

            # Проверка --args
            if command.endswith(" --args"):
                cmd_base = command.rsplit(" ", 1)[0]
                if cmd_base in command_args_info:
                    print(color(f"Аргументы для команды '{cmd_base}':", Colors.HEADER))
                    print(command_args_info[cmd_base])
                else:
                    print(color(f"Нет сведений об аргументах для команды '{cmd_base}'", Colors.WARNING))
                continue

            if command == "whoami":
                print(os_system.current_user)
                continue

            # Проверяем, есть ли такая команда в registry
            cmd_name = command.split()[0]
            if cmd_name in command_registry:
                command_registry[cmd_name](command, os_system)
                continue

            is_sudo = False
            raw_cmd = command
            if command.startswith("sudo "):
                is_sudo = True
                command = command[len("sudo "):]

            # echo
            if command.startswith("echo "):
                print(command[5:])
                continue

            if command.endswith("--help"):
                print(color("Описание отсутствует.", Colors.YELLOW))
                continue

            if command.startswith("ping "):
                host = command.split()[1]
                ping(host, os_system)
                continue

            if command == "uptime":
                seconds = int(time.time() - os_system.boot_time)
                h = seconds // 3600
                m = (seconds % 3600) // 60
                s = seconds % 60
                print(f"Uptime: {h}ч {m}м {s}с")
                continue

            if command in ("quit", "exit"):
                if os_system.is_root or is_sudo:
                    print(color("Выход из Interium...", Colors.HEADER))
                sys.exit(0)

            if command.startswith("date"):
                parts = command.split()
                if "--set" in parts:
                    try:
                        i = parts.index("--set")
                        newdate = " ".join(parts[i+1:i+3])
                        # Здесь имитация, просто сообщаем пользователю (или используем встроенную функцию если под root)
                        print(f"Дата/время установлены на: {newdate} (имитация)")
                    except Exception:
                        print("Использование: date --set YYYY-MM-DD HH:MM:SS")
                else:
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"Текущая дата и время: {now}")
                continue

            if command == "help":
                cls()
                print(color("Доступные команды:", Colors.HEADER))
                print(color("help", Colors.YELLOW) + " - " + color("Список команд", Colors.YELLOW))
                print(color("sys", Colors.YELLOW) + " - " + color("Информация о системе", Colors.YELLOW))
                print(color("fm", Colors.YELLOW) + " - " + color("Файловый менеджер", Colors.YELLOW))
                print(color("apps", Colors.YELLOW) + " - " + color("Список приложений", Colors.YELLOW))
                print(color("run", Colors.YELLOW) + " <app> - " + color("Запустить приложение", Colors.YELLOW))
                print(color("clone", Colors.YELLOW) + " <git-url> - " + color("Клонировать git репозиторий", Colors.YELLOW))
                print(color("zip", Colors.YELLOW) + " <source> <target.zip> - " + color("Создать zip архив", Colors.YELLOW))
                print(color("unzip", Colors.YELLOW) + " <file.zip> [target_dir] - " + color("Распаковать zip архив", Colors.YELLOW))
                print(color("getfrom", Colors.YELLOW) + " <repo_url> [release] - " + color("Установить приложение", Colors.YELLOW))
                print(color("getlist", Colors.YELLOW) + " <repo_url> - " + color("Показать все релизы в репозитории", Colors.YELLOW))
                print(color("getupdate interium", Colors.YELLOW) + " [version] - " + color("Обновить ядро системы", Colors.YELLOW))
                print(color("getupdate interium --check", Colors.YELLOW) + " - " + color("Проверить обновления", Colors.YELLOW))
                print(color("getupdate <repo>", Colors.YELLOW) + " - " + color("Обновить приложение", Colors.YELLOW))
                print(color("getupdate all", Colors.YELLOW) + " - " + color("Обновить все приложения", Colors.YELLOW))
                print(color("installed", Colors.YELLOW) + " - " + color("Список установленных приложений", Colors.YELLOW))
                print(color("uninstall", Colors.YELLOW) + " <repo> [version] - " + color("Удалить приложение", Colors.YELLOW))
                print(color("getapp", Colors.YELLOW) + " <AppName> - " + color("Установить приложение из QDUGUI", Colors.YELLOW))
                print(color("service", Colors.YELLOW) + " <service> <start|stop|restart|status> - " + color("Управление службой", Colors.YELLOW))
                print(color("systemctl", Colors.YELLOW) + " <start|stop|restart|enable|disable> <service> - " + color("Управление автозапуском службы", Colors.YELLOW))
                print(color("settings", Colors.YELLOW) + " - " + color("Настройки системы", Colors.YELLOW))
                print(color("history", Colors.YELLOW) + " - " + color("История команд", Colors.YELLOW))
                print(color("find", Colors.YELLOW) + " <dir> <name> - " + color("Поиск файлов по имени", Colors.YELLOW))
                print(color("grep", Colors.YELLOW) + " <text> <file> - " + color("Поиск текста в файле", Colors.YELLOW))
                print(color("search", Colors.YELLOW) + " <app> - " + color("Поиск приложений", Colors.YELLOW))
                print(color("clean", Colors.YELLOW) + " - " + color("Очистка временных файлов", Colors.YELLOW))
                print(color("vault", Colors.YELLOW) + " <add/get/list/remove> - " + color("Управление парольным хранилищем", Colors.YELLOW))
                print(color("bookmark", Colors.YELLOW) + " <add/go/list/remove> - " + color("Управление закладками", Colors.YELLOW))
                print(color("convert", Colors.YELLOW) + " <file> <format> - " + color("Конвертация файлов", Colors.YELLOW))
                print(color("temp", Colors.YELLOW) + " - " + color("Температура CPU", Colors.YELLOW))
                print(color("server", Colors.YELLOW) + " [port] - " + color("Запуск веб-сервера", Colors.YELLOW))
                print(color("cls", Colors.YELLOW) + " - " + color("Очистить экран", Colors.YELLOW))
                print(color("ping", Colors.YELLOW) + " <host> - " + color("Пинговать адрес", Colors.YELLOW))
                print(color("echo", Colors.YELLOW) + " <msg> - " + color("Вывести сообщение", Colors.YELLOW))
                print(color("quit/exit", Colors.YELLOW) + " - " + color("Выход", Colors.YELLOW))
                continue

            if command == "sys":
                cls()
                print(color(f"Система: {os_system.system_config['system_name']}", Colors.OKCYAN))
                print(color(f"Версия: {os_system.system_config['version']}", Colors.OKCYAN))
                print(color(f"Пользователь: {os_system.current_user}", Colors.OKCYAN))
                print(color(f"Профиль: {os_system.current_profile}", Colors.OKCYAN))
                print(color(f"RAM: {os_system.system_config['ram']}", Colors.OKCYAN))
                print(color(f"ROM: {os_system.system_config['rom']}", Colors.OKCYAN))
                print(color(f"ОС: {platform.system()} {platform.release()}", Colors.OKCYAN))
                print(color(f"Текущая директория: {os.getcwd()}", Colors.GREY))
                continue

            if command == "fm":
                file_manager()
                cls()
                continue

            if command == "apps":
                cls()
                apps = list_py_apps()
                if apps:
                    print(color("Доступные приложения:", Colors.HEADER))
                    for app in apps:
                        print(color(f"- {app}", Colors.OKGREEN))
                else:
                    print(color("Приложения не найдены!", Colors.WARNING))
                continue

            if command == "apps --check":
                cls()
                list_installed_apps(os_system, check_updates=True)
                continue

            if command.startswith("run "):
                app_name = command.split()[1]
                run_py_app(app_name)
                continue

            if sudo_required(command.split()[0]):
                if not (os_system.is_root or is_sudo):
                    print(color("Для выполнения этой команды требуются root-права. Используйте sudo.", Colors.WARNING))
                    continue

            if command.startswith("clone "):
                url = command.split()[1]
                print(color(url, Colors.LIGHTBLUE))
                clone_repo(url, os_system)
                continue

            if command.startswith("zip "):
                parts = command.split()
                source = parts[1]
                target = parts[2]
                print(color(target, Colors.LIGHTBLUE))
                create_zip(source, target)
                continue

            if command.startswith("unzip "):
                parts = command.split()
                zip_file = parts[1]
                target_dir = parts[2] if len(parts) > 2 else None
                print(color(zip_file, Colors.LIGHTBLUE))
                extract_zip(zip_file, target_dir)
                continue

            if command.startswith("getfrom "):
                parts = command.split()
                repo_url = parts[1]
                print(color(repo_url, Colors.LIGHTBLUE))
                release_name = parts[2] if len(parts) > 2 else None
                print(color(f"Установка из {repo_url}...", Colors.OKBLUE))
                if download_release(os_system, repo_url, release_name):
                    print(color("Установка завершена успешно!", Colors.OKGREEN))
                else:
                    print(color("Не удалось установить приложение", Colors.FAIL))
                continue

            if command.startswith("getlist "):
                repo_url = command.split()[1]
                print(color(repo_url, Colors.LIGHTBLUE))
                get_releases_list(repo_url, os_system)
                continue

            if command == "getupdate interium --check":
                check_for_updates(os_system)
                continue

            if command.startswith("getupdate interium"):
                parts = command.split()
                version = parts[2] if len(parts) > 2 else None
                if update_interium(os_system, version):
                    print(color("Система успешно обновлена! Пожалуйста, перезапустите систему.", Colors.OKGREEN))
                    sys.exit(0)
                else:
                    print(color("Не удалось обновить систему", Colors.FAIL))
                continue

            if command.startswith("getupdate "):
                parts = command.split()
                if len(parts) == 1:
                    print(color("Укажите имя репозитория или 'all'", Colors.WARNING))
                    continue
                repo_name = parts[1]
                if repo_name == "all":
                    update_all_apps(os_system)
                else:
                    update_app(os_system, repo_name)
                continue

            if command == "installed":
                cls()
                list_installed_apps(os_system)
                continue

            if command.startswith("uninstall "):
                parts = command.split()
                if len(parts) > 1 and parts[1] == "--list":
                    apps = list_py_apps()
                    if apps:
                        print(color("Доступные для удаления приложения:", Colors.HEADER))
                        for app in apps:
                            print(color(f"- {app}", Colors.OKGREEN))
                    else:
                        print(color("Нет приложений для удаления!", Colors.WARNING))
                    continue

                app_file = parts[1] if len(parts) > 1 else None
                if not app_file:
                    print(color("Укажите имя приложения для удаления. Используйте 'uninstall --list' чтобы увидеть список.", Colors.WARNING))
                    continue
                if uninstall_app_file(app_file):
                    print(color("Удаление завершено.", Colors.OKGREEN))
                else:
                    print(color("Не удалось удалить приложение.", Colors.FAIL))
                continue

            if command.startswith("getapp "):
                app_name = command.split()[1]
                print(color(f"Запрос установки {app_name} из QDUGUI...", Colors.OKBLUE))
                if get_app_from_qdugui(app_name, os_system):
                    print(color("Приложение успешно установлено!", Colors.OKGREEN))
                else:
                    print(color("Не удалось установить приложение", Colors.FAIL))
                continue

            if command.startswith("service "):
                service_command(command.split(), os_system)
                continue

            if command.startswith("systemctl "):
                systemctl_command(command.split(), os_system)
                continue

            if command == "settings":
                system_settings(os_system)
                cls()
                continue

            if command == "history":
                show_history(os_system)
                continue

            if command.startswith("find "):
                parts = command.split()
                if len(parts) < 3:
                    print(color("Использование: find <dir> <name>", Colors.WARNING))
                    continue
                directory, pattern = parts[1], parts[2]
                if not os.path.exists(directory):
                    print(color(f"Директория {directory} не существует", Colors.FAIL))
                    continue
                print(color(f"Поиск файлов с '{pattern}' в {directory}...", Colors.OKBLUE))
                matches = find_files(directory, pattern)
                if matches:
                    print(color("Найдены файлы:", Colors.HEADER))
                    for match in matches:
                        print(match)
                else:
                    print(color("Файлы не найдены", Colors.WARNING))
                continue

            if command.startswith("grep "):
                parts = command.split()
                if len(parts) < 3:
                    print(color("Использование: grep <text> <file>", Colors.WARNING))
                    continue
                text, filepath = ' '.join(parts[1:-1]), parts[-1]
                if not os.path.exists(filepath):
                    print(color(f"Файл {filepath} не найден", Colors.FAIL))
                    continue
                print(color(f"Поиск '{text}' в {filepath}...", Colors.OKBLUE))
                grep_text(text, filepath)
                continue

            if command.startswith("search "):
                app_name = command.split()[1]
                search_apps(app_name)
                continue

            if command == "clean":
                clean_temp_files()
                continue

            if command.startswith("vault "):
                parts = command.split()
                if len(parts) < 2:
                    print(color("Использование: vault <add/get/list/remove> [args]", Colors.WARNING))
                    continue
                action = parts[1]
                manage_vault(action, *parts[2:])
                continue

            if command.startswith("bookmark "):
                parts = command.split()
                if len(parts) < 2:
                    print(color("Использование: bookmark <add/go/list/remove> [args]", Colors.WARNING))
                    continue
                action = parts[1]
                manage_bookmarks(action, *parts[2:])
                continue

            if command.startswith("convert "):
                parts = command.split()
                if len(parts) < 3:
                    print(color("Использование: convert <file> <format>", Colors.WARNING))
                    continue
                input_file, output_format = parts[1], parts[2]
                convert_file(input_file, output_format)
                continue

            if command == "temp":
                print(color(f"Температура CPU: {get_cpu_temp()}", Colors.OKCYAN))
                continue

            if command.startswith("server"):
                parts = command.split()
                port = int(parts[1]) if len(parts) > 1 else 8000
                start_web_server(port)
                continue

            if command == "cls":
                cls()
                continue

            print(color(f"Неизвестная команда: {command}. Введите 'help' для списка команд.", Colors.WARNING))

        except KeyboardInterrupt:
            print(color("\nДля выхода введите 'quit' или 'exit'", Colors.WARNING))
        except Exception as e:
            print(color(f"Ошибка: {e}", Colors.FAIL))

if __name__ == "__main__":
    main()