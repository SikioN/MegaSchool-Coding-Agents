# Отчет по работе системы Coding Agents

## 1. Ссылки
*   **Репозиторий проекта**: [MegaSchool-Coding-Agents](https://github.com/SikioN/MegaSchool-Coding-Agents)
*   **Тестовый репозиторий (валидация)**: [test-agent-playground](https://github.com/SikioN/test-agent-playground)

## 2. Инструкция по запуску

### Локально
```bash
# Установка
git clone https://github.com/SikioN/MegaSchool-Coding-Agents.git
cd MegaSchool-Coding-Agents
poetry install

# Настройка .env (см. README)
# Запуск Code Agent
poetry run python -m src.main code --issue <ISSUE_URL>
```

### Docker
```bash
docker-compose up -d
```

### GitHub Actions (CI/CD)
Система автоматически работает в репозитории при наличии секретов (`LLM_API_KEY`, `YC_FOLDER_ID`).
*   **Code Agent**: Триггер - лейбл `ready-to-code` на Issue.
*   **Reviewer Agent**: Триггер - создание/обновление PR.
*   **Fix Mode**: Триггер - комментарий `/fix` в PR.

## 3. Выполнение требований

| Требование | Статус | Комментарий |
| :--- | :--- | :--- |
| **SDLC Automation** | ✅ Выполнено | Полный цикл Issue -> Code -> PR -> Review -> Fix реализован. |
| **Code Agent (CLI)** | ✅ Выполнено | CLI поддерживает команды `code`, `review`, `fix`. |
| **AI Reviewer** | ✅ Выполнено | Анализирует Diff, постит комментарии с вердиктом. |
| **Max Iterations** | ✅ Выполнено | Лимит настраивается (default: 5). Агент останавливается при превышении. |
| **GitHub Native** | ✅ Выполнено | Используются только Issues, PR, Actions. |
| **Tech Stack** | ✅ Выполнено | Python 3.11, Poetry, PyGithub, YandexGPT. |
| **Docker** | ✅ Выполнено | `Dockerfile` и `docker-compose.yml` в наличии. |

## 4. Качество и Безопасность (Quality Gates)

*   **Тесты**: Проект настроен на использование `pytest`.
*   **Линтеры**: Добавлены `ruff`, `black` в зависимости.
*   **Безопасность**: Лимиты итераций предотвращают бесконечные циклы. Токены хранятся безопасно.
*   **Branch Protection**: Агенты работают через PR, прямой пуш в main ограничен (рекомендация).

## 5. Метрики (по результатам валидации)

*   **Успешность задач**: 100% (на тестовом сценарии с калькулятором).
*   **Среднее число итераций**: 2 (1 создание + 1 исправление).
*   **CI Pass Rate**: 100%.

## 6. Демонстрация
Пример работы в `test-agent-playground`:
1.  [Issue #1: Implement minimal calculator](https://github.com/SikioN/test-agent-playground/issues/1)
2.  [PR #2: Fix: Issue 1](https://github.com/SikioN/test-agent-playground/pull/2) - Одобрен Reviewer Agent.

---
Автор: Муравья Никита Романович
