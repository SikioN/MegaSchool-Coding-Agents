# Инструкция: Как создать GitHub App

Следуйте этим шагам, чтобы зарегистрировать приложение GitHub App для нашего агента.

## Шаг 1: Начало регистрации
1.  Перейдите в настройки разработчика GitHub:
    **[Developer Settings -> GitHub Apps](https://github.com/settings/apps)**.
2.  Нажмите кнопку **New GitHub App** (справа сверху).

## Шаг 2: Основные настройки (General)
Заполните поля формы:

*   **GitHub App name**: `MegaSchool-Agent-[ВашНик]` (Название должно быть уникальным, добавьте свой ник или цифры).
*   **Homepage URL**: `https://github.com/SikioN/MegaSchool-Coding-Agents` (Можно указать ссылку на ваш репозиторий).
*   **Callback URL** (User authorization callback URL): `https://github.com/SikioN/MegaSchool-Coding-Agents` (Пока не важно, оставьте ссылку на репо, галочку *Expire user authorization tokens* **не** ставьте).
*   **Webhook URL**: `https://example.com/webhook` (Это **временная заглушка**. Позже мы поменяем её на адрес от `ngrok`).
*   **Webhook Secret**: Придумайте сложный пароль. **Запишите его!**

## Шаг 3: Права доступа (Permissions)
Вам нужно развернуть вкладку **Permissions** и выдать права.
Для разделов, которые не указаны ниже, оставьте *No access*.

### Repository permissions (Доступ к репозиторию)
1.  **Actions**: `Read-only` (чтобы видеть результаты тестов).
2.  **Checks**: `Read and write` (чтобы агент мог ставить свои галочки/статусы).
3.  **Contents**: `Read and write` (ГЛАВНОЕ: чтобы агент мог читать код и делать коммиты).
4.  **Issues**: `Read and write` (чтобы отвечать на ишью).
5.  **Metadata**: `Read-only` (выбрано по умолчанию).
6.  **Pull requests**: `Read and write` (чтобы создавать и комментировать PR).

## Шаг 4: Подписка на события (Subscribe to events)
Чуть ниже в разделе **Subscribe to events** поставьте галочки:

1.  [x] **Issue comment** (чтобы слышать команды типа `/fix`).
2.  [x] **Issues** (чтобы реагировать на новые задачи).
3.  [x] **Pull request** (чтобы запускать ревью).
4.  [x] **Workflow run** (желательно, чтобы знать статус CI).

## Шаг 5: Создание и получение ключей
1.  В самом низу выберите **Any account** (доступно всем).
    *   *Важно для хакатона*: Это позволит судьям установить ваше приложение к себе, чтобы проверить его работу (как того требует пункт 8.2 extra.txt).
2.  Нажмите зеленую кнопку **Create GitHub App**.

### После создания:
Вы попадете на страницу настроек созданного приложения.

1.  **App ID**: В самом верху страницы найдите `App ID: 12345...`. **Скопируйте это число**.
2.  **Private keys**: Прокрутите в самый низ. Нажмите **Generate a private key**.
    *   Скачается файл (например, `megaschool-agent.2026-01-30.private-key.pem`).
    *   **Откройте этот файл** в текстовом редакторе и скопируйте ВСЁ содержимое (от `-----BEGIN RSA PRIVATE KEY-----` до `-----END...`).

## Шаг 6: Установка приложения (Install)
1.  В меню слева выберите **Install App**.
2.  Нажмите **Install** напротив вашего аккаунта.
3.  Выберите **Only select repositories** и выберите наш репозиторий `MegaSchool-Coding-Agents`.
4.  Нажмите **Install**.

---

## Итого: Где сохранить ключи
Добавьте полученные данные в файл `.env` в корне проекта (или в GitHub Secrets, если запускаете через Actions):

```ini
GITHUB_APP_ID=...
GITHUB_WEBHOOK_SECRET=...
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
...ваши данные...
-----END RSA PRIVATE KEY-----"
```
