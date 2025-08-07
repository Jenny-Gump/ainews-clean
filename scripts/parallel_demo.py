#!/usr/bin/env python3
"""
Демонстрационный скрипт параллельной работы AI News Parser
"""

import subprocess
import time
import os
import signal
import sys
from pathlib import Path

def run_command(cmd, description):
    """Выполнить команду с описанием"""
    print(f"\n🔍 {description}")
    print(f"💻 Команда: {cmd}")
    print("-" * 60)
    
    # Выполняем команду в venv
    full_cmd = f"source venv/bin/activate && {cmd}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Успешно выполнено")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ Ошибка (код {result.returncode})")
        if result.stderr:
            print(result.stderr)
    
    return result.returncode == 0

def main():
    """Главная функция демонстрации"""
    print("=" * 80)
    print("🚀 ДЕМОНСТРАЦИЯ ПАРАЛЛЕЛЬНОЙ РАБОТЫ AI NEWS PARSER")
    print("=" * 80)
    print()
    print("Этот скрипт продемонстрирует:")
    print("1. Мониторинг активных сессий")
    print("2. Запуск 3 параллельных воркеров")
    print("3. Мониторинг во время работы")
    print("4. Финальную статистику")
    print()
    
    # Проверяем что мы в правильной директории
    if not Path("core/main.py").exists():
        print("❌ Ошибка: Скрипт должен запускаться из корневой директории проекта")
        print("💡 Выполните: cd '/Users/skynet/Desktop/AI DEV/ainews-clean'")
        sys.exit(1)
    
    # Шаг 1: Показать текущее состояние сессий
    print("\n" + "=" * 60)
    print("📊 ШАГ 1: Текущее состояние сессий")
    print("=" * 60)
    
    run_command(
        "python core/main.py --monitor-sessions",
        "Проверка активных сессий (должно быть пусто)"
    )
    
    # Шаг 2: Показать статистику статей
    print("\n" + "=" * 60)
    print("📈 ШАГ 2: Статистика статей")
    print("=" * 60)
    
    run_command(
        "python core/main.py --stats",
        "Проверка количества статей для обработки"
    )
    
    # Спрашиваем разрешение на продолжение
    print("\n" + "=" * 60)
    print("⚡ ШАГ 3: Параллельная обработка")
    print("=" * 60)
    print("Сейчас будет запущено 3 параллельных воркера для обработки статей")
    print("Каждый воркер обработает максимум 5 статей с интервалом 3 секунды")
    print()
    response = input("Продолжить? (y/N): ").strip().lower()
    
    if response != 'y':
        print("Демонстрация прервана пользователем")
        return
    
    print("\n🚀 Запуск параллельных воркеров...")
    print("💡 Чтобы остановить, нажмите Ctrl+C через несколько секунд")
    print()
    
    # Создаем процесс параллельных воркеров
    cmd = "source venv/bin/activate && python core/main.py --parallel-workers 3 --max-articles 5 --delay-between 3"
    
    try:
        # Запускаем в отдельном процессе
        process = subprocess.Popen(
            cmd, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print(f"💻 Запущена команда: {cmd}")
        print(f"🆔 PID процесса: {process.pid}")
        print()
        
        # Даем воркерам время поработать
        print("⏱️  Ожидание 10 секунд для демонстрации...")
        
        start_time = time.time()
        output_lines = []
        
        while time.time() - start_time < 10:
            if process.poll() is not None:  # Процесс завершился
                break
            
            # Читаем вывод
            try:
                line = process.stdout.readline()
                if line:
                    print(f"📝 {line.rstrip()}")
                    output_lines.append(line)
            except:
                pass
            
            time.sleep(0.1)
        
        # Останавливаем процесс
        if process.poll() is None:
            print("\n⏹️  Останавливаем воркеры...")
            process.send_signal(signal.SIGINT)
            
            # Ждем до 5 секунд для graceful shutdown
            try:
                process.wait(timeout=5)
                print("✅ Воркеры корректно остановлены")
            except subprocess.TimeoutExpired:
                print("⚠️  Принудительная остановка...")
                process.kill()
                process.wait()
        
        # Читаем оставшийся вывод
        remaining_output = process.communicate()[0]
        if remaining_output:
            print("📝 Финальный вывод:")
            print(remaining_output)
    
    except KeyboardInterrupt:
        print("\n⚠️  Получен Ctrl+C, останавливаем демо...")
        if 'process' in locals() and process.poll() is None:
            process.kill()
            process.wait()
    
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")
        return
    
    # Шаг 4: Финальный мониторинг
    print("\n" + "=" * 60)
    print("📊 ШАГ 4: Финальное состояние")
    print("=" * 60)
    
    time.sleep(2)  # Ждем чтобы БД обновилась
    
    run_command(
        "python core/main.py --monitor-sessions",
        "Проверка сессий после работы"
    )
    
    run_command(
        "python core/main.py --stats",
        "Финальная статистика статей"
    )
    
    print("\n" + "=" * 80)
    print("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 80)
    print()
    print("🎯 Что было продемонстрировано:")
    print("   ✓ Параллельная работа 3 воркеров без конфликтов")
    print("   ✓ Атомарное получение статей через SessionManager")  
    print("   ✓ Мониторинг активных сессий в реальном времени")
    print("   ✓ Graceful shutdown при получении Ctrl+C")
    print()
    print("💡 Для продакшен использования:")
    print(f"   python core/main.py --parallel-workers 3")
    print(f"   python core/main.py --monitor-sessions")
    print()

if __name__ == "__main__":
    main()