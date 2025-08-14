#!/usr/bin/env python3
"""
Проверка текущего использования памяти системой AI News
"""
import psutil
import os

def get_ainews_processes():
    """Получить все процессы AI News"""
    ainews_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
        try:
            proc_info = proc.info
            if not proc_info['cmdline']:
                continue
                
            cmd_str = ' '.join(proc_info['cmdline']).lower()
            
            # Проверяем процессы AI News
            if any(keyword in cmd_str for keyword in ['ainews', 'main.py', 'app.py', 'monitoring', 'single_pipeline']):
                memory_mb = proc_info['memory_info'].rss / 1024 / 1024
                ainews_processes.append({
                    'pid': proc_info['pid'],
                    'name': proc_info['name'],
                    'memory_mb': memory_mb,
                    'cmd': ' '.join(proc_info['cmdline'][:3])
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return ainews_processes

def main():
    print("=" * 60)
    print("📊 AI NEWS MEMORY USAGE CHECK")
    print("=" * 60)
    
    processes = get_ainews_processes()
    
    if not processes:
        print("❌ No AI News processes found")
        return
    
    total_memory = 0
    
    print(f"\n{'PID':<8} {'Memory (MB)':<12} {'Process'}")
    print("-" * 60)
    
    for proc in sorted(processes, key=lambda p: p['memory_mb'], reverse=True):
        print(f"{proc['pid']:<8} {proc['memory_mb']:>10.1f}  {proc['cmd'][:40]}")
        total_memory += proc['memory_mb']
    
    print("-" * 60)
    print(f"{'TOTAL':<8} {total_memory:>10.1f} MB  ({len(processes)} processes)")
    print("=" * 60)
    
    # Оценка
    if total_memory < 500:
        print("✅ Memory usage is NORMAL")
    elif total_memory < 1000:
        print("⚠️ Memory usage is MODERATE")
    else:
        print("❌ Memory usage is HIGH - consider restart")

if __name__ == "__main__":
    main()