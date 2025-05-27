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

# Конфигурация системы
CONFIG_FILE = "system_config.json"
USER_FILE = "users.json"
PROFILES_FILE = "profiles.json"
HOME_DIR = "home"
APPS_DIR = os.path.join(HOME_DIR, "apps")
INSTALLED_APPS_FILE = os.path.join(HOME_DIR, "installed_apps.json")
INTERIUM_UPDATE_URL = "https://github.com/ShadowFlash900/INTERIUMOS"

class InteriumOS:
    def __init__(self):
        self.current_user = None
        self.current_profile = None
        self.system_config = self.load_config()
        self.users = self.load_users()
        self.profiles = self.load_profiles()
        self.installed_apps = self.load_installed_apps()
        self.current_dir = os.getcwd()
        
        self.create_dirs([HOME_DIR, APPS_DIR])
    
    def create_dirs(self, dirs):
        for directory in dirs:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
    
    def load_config(self):
        default_config = {
            "version": "1.3",
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
                "home_dir": os.path.join(HOME_DIR, "admin")
            }
        }
        
        if os.path.exists(USER_FILE):
            try:
                with open(USER_FILE, "r") as f:
                    users = json.load(f)
                    for user, data in users.items():
                        user_dir = data.get("home_dir", os.path.join(HOME_DIR, user))
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
    
    def login(self):
        cls()
        print(f"{self.system_config['system_name']} v{self.system_config['version']}")
        print("Для выхода введите 'exit'")
        
        while True:
            username = input("Имя пользователя: ")
            if username == "exit":
                sys.exit(0)
            
            if username in self.users:
                password = getpass.getpass("Пароль: ")
                if password == self.users[username]["password"]:
                    self.current_user = username
                    user_dir = self.users[username].get("home_dir", os.path.join(HOME_DIR, username))
                    if not os.path.exists(user_dir):
                        os.makedirs(user_dir, exist_ok=True)
                    os.chdir(user_dir)
                    self.current_dir = user_dir
                    self.current_profile = self.system_config.get("default_profile", "default")
                    print(f"Добро пожаловать, {username} (профиль: {self.current_profile})!")
                    time.sleep(1)
                    return
                else:
                    print("Неверный пароль!")
            else:
                print("Пользователь не найден!")

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
            print(f"Ошибка при запуске приложения: {e}")
    else:
        print(f"Приложение {app_name} не найдено!")

def clone_repo(url):
    try:
        if not shutil.which("git"):
            print("Git не установлен в системе!")
            return False
        
        repo_name = url.split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        
        clone_dir = os.path.join(HOME_DIR, repo_name)
        
        if os.path.exists(clone_dir):
            print(f"Директория {clone_dir} уже существует!")
            return False
        
        subprocess.run(["git", "clone", url, clone_dir], check=True)
        print(f"Репозиторий успешно клонирован в {clone_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при клонировании репозитория: {e}")
        return False
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

def extract_zip(zip_file, target_dir=None):
    if not target_dir:
        target_dir = os.path.dirname(zip_file)
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        print(f"Архив {zip_file} успешно распакован в {target_dir}")
        return True
    except Exception as e:
        print(f"Ошибка при распаковке архива: {e}")
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
        print(f"Архив {zip_name} успешно создан")
        return True
    except Exception as e:
        print(f"Ошибка при создании архива: {e}")
        return False

def file_manager():
    """Простой файловый менеджер с функцией создания txt файлов"""
    cls()
    current_dir = os.getcwd()
    print(f"Файловый менеджер (текущая директория: {current_dir})")
    print("Команды: ls, cd <dir>, mkdir <dir>, touch <file.txt>, rm <file>, exit")
    
    while True:
        cmd = input("fm> ").strip().split()
        if not cmd:
            continue
        
        if cmd[0] == "exit":
            break
        
        elif cmd[0] == "ls":
            print("\nСодержимое директории:")
            for item in os.listdir(current_dir):
                print(f"{'[DIR]' if os.path.isdir(os.path.join(current_dir, item)) else '[FILE]'} {item}")
            print()
        
        elif cmd[0] == "cd" and len(cmd) > 1:
            new_dir = cmd[1]
            try:
                if new_dir == "..":
                    os.chdir("..")
                else:
                    os.chdir(new_dir)
                current_dir = os.getcwd()
                print(f"Текущая директория: {current_dir}")
            except Exception as e:
                print(f"Ошибка: {e}")
        
        elif cmd[0] == "mkdir" and len(cmd) > 1:
            try:
                os.mkdir(cmd[1])
                print(f"Директория {cmd[1]} создана")
            except Exception as e:
                print(f"Ошибка: {e}")
        
        elif cmd[0] == "touch" and len(cmd) > 1:
            try:
                filename = cmd[1]
                if not filename.endswith('.txt'):
                    filename += '.txt'
                
                with open(os.path.join(current_dir, filename), 'w') as f:
                    content = input("Введите содержимое файла (оставьте пустым для создания пустого файла): ")
                    f.write(content)
                print(f"Файл {filename} успешно создан")
            except Exception as e:
                print(f"Ошибка при создании файла: {e}")
        
        elif cmd[0] == "rm" and len(cmd) > 1:
            try:
                target = cmd[1]
                if os.path.isdir(target):
                    shutil.rmtree(target)
                else:
                    os.remove(target)
                print(f"{target} удален")
            except Exception as e:
                print(f"Ошибка: {e}")
        
        else:
            print("Неизвестная команда")

def system_settings():
    cls()
    os_system = InteriumOS()
    print("Настройки системы")
    print("1. Изменить имя системы")
    print("2. Добавить пользователя")
    print("3. Изменить пароль")
    print("4. Управление профилями")
    print("5. Вернуться")
    
    choice = input("Выберите действие: ")
    
    if choice == "1":
        new_name = input("Новое имя системы: ")
        os_system.system_config["system_name"] = new_name
        os_system.save_config()
        print("Имя системы изменено!")
    
    elif choice == "2":
        username = input("Новое имя пользователя: ")
        if username in os_system.users:
            print("Пользователь уже существует!")
        else:
            password = getpass.getpass("Пароль: ")
            confirm = getpass.getpass("Подтвердите пароль: ")
            if password == confirm:
                os_system.users[username] = {
                    "password": password,
                    "permissions": "user",
                    "home_dir": os.path.join(HOME_DIR, username)
                }
                os_system.save_users()
                os.makedirs(os.path.join(HOME_DIR, username), exist_ok=True)
                print("Пользователь создан!")
            else:
                print("Пароли не совпадают!")
    
    elif choice == "3":
        if not os_system.current_user:
            print("Сначала войдите в систему!")
            return
        
        old_pass = getpass.getpass("Текущий пароль: ")
        if old_pass != os_system.users[os_system.current_user]["password"]:
            print("Неверный пароль!")
            return
        
        new_pass = getpass.getpass("Новый пароль: ")
        confirm = getpass.getpass("Подтвердите пароль: ")
        
        if new_pass == confirm:
            os_system.users[os_system.current_user]["password"] = new_pass
            os_system.save_users()
            print("Пароль изменен!")
        else:
            print("Пароли не совпадают!")
    
    elif choice == "4":
        manage_profiles(os_system)

def manage_profiles(os_system):
    while True:
        cls()
        print("Управление профилями")
        print(f"Текущий профиль: {os_system.current_profile}")
        print("1. Создать новый профиль")
        print("2. Переключить профиль")
        print("3. Изменить настройки профиля")
        print("4. Удалить профиль")
        print("5. Назначить профиль по умолчанию")
        print("6. Вернуться")
        
        choice = input("Выберите действие: ")
        
        if choice == "1":
            profile_name = input("Имя нового профиля: ")
            if profile_name in os_system.profiles:
                print("Профиль с таким именем уже существует!")
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
                print(f"Профиль {profile_name} создан!")
            time.sleep(1)
        
        elif choice == "2":
            print("Доступные профили:")
            for profile in os_system.profiles:
                print(f"- {profile}")
            
            profile_name = input("Выберите профиль: ")
            if profile_name in os_system.profiles:
                os_system.current_profile = profile_name
                print(f"Профиль изменен на {profile_name}")
            else:
                print("Профиль не найден!")
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
                print("Настройка изменена!")
            else:
                print("Недопустимое свойство")
            time.sleep(1)
        
        elif choice == "4":
            print("Доступные профили:")
            for profile in os_system.profiles:
                print(f"- {profile}")
            
            profile_name = input("Какой профиль удалить? (нельзя удалить текущий): ")
            if profile_name == os_system.current_profile:
                print("Нельзя удалить текущий профиль!")
            elif profile_name in os_system.profiles:
                del os_system.profiles[profile_name]
                os_system.save_profiles()
                print(f"Профиль {profile_name} удален!")
            else:
                print("Профиль не найден!")
            time.sleep(1)
        
        elif choice == "5":
            print("Доступные профили:")
            for profile in os_system.profiles:
                print(f"- {profile}")
            
            profile_name = input("Какой профиль сделать профилем по умолчанию? ")
            if profile_name in os_system.profiles:
                os_system.system_config["default_profile"] = profile_name
                os_system.save_config()
                print(f"Профиль {profile_name} теперь используется по умолчанию!")
            else:
                print("Профиль не найден!")
            time.sleep(1)
        
        elif choice == "6":
            return
        
        else:
            print("Неверный выбор!")
            time.sleep(1)

def get_repo_name_from_url(url):
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) >= 2:
        return f"{path_parts[0]}_{path_parts[1]}"
    return None

def download_release(os_system, repo_url, release_name=None):
    try:
        if "github.com" not in repo_url:
            print("Поддерживаются только GitHub репозитории")
            return False

        repo_name = get_repo_name_from_url(repo_url)
        if not repo_name:
            print("Неверный URL репозитория")
            return False

        api_url = repo_url.replace("github.com", "api.github.com/repos").replace("/releases", "")
        releases_url = f"{api_url}/releases"

        response = requests.get(releases_url)
        response.raise_for_status()
        releases = response.json()

        if not releases:
            print("В репозитории нет релизов")
            return False

        if release_name is None:
            release = releases[0]
            release_name = release['name']
        else:
            release = next((r for r in releases if r['name'].lower() == release_name.lower()), None)
            if not release:
                print(f"Релиз {release_name} не найден")
                return False

        if repo_name in os_system.installed_apps:
            if release_name in os_system.installed_apps[repo_name]['versions']:
                print(f"Версия {release_name} уже установлена")
                return False

        if not release['assets']:
            print("В релизе нет файлов для скачивания")
            return False

        with tempfile.TemporaryDirectory() as temp_dir:
            installed_files = []
            for asset in release['assets']:
                if asset['name'].endswith(('.py', '.zip', '.exe', '.sh')):
                    print(f"Скачивание {asset['name']}...")
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
        
        print(f"Релиз {release_name} успешно установлен")
        return True

    except Exception as e:
        print(f"Ошибка при скачивании релиза: {e}")
        return False

def get_releases_list(repo_url):
    try:
        if "github.com" not in repo_url:
            print("Поддерживаются только GitHub репозитории")
            return False

        api_url = repo_url.replace("github.com", "api.github.com/repos").replace("/releases", "")
        releases_url = f"{api_url}/releases"

        response = requests.get(releases_url)
        response.raise_for_status()
        releases = response.json()

        if not releases:
            print("В репозитории нет релизов")
            return False

        print(f"\nСписок релизов в {repo_url}:")
        print("-" * 50)
        for i, release in enumerate(releases, 1):
            print(f"\n{i}. {release['name']} ({release['tag_name']})")
            print(f"   Дата: {release['published_at']}")
            print(f"   Автор: {release['author']['login']}")
            print(f"   Описание: {release.get('body', 'нет описания')[:100]}...")
            print(f"   Файлов: {len(release['assets'])}")
            print("-" * 50)

        return True

    except Exception as e:
        print(f"Ошибка при получении списка релизов: {e}")
        return False

def check_for_updates(os_system):
    try:
        api_url = INTERIUM_UPDATE_URL.replace("github.com", "api.github.com/repos")
        releases_url = f"{api_url}/releases/latest"
        
        response = requests.get(releases_url)
        response.raise_for_status()
        latest_release = response.json()
        
        current_version = os_system.system_config["version"]
        latest_version = latest_release["tag_name"]
        
        if latest_version > current_version:
            print(f"Доступно обновление: {latest_version} (текущая версия: {current_version})")
            return latest_version
        else:
            print("У вас установлена последняя версия системы")
            return None
    except Exception as e:
        print(f"Ошибка при проверке обновлений: {e}")
        return None

def update_interium(os_system, version=None):
    try:
        api_url = INTERIUM_UPDATE_URL.replace("github.com", "api.github.com/repos")
        
        if version:
            releases_url = f"{api_url}/releases/tags/{version}"
        else:
            releases_url = f"{api_url}/releases/latest"
        
        response = requests.get(releases_url)
        response.raise_for_status()
        release = response.json()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for asset in release["assets"]:
                if asset["name"] == "interium.py":
                    print("Скачивание нового ядра системы...")
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
                    print(f"Создана резервная копия: {backup_path}")
                    
                    shutil.move(file_path, current_path)
                    print("Ядро системы успешно обновлено!")
                    
                    os_system.system_config["version"] = release["tag_name"]
                    os_system.save_config()
                    
                    return True
        
        print("Файл ядра (interium.py) не найден в релизе")
        return False
    except Exception as e:
        print(f"Ошибка при обновлении системы: {e}")
        return False

def list_installed_apps(os_system):
    if not os_system.installed_apps:
        print("Нет установленных приложений")
        return
    
    print("Установленные приложения:")
    for repo, data in os_system.installed_apps.items():
        print(f"\nРепозиторий: {repo}")
        print(f"URL: {data['repo_url']}")
        print("Версии:")
        for version, info in data['versions'].items():
            print(f"  {version} (установлено {info['installed_at']})")

def uninstall_app(os_system, repo_name, version=None):
    if repo_name not in os_system.installed_apps:
        print(f"Репозиторий {repo_name} не найден в установленных приложениях")
        return False
    
    versions = os_system.installed_apps[repo_name]['versions']
    
    if version is None:
        for ver, info in versions.items():
            for file in info['files']:
                if file.startswith("zip:"):
                    print(f"Файлы из архива {file[4:]} нужно удалить вручную")
                else:
                    file_path = os.path.join(APPS_DIR, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"Удален файл {file}")
        
        del os_system.installed_apps[repo_name]
    else:
        if version not in versions:
            print(f"Версия {version} не найдена для репозитория {repo_name}")
            return False
        
        for file in versions[version]['files']:
            if file.startswith("zip:"):
                print(f"Файлы из архива {file[4:]} нужно удалить вручную")
            else:
                file_path = os.path.join(APPS_DIR, file)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Удален файл {file}")
        
        del versions[version]
        if not versions:
            del os_system.installed_apps[repo_name]
    
    os_system.save_installed_apps()
    print("Удаление завершено")
    return True

def main():
    os_system = InteriumOS()
    
    print(f"{os_system.system_config['system_name']} загружается...")
    time.sleep(0.5)
    print(f"Версия: {os_system.system_config['version']}")
    time.sleep(0.3)
    print(f"RAM: {os_system.system_config['ram']}")
    print(f"ROM: {os_system.system_config['rom']}")
    time.sleep(0.5)
    print(f"Текущая директория: {os_system.current_dir}")
    time.sleep(1)
    
    os_system.login()
    cls()
    
    while True:
        try:
            current_dir = os.getcwd()
            prompt = f"{os_system.current_user}@{os_system.system_config['system_name']}:{current_dir} [{os_system.current_profile}]$ "
            command = input(prompt).strip()
            
            if not command:
                continue
            
            elif command == "quit" or command == "exit":
                sys.exit(0)
            
            elif command == "help":
                cls()
                print("Доступные команды:")
                print("help - Список команд")
                print("sys - Информация о системе")
                print("fm - Файловый менеджер")
                print("apps - Список приложений")
                print("run <app> - Запустить приложение")
                print("clone <git-url> - Клонировать git репозиторий")
                print("zip <source> <target.zip> - Создать zip архив")
                print("unzip <file.zip> [target_dir] - Распаковать zip архив")
                print("getfrom <repo_url> [release] - Установить приложение")
                print("getlist <repo_url> - Показать все релизы в репозитории")
                print("getupdate interium [version] - Обновить ядро системы")
                print("getupdate interium --check - Проверить обновления")
                print("installed - Список установленных приложений")
                print("uninstall <repo> [version] - Удалить приложение")
                print("settings - Настройки системы")
                print("cls - Очистить экран")
                print("quit/exit - Выход")
            
            elif command == "sys":
                cls()
                print(f"Система: {os_system.system_config['system_name']}")
                print(f"Версия: {os_system.system_config['version']}")
                print(f"Пользователь: {os_system.current_user}")
                print(f"Профиль: {os_system.current_profile}")
                print(f"RAM: {os_system.system_config['ram']}")
                print(f"ROM: {os_system.system_config['rom']}")
                print(f"ОС: {platform.system()} {platform.release()}")
                print(f"Текущая директория: {current_dir}")
            
            elif command == "fm":
                file_manager()
                cls()
            
            elif command == "apps":
                cls()
                apps = list_py_apps()
                if apps:
                    print("Доступные приложения:")
                    for app in apps:
                        print(f"- {app}")
                else:
                    print("Приложения не найдены!")
            
            elif command.startswith("run ") and len(command.split()) > 1:
                app_name = command.split()[1]
                run_py_app(app_name)
            
            elif command.startswith("clone ") and len(command.split()) > 1:
                url = command.split()[1]
                clone_repo(url)
            
            elif command.startswith("zip ") and len(command.split()) > 2:
                source = command.split()[1]
                target = command.split()[2]
                create_zip(source, target)
            
            elif command.startswith("unzip ") and len(command.split()) > 1:
                zip_file = command.split()[1]
                target_dir = command.split()[2] if len(command.split()) > 2 else None
                extract_zip(zip_file, target_dir)
            
            elif command.startswith("getfrom ") and len(command.split()) > 1:
                parts = command.split()
                repo_url = parts[1]
                release_name = parts[2] if len(parts) > 2 else None
                print(f"Установка из {repo_url}...")
                if download_release(os_system, repo_url, release_name):
                    print("Установка завершена успешно!")
                else:
                    print("Не удалось установить приложение")
            
            elif command.startswith("getlist ") and len(command.split()) > 1:
                repo_url = command.split()[1]
                get_releases_list(repo_url)
            
            elif command == "getupdate interium --check":
                check_for_updates(os_system)
            
            elif command.startswith("getupdate interium"):
                parts = command.split()
                version = parts[2] if len(parts) > 2 else None
                
                if update_interium(os_system, version):
                    print("Система успешно обновлена! Пожалуйста, перезапустите систему.")
                    sys.exit(0)
                else:
                    print("Не удалось обновить систему")
            
            elif command == "installed":
                cls()
                list_installed_apps(os_system)
            
            elif command.startswith("uninstall ") and len(command.split()) > 1:
                parts = command.split()
                repo_name = parts[1]
                version = parts[2] if len(parts) > 2 else None
                if uninstall_app(os_system, repo_name, version):
                    print("Приложение успешно удалено")
                else:
                    print("Не удалось удалить приложение")
            
            elif command == "settings":
                system_settings()
                cls()
            
            elif command == "cls":
                cls()
            
            else:
                print(f"Неизвестная команда: {command}. Введите 'help' для списка команд.")
        
        except KeyboardInterrupt:
            print("\nДля выхода введите 'quit' или 'exit'")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()