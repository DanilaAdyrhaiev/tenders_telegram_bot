import os

# Настройки
OUTPUT_FILENAME = "all_project_code.txt"  # Имя итогового файла
ROOT_DIR = "."  # Текущая директория

# Игнорируемые директории и файлы (чтобы не тянуть мусор)
IGNORE_DIRS = {'.venv', '__pycache__', 'backups', '.git'}
IGNORE_EXTENSIONS = {'.pyc', '.pyo', '.pyd', '.sqllite3', '.db', '.log'}

def merge_project_files():
    # Открываем итоговый файл для записи
    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as outfile:
        
        # Обходим все директории
        for root, dirs, files in os.walk(ROOT_DIR):
            # Исключаем ненужные папки "на лету"
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                # Пропускаем сам скрипт и итоговый файл
                if file == OUTPUT_FILENAME or file == os.path.basename(__file__):
                    continue
                
                # Проверяем расширение
                ext = os.path.splitext(file)[1].lower()
                if ext in IGNORE_EXTENSIONS:
                    continue
                
                # Формируем пути
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, ROOT_DIR)
                
                # Подбираем правильный символ комментария в зависимости от расширения
                comment_char = "#"
                if ext in {'.json'}:
                    comment_char = "//"
                
                try:
                    # Читаем содержимое файла
                    with open(file_path, "r", encoding="utf-8") as infile:
                        content = infile.read()
                        
                        # Записываем красивый заголовок с путем
                        outfile.write(f"{comment_char} " + "=" * 50 + "\n")
                        outfile.write(f"{comment_char} PATH: {relative_path}\n")
                        outfile.write(f"{comment_char} " + "=" * 50 + "\n\n")
                        
                        # Записываем сам код
                        outfile.write(content)
                        outfile.write("\n\n\n")
                        
                except Exception as e:
                    print(f"Пропущен файл {relative_path} (ошибка чтения: {e})")

    print(f"✅ Готово! Весь код собран в файл: {OUTPUT_FILENAME}")

if __name__ == "__main__":
    merge_project_files()