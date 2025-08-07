#!/usr/bin/env python3
"""
Тестовый скрипт для проверки параллельной работы
"""

import sys
import os
import subprocess
from pathlib import Path

def test_help():
    """Тестируем новые опции в help"""
    print("🧪 Тест 1: Проверка help с новыми опциями")
    result = subprocess.run(
        ["bash", "-c", "source venv/bin/activate && python core/main.py --help"],
        capture_output=True,
        text=True,
        cwd="/Users/skynet/Desktop/AI DEV/ainews-clean"
    )
    
    if result.returncode == 0:
        output = result.stdout
        if "--parallel-workers" in output and "--monitor-sessions" in output:
            print("✅ Новые опции найдены в help")
            return True
        else:
            print("❌ Новые опции не найдены в help")
            return False
    else:
        print(f"❌ Ошибка выполнения help: {result.stderr}")
        return False

def test_monitor_sessions():
    """Тестируем команду мониторинга сессий"""
    print("\n🧪 Тест 2: Команда --monitor-sessions")
    result = subprocess.run(
        ["bash", "-c", "source venv/bin/activate && python core/main.py --monitor-sessions"],
        capture_output=True,
        text=True,
        cwd="/Users/skynet/Desktop/AI DEV/ainews-clean"
    )
    
    if result.returncode == 0:
        output = result.stderr  # Логи выводятся в stderr
        if "АКТИВНЫЕ СЕССИИ" in output and "ЗАБЛОКИРОВАННЫЕ СТАТЬИ" in output:
            print("✅ Команда --monitor-sessions работает")
            print(f"📊 Вывод: {len(output.splitlines())} строк")
            return True
        else:
            print("❌ Неожиданный вывод команды --monitor-sessions")
            print(f"stdout: {result.stdout[:200]}...")
            print(f"stderr: {result.stderr[:200]}...")
            return False
    else:
        print(f"❌ Ошибка выполнения --monitor-sessions: {result.stderr}")
        return False

def test_parallel_workers_validation():
    """Тестируем валидацию параметров параллельных воркеров"""
    print("\n🧪 Тест 3: Валидация параметров --parallel-workers")
    
    # Тест невалидного количества воркеров (0)
    result = subprocess.run(
        ["bash", "-c", "source venv/bin/activate && python core/main.py --parallel-workers 0"],
        capture_output=True,
        text=True,
        cwd="/Users/skynet/Desktop/AI DEV/ainews-clean"
    )
    
    # Вывод в stderr 
    output = result.stderr or result.stdout
    
    if result.returncode != 0 and "должно быть больше 0" in output:
        print("✅ Валидация минимального количества воркеров работает")
        
        # Тест слишком большого количества воркеров (>10)
        result = subprocess.run(
            ["bash", "-c", "source venv/bin/activate && python core/main.py --parallel-workers 15"],
            capture_output=True,
            text=True,
            cwd="/Users/skynet/Desktop/AI DEV/ainews-clean"
        )
        
        output = result.stderr or result.stdout
        if result.returncode != 0 and "Максимальное количество воркеров: 10" in output:
            print("✅ Валидация максимального количества воркеров работает")
            return True
        else:
            print("❌ Валидация максимального количества воркеров не работает")
            print(f"Вывод: {output[:200]}")
            return False
    else:
        print("❌ Валидация минимального количества воркеров не работает")
        print(f"Код возврата: {result.returncode}")
        print(f"Вывод: {output[:200]}")
        return False

def test_session_manager_import():
    """Тестируем импорт SessionManager"""
    print("\n🧪 Тест 4: Импорт SessionManager")
    
    result = subprocess.run([
        "bash", "-c", 
        "cd /Users/skynet/Desktop/AI\\ DEV/ainews-clean && source venv/bin/activate && python -c 'from core.session_manager import SessionManager; sm = SessionManager(); print(\"✅ SessionManager импортирован успешно\")'"
    ], 
    capture_output=True,
    text=True,
    cwd="/Users/skynet/Desktop/AI DEV/ainews-clean"
    )
    
    if result.returncode == 0:
        print("✅ SessionManager импортируется корректно")
        return True
    else:
        print(f"❌ Ошибка импорта SessionManager: {result.stderr}")
        return False

def main():
    """Главная функция тестирования"""
    print("=" * 60)
    print("🚀 ТЕСТИРОВАНИЕ ПАРАЛЛЕЛЬНОЙ ПОДДЕРЖКИ")
    print("=" * 60)
    
    # Проверяем что мы в правильной директории
    if not Path("/Users/skynet/Desktop/AI DEV/ainews-clean/core/main.py").exists():
        print("❌ Ошибка: файл main.py не найден")
        print("Убедитесь что скрипт запускается из правильной директории")
        sys.exit(1)
    
    tests = [
        test_help,
        test_monitor_sessions, 
        test_parallel_workers_validation,
        test_session_manager_import
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Тест {test.__name__} завершился с исключением: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    print(f"✅ Прошли: {passed}")
    print(f"❌ Не прошли: {failed}")
    
    if failed == 0:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("Параллельная поддержка интегрирована корректно")
    else:
        print(f"\n⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ ({failed}/{len(tests)})")
        print("Необходимо исправить ошибки перед использованием")
    
    print("\n💡 Для ручного тестирования используйте:")
    print("   python core/main.py --monitor-sessions")
    print("   ./scripts/parallel_demo.py")

if __name__ == "__main__":
    main()