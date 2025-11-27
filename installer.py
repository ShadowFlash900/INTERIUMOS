import os
import requests
import subprocess
import sys
from urllib.parse import urljoin
from tqdm import tqdm as tqdm_lib

def get_github_tags(repo):
    """Получить список тегов из GitHub репозитория"""
    url = f"https://api.github.com/repos/{repo}/tags"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Ошибка при получении тегов: {response.status_code}")
    return response.json()

def get_latest_release_info(repo):
    """Получить информацию о последнем релизе"""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Ошибка при получении последнего релиза: {response.status_code}")
    return response.json()

def get_release_assets(repo, tag):
    """Получить информацию об ассетах релиза"""
    if tag == "latest":
        url = f"https://api.github.com/repos/{repo}/releases/latest"
    else:
        url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Ошибка при получении релиза: {response.status_code}")
    
    release_data = response.json()
    return release_data['assets'], release_data.get('name', 'Без названия')

def download_file_with_progress(url, filename, folder):
    """Скачать файл с progress bar"""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # Получаем общий размер файла
    total_size = int(response.headers.get('content-length', 0))
    
    filepath = os.path.join(folder, filename)
    with open(filepath, 'wb') as f:
        with tqdm_lib(total=total_size, unit='B', unit_scale=True, desc=filename, ncols=80) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    
    return filepath

def download_raw_github_file(repo, filepath, folder):
    """Скачать сырой файл из GitHub (для LICENSE и README)"""
    url = f"https://raw.githubusercontent.com/{repo}/main/{filepath}"
    filename = os.path.basename(filepath)
    
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise Exception(f"Файл {filename} не найден (статус: {response.status_code})")
    
    total_size = int(response.headers.get('content-length', 0))
    
    filepath_local = os.path.join(folder, filename)
    with open(filepath_local, 'wb') as f:
        with tqdm_lib(total=total_size, unit='B', unit_scale=True, desc=filename, ncols=80) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    
    return filepath_local

def install_requirements_with_progress(requirements_path):
    """Установить зависимости с progress bar"""
    print("\nУстановка зависимостей...")
    
    # Получаем список пакетов для отслеживания прогресса
    with open(requirements_path, 'r', encoding='utf-8') as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"Найдено {len(packages)} пакетов для установки")
    
    successful_installs = 0
    for package in packages:
        print(f"Устанавливается: {package}")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✓ {package} установлен успешно")
            successful_installs += 1
        except subprocess.CalledProcessError as e:
            print(f"✗ Ошибка при установке {package}: {e}")
    
    print(f"\nУспешно установлено: {successful_installs}/{len(packages)} пакетов")

def main():
    repo = "ShadowFlash900/INTERIUMOS"
    
    # Получаем список тегов
    print("Получение списка версий...")
    try:
        tags = get_github_tags(repo)
        latest_release = get_latest_release_info(repo)
    except Exception as e:
        print(f"Ошибка: {e}")
        return

    # Показываем меню выбора с названиями релизов
    print("\nДоступные версии:")
    print(f"1) latest - {latest_release.get('name', 'Последняя версия')}")
    
    for i, tag in enumerate(tags[:10], 2):  # Показываем первые 10 тегов
        tag_name = tag['name']
        # Для тегов получаем информацию о релизе чтобы получить название
        try:
            _, release_name = get_release_assets(repo, tag_name)
            display_name = release_name if release_name != 'Без названия' else tag_name
        except:
            display_name = tag_name
        
        print(f"{i}) {tag_name} - {display_name}")
    
    try:
        choice = int(input("\nВыберите версию (введите номер): "))
        if choice == 1:
            selected_tag = "latest"
            selected_name = latest_release.get('name', 'Последняя версия')
        elif 2 <= choice <= len(tags) + 1:
            selected_tag = tags[choice - 2]['name']
            _, selected_name = get_release_assets(repo, selected_tag)
        else:
            print("Неверный выбор!")
            return
    except ValueError:
        print("Введите число!")
        return

    print(f"\nВыбрана версия: {selected_tag} - {selected_name}")

    # Создаем папку IntOS
    folder = "IntOS"
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Получаем информацию о выбранном релизе
    print(f"\nПолучение информации о релизе...")
    try:
        assets, release_name = get_release_assets(repo, selected_tag)
    except Exception as e:
        print(f"Ошибка: {e}")
        return

    # Скачиваем обязательные файлы (LICENSE и README)
    print("\nСкачивание обязательных файлов...")
    mandatory_files = ["LICENSE", "README.md"]
    for file in mandatory_files:
        try:
            download_raw_github_file(repo, file, folder)
        except Exception as e:
            print(f"Предупреждение: Не удалось скачать {file}: {e}")

    if not assets:
        print("В этом релизе нет дополнительных файлов для скачивания")
    else:
        # Скачиваем все файлы релиза
        print(f"\nСкачивание файлов релиза...")
        downloaded_files = []
        for asset in assets:
            try:
                download_file_with_progress(asset['browser_download_url'], asset['name'], folder)
                downloaded_files.append(asset['name'])
            except Exception as e:
                print(f"Ошибка при скачивании {asset['name']}: {e}")

    # Проверяем наличие requirements.txt
    requirements_path = os.path.join(folder, "requirements.txt")
    if os.path.exists(requirements_path):
        print("\nОбнаружен requirements.txt")
        try:
            install_requirements_with_progress(requirements_path)
            print("Зависимости успешно установлены!")
        except Exception as e:
            print(f"Ошибка при установке зависимостей: {e}")
    else:
        print("\n⚠️  Файл requirements.txt не найден среди скачанных файлов!")
        print("Пропускаем установку зависимостей.")

    print(f"\n✅ Готово! Все файлы сохранены в папке '{folder}'")

if __name__ == "__main__":
    # Проверяем установлен ли tqdm
    try:
        import tqdm
    except ImportError:
        print("Установка tqdm для progress bar...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    
    main()