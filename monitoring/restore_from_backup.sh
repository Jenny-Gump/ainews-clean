#!/bin/bash

# ВОССТАНОВЛЕНИЕ МОНИТОРИНГА ИЗ КРИТИЧЕСКОГО БЭКАПА
# Использование: ./restore_from_backup.sh backups/monitoring_critical_YYYYMMDD_HHMMSS

if [ $# -eq 0 ]; then
    echo "❌ ОШИБКА: Укажите директорию бэкапа!"
    echo "Использование: $0 backups/monitoring_critical_YYYYMMDD_HHMMSS"
    echo ""
    echo "Доступные бэкапы:"
    ls -d backups/monitoring_critical_* 2>/dev/null | tail -5
    exit 1
fi

backup_dir="$1"

# Проверяем что бэкап существует
if [ ! -d "$backup_dir" ]; then
    echo "❌ ОШИБКА: Директория бэкапа не найдена: $backup_dir"
    echo ""
    echo "Доступные бэкапы:"
    ls -d backups/monitoring_critical_* 2>/dev/null | tail -5
    exit 1
fi

# Проверяем что это критический бэкап мониторинга
if [ ! -f "$backup_dir/BACKUP_INFO.txt" ]; then
    echo "❌ ОШИБКА: Это не критический бэкап мониторинга!"
    echo "Файл BACKUP_INFO.txt не найден"
    exit 1
fi

echo "🔴 ВОССТАНОВЛЕНИЕ МОНИТОРИНГА ИЗ КРИТИЧЕСКОГО БЭКАПА"
echo "📁 Источник: $backup_dir"
echo ""

# Переходим в корневую директорию проекта
cd /Users/skynet/Desktop/AI\ DEV/ainews-clean

# Останавливаем мониторинг если он запущен
echo "🛑 Останавливаем мониторинг..."
cd monitoring && ./stop_monitoring.sh 2>/dev/null
cd ..

# Создаем бэкап текущего состояния (на всякий случай)
echo "💾 Создаем бэкап текущего состояния..."
current_backup="backups/monitoring_before_restore_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$current_backup"
cp -r monitoring/api "$current_backup/" 2>/dev/null
cp -r monitoring/static "$current_backup/" 2>/dev/null
cp monitoring/app.py "$current_backup/" 2>/dev/null
echo "  ✅ Текущее состояние сохранено в: $current_backup"

# Восстанавливаем файлы из бэкапа
echo ""
echo "📋 Восстанавливаем API файлы..."
cp -r "$backup_dir/api"/* monitoring/api/
echo "  ✅ Восстановлены API файлы"

echo "📋 Восстанавливаем статические файлы..."
cp -r "$backup_dir/static"/* monitoring/static/
echo "  ✅ Восстановлены статические файлы"

echo "📋 Восстанавливаем главный файл..."
cp "$backup_dir/app.py" monitoring/
echo "  ✅ Восстановлен app.py"

# Восстанавливаем скрипты если есть
if [ -f "$backup_dir/start_monitoring.sh" ]; then
    echo "📋 Восстанавливаем скрипты запуска..."
    cp "$backup_dir"/*.sh monitoring/ 2>/dev/null
    chmod +x monitoring/*.sh
    echo "  ✅ Восстановлены скрипты"
fi

echo ""
echo "🚀 Запускаем мониторинг..."
cd monitoring && ./start_monitoring.sh

# Ждем запуска
sleep 5

echo ""
echo "🔍 Проверяем работу логов..."
response=$(curl -s "http://localhost:8001/api/pipeline/logs?limit=1" 2>/dev/null)

if echo "$response" | grep -q '"logs"'; then
    count=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('logs', [])))" 2>/dev/null || echo "0")
    if [ "$count" -gt "0" ]; then
        echo "  ✅ ЛОГИ РАБОТАЮТ! Найдено записей: $count"
    else
        echo "  ⚠️  Логи возвращают пустой массив (возможно файл логов пуст)"
    fi
else
    echo "  ❌ ОШИБКА: API не отвечает или формат неправильный"
    echo "  Ответ: $response"
fi

echo ""
echo "✅ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo ""
echo "📝 Информация о восстановленном бэкапе:"
head -5 "$backup_dir/BACKUP_INFO.txt" 2>/dev/null
echo ""
echo "🌐 Откройте дашборд: http://localhost:8001"
echo "📊 Проверьте вкладку Control -> Pipeline Activity"