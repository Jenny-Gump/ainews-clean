import json

with open('../services/source_extractors.json', 'r') as f:
    config = json.load(f)

untested = []
tested = []

for source_id, cfg in config['extractors'].items():
    if cfg.get('status') != 'tested_real':
        untested.append(f"{source_id}: {cfg['name']}")
    else:
        tested.append(source_id)

print(f'✅ Протестированные источники: {len(tested)}')
print(f'❌ Непротестированные источники ({len(untested)}):')
for s in untested:
    print(f'  • {s}')