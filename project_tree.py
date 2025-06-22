import os
from pathlib import Path

def print_tree(path, prefix='', ignore=None):
    if ignore is None:
        ignore = {'__pycache__', '.venv', '.git', '.idea', '.vscode'}

    try:
        # Фильтрация элементов перед обработкой
        items = sorted([
            item for item in os.listdir(path)
            if item not in ignore
        ])
    except PermissionError:
        return

    pointers = ['├── '] * (len(items) - 1) + ['└── ']
    for pointer, item in zip(pointers, items):
        full_path = os.path.join(path, item)
        if os.path.isdir(full_path):
            print(f"{prefix}{pointer}{item}/")
            extension = '│   ' if pointer == '├── ' else '    '
            print_tree(full_path, prefix + extension, ignore)
        else:
            print(f"{prefix}{pointer}{item}")

root = Path(__file__).parent
print(f"{root.name}/")
print_tree(root)