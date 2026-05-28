import yaml
from pathlib import Path

# Вычисляем путь к файлу texts.yaml (находится на 2 уровня выше папки utils)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEXTS_PATH = BASE_DIR / "texts.yaml"

def load_texts(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

# Загружаем словарь в переменную TEXTS при импорте модуля
TEXTS = load_texts(TEXTS_PATH)