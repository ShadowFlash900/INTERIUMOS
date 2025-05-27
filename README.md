# 🚀 Interium KERNEL

![Interium OS Logo](https://raw.githubusercontent.com/ShadowFlash900/INTERIUMOS/main/docs/logo.png)

> **Interium OS** — современная консольная "операционная система" на Python с поддержкой приложений, системой пользователей, профилей, пакетным менеджером, сервисами и множеством инструментов для эмуляции настоящей ОС в терминале.

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

![term1](https://raw.githubusercontent.com/ShadowFlash900/INTERIUMOS/main/docs/screenshot1.png)
![term2](https://raw.githubusercontent.com/ShadowFlash900/INTERIUMOS/main/docs/screenshot2.png)

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
