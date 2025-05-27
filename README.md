# 🚀 Interium KERNEL

![INTERIUMLOGO](https://github.com/user-attachments/assets/9580ee5c-2191-4cfb-8a52-6164384a2779)


> **Interium OS** — Консольное ядро псевдо системы interium, полностью кастомизированая система!

---

## ✨ Возможности

- 👤 Многопользовательская система (root и обычные пользователи)
- 🗂️ Домашние директории и профили
- 🧩 Установка приложений из GitHub-релизов (и собственного каталога QDUGUI)
- 📦 Список и удаление установленных приложений
- 🔧 Псевдослужбы: service, systemctl, автозапуск
- 💾 Файловый менеджер, архиватор (zip/unzip), git clone
- 🌐 ping, обновление ядра, настройка системы
- 🎨 Приятный CLI-интерфейс с цветами и прогресс-барами

---

## 🚀 Быстрый старт

```bash
# 1. Склонировать репозиторий
git clone https://github.com/ShadowFlash900/INTERIUMOS.git
cd INTERIUMOS

# 2. Запустить ядро
python3 interium.py
```

---

## 📦 Приложения и установка

**Установка приложения из каталога QDUGUI:**
```bash
sudo getapp JustCalculator
```

**Установка из любого GitHub-репозитория (релиза):**
```bash
sudo getfrom https://github.com/USER/REPO RELEASE_NAME
```
> Используйте флаг `--system`, чтобы установить рядом с ядром:  
> `sudo getfrom https://github.com/USER/REPO RELEASE_NAME --system`

**Просмотр списка доступных релизов:**
```bash
getlist https://github.com/USER/REPO
```

---

## 🛠️ Основные команды

| Команда       | Описание                                    |
|:--------------|:--------------------------------------------|
| `help`        | Список всех команд                          |
| `apps`        | Список установленных приложений             |
| `run <app>`   | Запустить Python-приложение                 |
| `getapp ...`  | Установить из каталога QDUGUI               |
| `getfrom ...` | Установить из GitHub-репозитория            |
| `uninstall ...`| Удалить приложение                         |
| `clone ...`   | Клонировать репозиторий Git                 |
| `zip ...`     | Заархивировать файл/папку                   |
| `unzip ...`   | Распаковать архив                           |
| `service ...` | Управление службой                          |
| `systemctl ...`| Автозапуск/старт/стоп службы               |
| `ping ...`    | Проверить доступность адреса                 |
| `settings`    | Настройки системы, управление пользователями |
| `cls`         | Очистить экран                              |

---

## 🖼️ Скриншоты

![image](https://github.com/user-attachments/assets/5e01f30c-e133-44f7-9416-1049d400972c)

![image](https://github.com/user-attachments/assets/d10e3d9c-10a8-42f0-a8f3-ae3978d888e7)


---

## 💡 FAQ

- **Где приложения?**  
  В папке `home/apps` после установки.

- **Как добавить своё приложение?**  
  Опубликуйте его как релиз на GitHub и установите через `getfrom`.

- **Ядро обновляется?**  
  Да! Используйте `getupdate interium --check` и `sudo getupdate interium`.

---

## 🛡️ Лицензия

[MIT License](LICENSE)

---

> © ShadowFlash900, 2025  
> [GitHub](https://github.com/ShadowFlash900/INTERIUMOS)
