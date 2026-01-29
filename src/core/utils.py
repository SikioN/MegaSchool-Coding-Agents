import re
import os

def parse_code_blocks(markdown_text: str) -> list[dict]:
    """
    Парсит блоки кода из Markdown текста для извлечения изменений файлов.
    Ожидаемый формат:
    File: `src/main.py`
    ```python
    код...
    ```
    """
    blocks = []
    
    # Паттерн ищет строку 'File: `путь`' и следующий за ней блок кода
    pattern = r"File: `(.*?)`\s*```.*?\n(.*?)```"
    matches = re.finditer(pattern, markdown_text, re.DOTALL)
    
    for match in matches:
        path = match.group(1).strip()
        content = match.group(2)
        blocks.append({"path": path, "content": content})
        
    return blocks

def apply_file_changes(changes: list[dict]):
    """
    Применяет список изменений к файловой системе.
    Создает необходимые директории и перезаписывает файлы.
    """
    for change in changes:
        path = change["path"]
        content = change["content"]
        
        # Обеспечиваем существование директории
        dirname = os.path.dirname(path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        
        with open(path, "w") as f:
            f.write(content)
        print(f"Обновлен файл: {path}")
