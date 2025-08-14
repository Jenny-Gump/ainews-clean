#!/bin/bash

# КРИТИЧЕСКИЙ БЭКАП МОНИТОРИНГА
# Этот скрипт создает полный бэкап всех критических файлов мониторинга
# которые влияют на работу логов RSS парсинга

cd /Users/skynet/Desktop/AI\ DEV/ainews-clean

# Создаем директорию для бэкапа с текущей датой и временем
backup_dir="backups/monitoring_critical_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

echo "🔴 СОЗДАНИЕ КРИТИЧЕСКОГО БЭКАПА МОНИТОРИНГА"
echo "📁 Директория бэкапа: $backup_dir"
echo ""

# Бэкап API файлов (КРИТИЧЕСКИ ВАЖНО!)
echo "📋 Бэкап API файлов..."
cp -r monitoring/api "$backup_dir/"
echo "  ✅ monitoring/api/pipeline_supabase.py"
echo "  ✅ monitoring/api/__init__.py"
echo "  ✅ monitoring/api/*.py"

# Бэкап статических файлов (JavaScript для логов)
echo "📋 Бэкап статических файлов..."
cp -r monitoring/static "$backup_dir/"
echo "  ✅ monitoring/static/pipeline-logs.js"
echo "  ✅ monitoring/static/index.html"

# Бэкап главного файла приложения
echo "📋 Бэкап главного файла..."
cp monitoring/app.py "$backup_dir/"
echo "  ✅ monitoring/app.py"

# Бэкап скриптов запуска
echo "📋 Бэкап скриптов запуска..."
cp monitoring/*.sh "$backup_dir/" 2>/dev/null
echo "  ✅ monitoring/*.sh"

# Создаем файл с информацией о бэкапе
cat > "$backup_dir/BACKUP_INFO.txt" << EOF
КРИТИЧЕСКИЙ БЭКАП МОНИТОРИНГА
==============================
Дата создания: $(date)
Версия системы: v2.9 (с исправленными логами)

ВКЛЮЧЕННЫЕ ФАЙЛЫ:
- api/pipeline_supabase.py - основной API для логов (КРИТИЧЕСКИ ВАЖНО!)
- api/__init__.py - импорты роутеров
- app.py - регистрация роутеров
- static/pipeline-logs.js - клиентская часть логов
- static/index.html - интерфейс дашборда

ВОССТАНОВЛЕНИЕ:
1. cd /Users/skynet/Desktop/AI\ DEV/ainews-clean
2. cp -r "$backup_dir/api"/* monitoring/api/
3. cp -r "$backup_dir/static"/* monitoring/static/
4. cp "$backup_dir/app.py" monitoring/
5. cd monitoring && ./stop_monitoring.sh && ./start_monitoring.sh

ПРОВЕРКА ПОСЛЕ ВОССТАНОВЛЕНИЯ:
curl -s "http://localhost:8001/api/pipeline/logs" | python3 -m json.tool | head -20

КРИТИЧЕСКИ ВАЖНЫЕ МОМЕНТЫ:
- В pipeline_supabase.py должно быть ДВА endpoint
- Первый на /logs (строка ~159)
- Второй на /logs-detailed (строка ~398)
- Путь к логам должен быть абсолютным через Path(__file__).parent.parent.parent
EOF

echo ""
echo "✅ БЭКАП СОЗДАН УСПЕШНО!"
echo "📁 Расположение: $backup_dir"
echo ""
echo "📝 Для восстановления выполните:"
echo "   ./monitoring/restore_from_backup.sh $backup_dir"
echo ""
echo "⚠️  ВАЖНО: Этот бэкап содержит рабочую версию с исправленными логами!"