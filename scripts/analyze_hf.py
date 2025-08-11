import re

with open("content_huggingface.md", "r") as f:
    lines = f.readlines()

print("Анализ структуры ссылок на статьи:")
print("=" * 60)

# Ищем строки с ссылками на блог
for i, line in enumerate(lines[:100]):
    if "huggingface.co/blog/" in line and not "/assets/" in line:
        print(f"\nСтрока {i}: {line[:100]}...")
        if i > 0:
            print(f"Предыдущая: {lines[i-1][:100]}...")
