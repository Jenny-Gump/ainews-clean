# Backups Directory

This directory contains backups of the AI News Parser Clean system components.

## Backup Naming Convention
- `monitoring_YYYYMMDD_HHMMSS_description` - Monitoring system backups
- `core_YYYYMMDD_HHMMSS_description` - Core system backups
- `data_YYYYMMDD_HHMMSS_description` - Database backups

## Current Backups
- `monitoring_20250805_184436_working_dashboard/` - Working monitoring dashboard after fixing JS conflicts

## Creating Backups
```bash
# Backup monitoring
cp -r monitoring "backups/monitoring_$(date +%Y%m%d_%H%M%S)_description"

# Backup core
cp -r core services "backups/core_$(date +%Y%m%d_%H%M%S)_description"

# Backup databases
cp -r data "backups/data_$(date +%Y%m%d_%H%M%S)_description"
```

## Restoring from Backup
```bash
# Restore monitoring
cp -r backups/monitoring_20250805_184436_working_dashboard/* monitoring/

# Restore core
cp -r backups/core_YYYYMMDD_HHMMSS_description/* .

# Restore databases
cp -r backups/data_YYYYMMDD_HHMMSS_description/* data/
```