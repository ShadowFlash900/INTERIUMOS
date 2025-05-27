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
}
APPS_DIR = os.path.join(FS["USR_DIR"], "apps")
INSTALLED_APPS_FILE = os.path.join(FS["USR_DIR"], "installed_apps.json")
CONFIG_FILE = os.path.join(FS["ETC_DIR"], "system_config.json")
USER_FILE = os.path.join(FS["ETC_DIR"], "users.json")
PROFILES_FILE = os.path.join(FS["ETC_DIR"], "profiles.json")
SERVICES_FILE = os.path.join(FS["ETC_DIR"], "services.json")
INTERIUM_UPDATE_URL = "https://github.com/ShadowFlash900/INTERIUMOS"
QDUGUI_URL = "https://github.com/ShadowFlash900/QDUGUI"

def create_fs():
    for d in FS.values():
        os.makedirs(d, exist_ok=True)
    os.makedirs(APPS_DIR, exist_ok=True)

def load_services():
    # Только AdaptiveNetwork сервис
    default = {
        "AdaptiveNetwork": {"status": "running", "enabled": True}
    }
    if os.path.exists(SERVICES_FILE):
        try:
            with open(SERVICES_FILE, "r") as f:
                return json.load(f)
        except:
            return default.copy()
    return default.copy()

def save_services(services):
    with open(SERVICES_FILE, "w") as f:
        json.dump(services, f, indent=4)

def adaptive_network_required(os_system):
    return os_system.services.get("AdaptiveNetwork", {}).get("status", "stopped") != "running"

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
        self.create_dirs([FS["HOME_DIR"], APPS_DIR, FS["ETC_DIR"], FS["TMP_DIR"], FS["BOOT_DIR"], FS["ROOT_HOME"], FS["USR_DIR"]])
        self.first_run_check()

    def create_dirs(self, dirs):
        for directory in dirs:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

    def load_config(self):
        default_config = {
            "version": "1.5",
            "ram": "1VGB",
            "rom": "1VGB",
            "system_name": "Interium OS",
            "created_at": str(datetime.now()),
            "default_profile": "default"
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
                "password": "admin",
                "permissions": "full",
                "home_dir": FS["ROOT_HOME"]
            }
        }
        if os.path.exists(USER_FILE):
            try:
                with open(USER_FILE, "r") as f:
                    users = json.load(f)
                    for user, data in users.items():
                        user_dir = data.get("home_dir", os.path.join(FS["HOME_DIR"], user))
                        if not os.path.exists(user_dir):
                            os.makedirs(user_dir, exist_ok=True)
                    return users
            except:
                return default_users
        return default_users

    def save_users(self):
        with open(USER_FILE, "w") as f:
            json.dump(self.users, f, indent=4)

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

    def first_run_check(self):
        # Если только admin - предложить создать нового пользователя
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
    print(color("5. Вернуться", Colors.YELLOW))
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
                "installed_at": str(datetime.now())
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

def list_installed_apps(os_system):
    if not os_system.installed_apps:
        print(color("Нет установленных приложений", Colors.WARNING))
        return
    print(color("Установленные приложения:", Colors.HEADER))
    for repo, data in os_system.installed_apps.items():
        print(f"\n{color('Репозиторий:', Colors.OKCYAN)} {repo}")
        print(f"{color('URL:', Colors.LIGHTBLUE)} {data['repo_url']}")
        print(color('Версии:', Colors.YELLOW))
        for version, info in data['versions'].items():
            print(color(f"  {version} (установлено {info['installed_at']})", Colors.OKGREEN))

def uninstall_app(os_system, repo_name, version=None):
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

def get_app_from_qdugui(app_name, os_system):
    if adaptive_network_required(os_system):
        print(color("Сетевая функция отключена! Включите AdaptiveNetwork.", Colors.FAIL))
        return False
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
                    "installed_at": str(datetime.now())
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
        "getfrom", "getapp", "uninstall", "getupdate", "clone", "zip", "unzip", "exit", "quit"
    ]
    return any(cmd.startswith(c) for c in sudo_cmds)

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

def main():
    os_system = InteriumOS()
    print(color(f"{os_system.system_config['system_name']} загружается...", Colors.HEADER))
    time.sleep(0.5)
    print(color(f"Версия: {os_system.system_config['version']}", Colors.OKCYAN))
    time.sleep(0.3)
    print(color(f"RAM: {os_system.system_config['ram']}", Colors.OKCYAN))
    print(color(f"ROM: {os_system.system_config['rom']}", Colors.OKCYAN))
    time.sleep(0.5)
    print(color(f"Текущая директория: {os_system.current_dir}", Colors.GREY))
    time.sleep(1)
    os_system.login()
    cls()
    while True:
        try:
            prompt = f"{color(os_system.current_user, Colors.OKGREEN)}@{color(os_system.system_config['system_name'], Colors.OKCYAN)} $ "
            command = input(prompt).strip()
            if not command:
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

            if command in ("quit", "exit"):
                if os_system.is_root or is_sudo:
                    print(color("Выход из Interium...", Colors.HEADER))
                sys.exit(0)

            if command == "help":
                cls()
                print(color("Доступные команды:", Colors.HEADER))
                print(
                    color("help", Colors.YELLOW) + " - " + color("Список команд", Colors.YELLOW)
                )
                print(
                    color("sys", Colors.YELLOW) + " - " + color("Информация о системе", Colors.YELLOW)
                )
                print(
                    color("fm", Colors.YELLOW) + " - " + color("Файловый менеджер", Colors.YELLOW)
                )
                print(
                    color("apps", Colors.YELLOW) + " - " + color("Список приложений", Colors.YELLOW)
                )
                print(
                    color("run", Colors.YELLOW) + " <app> - " + color("Запустить приложение", Colors.YELLOW)
                )
                print(
                    color("clone", Colors.YELLOW) + " <git-url> - " + color("Клонировать git репозиторий", Colors.YELLOW)
                )
                print(
                    color("zip", Colors.YELLOW) + " <source> <target.zip> - " + color("Создать zip архив", Colors.YELLOW)
                )
                print(
                    color("unzip", Colors.YELLOW) + " <file.zip> [target_dir] - " + color("Распаковать zip архив", Colors.YELLOW)
                )
                print(
                    color("getfrom", Colors.YELLOW) + " <repo_url> [release] - " + color("Установить приложение", Colors.YELLOW)
                )
                print(
                    color("getlist", Colors.YELLOW) + " <repo_url> - " + color("Показать все релизы в репозитории", Colors.YELLOW)
                )
                print(
                    color("getupdate interium", Colors.YELLOW) + " [version] - " + color("Обновить ядро системы", Colors.YELLOW)
                )
                print(
                    color("getupdate interium --check", Colors.YELLOW) + " - " + color("Проверить обновления", Colors.YELLOW)
                )
                print(
                    color("installed", Colors.YELLOW) + " - " + color("Список установленных приложений", Colors.YELLOW)
                )
                print(
                    color("uninstall", Colors.YELLOW) + " <repo> [version] - " + color("Удалить приложение", Colors.YELLOW)
                )
                print(
                    color("getapp", Colors.YELLOW) + " <AppName> - " + color("Установить приложение из QDUGUI", Colors.YELLOW)
                )
                print(
                    color("service", Colors.YELLOW) + " <service> <start|stop|restart|status> - " + color("Управление службой", Colors.YELLOW)
                )
                print(
                    color("systemctl", Colors.YELLOW) + " <start|stop|restart|enable|disable> <service> - " + color("Управление автозапуском службы", Colors.YELLOW)
                )
                print(
                    color("settings", Colors.YELLOW) + " - " + color("Настройки системы", Colors.YELLOW)
                )
                print(
                    color("cls", Colors.YELLOW) + " - " + color("Очистить экран", Colors.YELLOW)
                )
                print(
                    color("ping", Colors.YELLOW) + " <host> - " + color("Пинговать адрес", Colors.YELLOW)
                )
                print(
                    color("echo", Colors.YELLOW) + " <msg> - " + color("Вывести сообщение", Colors.YELLOW)
                )
                print(
                    color("quit/exit", Colors.YELLOW) + " - " + color("Выход", Colors.YELLOW)
                )
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

            if command == "installed":
                cls()
                list_installed_apps(os_system)
                continue

            if command.startswith("uninstall "):
                parts = command.split()
                repo_name = parts[1]
                version = parts[2] if len(parts) > 2 else None
                if uninstall_app(os_system, repo_name, version):
                    print(color("Приложение успешно удалено", Colors.OKGREEN))
                else:
                    print(color("Не удалось удалить приложение", Colors.FAIL))
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