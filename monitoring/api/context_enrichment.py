"""
Context Enrichment Monitoring API
Provides monitoring endpoints for the Context Enrichment system
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import os
import sys

# Add the context enrichment standalone path
sys.path.append('/Users/skynet/Desktop/AI DEV/context_enrichment_standalone')

from .core import (
    get_monitoring_db_connection, 
    format_timestamp, 
    handle_db_error, 
    logger
)

router = APIRouter(prefix="/api/context-enrichment", tags=["context-enrichment"])

@router.get("/health")
async def get_health_status():
    """Get Context Enrichment system health status"""
    try:
        # Import performance monitor from context enrichment system
        try:
            from services.performance_monitor import get_performance_monitor
            monitor = get_performance_monitor()
            health_report = monitor.create_health_check_report()
            return health_report
        except ImportError:
            # Fallback if monitor not available
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'unknown',
                'issues': ['Performance monitor not available'],
                'metrics': {},
                'active_operations': 0,
                'uptime_seconds': 0
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to get Context Enrichment health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/summary")
async def get_metrics_summary(hours: int = Query(24, ge=1, le=168)):
    """Get performance metrics summary"""
    try:
        # Import performance monitor
        try:
            from services.performance_monitor import get_performance_monitor
            monitor = get_performance_monitor()
            summary = monitor.get_performance_summary(hours=hours)
            return summary
        except ImportError:
            # Fallback to direct database query
            return await _get_fallback_metrics_summary(hours)
            
    except Exception as e:
        logger.error(f"❌ Failed to get metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/costs/analysis")
async def get_cost_analysis(days: int = Query(7, ge=1, le=30)):
    """Get API cost analysis"""
    try:
        try:
            from services.performance_monitor import get_performance_monitor
            monitor = get_performance_monitor()
            cost_analysis = monitor.get_cost_analysis(days=days)
            return cost_analysis
        except ImportError:
            return await _get_fallback_cost_analysis(days)
            
    except Exception as e:
        logger.error(f"❌ Failed to get cost analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/costs/optimization")
async def get_cost_optimization_recommendations():
    """Get cost optimization recommendations"""
    try:
        try:
            from services.performance_analyzer import get_performance_analyzer
            analyzer = get_performance_analyzer()
            cost_analysis = await analyzer.analyze_api_costs(days=7)
            
            return {
                'optimizations': cost_analysis.get('optimizations', []),
                'total_potential_savings': sum(
                    opt['potential_savings'] for opt in cost_analysis.get('optimizations', [])
                ),
                'analysis_date': datetime.now().isoformat()
            }
        except ImportError:
            return {'error': 'Performance analyzer not available', 'optimizations': []}
            
    except Exception as e:
        logger.error(f"❌ Failed to get cost optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/report")
async def get_performance_report(days: int = Query(7, ge=1, le=30)):
    """Get comprehensive performance report"""
    try:
        try:
            from services.performance_analyzer import get_performance_analyzer
            analyzer = get_performance_analyzer()
            report = await analyzer.generate_optimization_report(days=days)
            return report
        except ImportError:
            return {'error': 'Performance analyzer not available'}
            
    except Exception as e:
        logger.error(f"❌ Failed to get performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiments/stats")
async def get_experiment_stats():
    """Get Context Enrichment experiment statistics from Supabase"""
    try:
        # Import Supabase client
        try:
            from services.supabase_database import create_database_instance
            from config import get_config
            
            config = get_config()
            if not config.USE_SUPABASE:
                return {'error': 'Supabase not configured'}
            
            db = create_database_instance(config)
            stats = await db.get_database_stats()
            
            return {
                'total_experiments': stats.total_experiments,
                'completed_experiments': stats.completed_experiments,
                'failed_experiments': stats.failed_experiments,
                'pending_experiments': stats.pending_experiments,
                'avg_processing_time': stats.avg_processing_time,
                'total_sources': stats.total_sources,
                'total_cost': stats.total_cost,
                'timestamp': datetime.now().isoformat()
            }
            
        except ImportError as e:
            return {'error': f'Context Enrichment system not available: {e}'}
            
    except Exception as e:
        logger.error(f"❌ Failed to get experiment stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vector-search/performance")
async def get_vector_search_performance(hours: int = Query(24)):
    """Get vector search performance metrics"""
    try:
        with get_monitoring_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get vector search metrics
            cursor.execute("""
                SELECT 
                    search_type,
                    COUNT(*) as total_searches,
                    AVG(search_time_ms) as avg_time_ms,
                    MIN(search_time_ms) as min_time_ms,
                    MAX(search_time_ms) as max_time_ms,
                    AVG(results_returned) as avg_results,
                    AVG(similarity_threshold) as avg_threshold
                FROM vector_search_performance
                WHERE timestamp >= datetime('now', '-{} hours')
                GROUP BY search_type
                ORDER BY total_searches DESC
            """.format(hours))
            
            search_stats = []
            for row in cursor.fetchall():
                search_stats.append({
                    'search_type': row[0],
                    'total_searches': row[1],
                    'avg_time_ms': round(row[2], 2) if row[2] else 0,
                    'min_time_ms': row[3],
                    'max_time_ms': row[4],
                    'avg_results': round(row[5], 1) if row[5] else 0,
                    'avg_threshold': round(row[6], 3) if row[6] else 0
                })
            
            return {
                'time_range_hours': hours,
                'search_performance': search_stats,
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to get vector search performance: {e}")
        return {
            'time_range_hours': hours,
            'search_performance': [],
            'error': str(e)
        }

@router.get("/pipeline/stages")
async def get_pipeline_performance(hours: int = Query(24)):
    """Get pipeline stage performance"""
    try:
        with get_monitoring_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    pipeline_stage,
                    COUNT(*) as total_operations,
                    AVG(stage_duration_ms) as avg_duration_ms,
                    AVG(memory_usage_mb) as avg_memory_mb,
                    AVG(cpu_usage_percent) as avg_cpu_percent,
                    SUM(sources_found) as total_sources_found,
                    SUM(sources_selected) as total_sources_selected,
                    SUM(total_cost_usd) as total_cost,
                    COUNT(CASE WHEN error_occurred = 1 THEN 1 END) as error_count
                FROM context_pipeline_metrics
                WHERE timestamp >= datetime('now', '-{} hours')
                GROUP BY pipeline_stage
                ORDER BY total_operations DESC
            """.format(hours))
            
            pipeline_stats = []
            for row in cursor.fetchall():
                pipeline_stats.append({
                    'stage': row[0],
                    'total_operations': row[1],
                    'avg_duration_ms': round(row[2], 2) if row[2] else 0,
                    'avg_memory_mb': round(row[3], 2) if row[3] else 0,
                    'avg_cpu_percent': round(row[4], 2) if row[4] else 0,
                    'total_sources_found': row[5] or 0,
                    'total_sources_selected': row[6] or 0,
                    'total_cost': round(row[7], 4) if row[7] else 0,
                    'error_count': row[8] or 0,
                    'success_rate': round((row[1] - (row[8] or 0)) / row[1] * 100, 1) if row[1] > 0 else 100
                })
            
            return {
                'time_range_hours': hours,
                'pipeline_stages': pipeline_stats,
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to get pipeline performance: {e}")
        return {
            'time_range_hours': hours,
            'pipeline_stages': [],
            'error': str(e)
        }

@router.get("/supabase/connection")
async def get_supabase_connection_status():
    """Get Supabase connection and performance status"""
    try:
        # Test Supabase connection
        try:
            from services.supabase_database import create_database_instance
            from config import get_config
            
            config = get_config()
            if not config.USE_SUPABASE:
                return {
                    'status': 'disabled',
                    'message': 'Supabase not configured in environment'
                }
            
            db = create_database_instance(config)
            connection_ok = await db.check_main_db_exists()
            
            if connection_ok:
                # Get recent query performance
                with get_monitoring_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT 
                            query_type,
                            COUNT(*) as query_count,
                            AVG(query_duration_ms) as avg_duration,
                            MAX(query_duration_ms) as max_duration,
                            COUNT(CASE WHEN error_code IS NOT NULL THEN 1 END) as error_count
                        FROM supabase_performance_metrics
                        WHERE timestamp >= NOW() - INTERVAL '-1 hours'
                        GROUP BY query_type
                        ORDER BY query_count DESC
                    """)
                    
                    query_performance = []
                    for row in cursor.fetchall():
                        query_performance.append({
                            'query_type': row[0],
                            'query_count': row[1],
                            'avg_duration_ms': round(row[2], 2) if row[2] else 0,
                            'max_duration_ms': row[3] or 0,
                            'error_count': row[4] or 0,
                            'success_rate': round((row[1] - (row[4] or 0)) / row[1] * 100, 1) if row[1] > 0 else 100
                        })
                
                return {
                    'status': 'connected',
                    'url': config.SUPABASE_URL,
                    'query_performance': query_performance,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to connect to Supabase'
                }
                
        except ImportError:
            return {
                'status': 'unavailable',
                'message': 'Context Enrichment system not available'
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to check Supabase connection: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

# Fallback functions for when performance monitor is not available
async def _get_fallback_metrics_summary(hours: int) -> Dict[str, Any]:
    """Fallback metrics summary when monitor is not available"""
    try:
        with get_monitoring_db_connection() as conn:
            cursor = conn.cursor()
            
            # Basic metrics from database
            cursor.execute("""
                SELECT 
                    component,
                    COUNT(*) as operations,
                    AVG(duration_ms) as avg_duration,
                    SUM(cost_usd) as total_cost
                FROM context_enrichment_metrics
                WHERE timestamp >= datetime('now', '-{} hours')
                GROUP BY component
            """.format(hours))
            
            metrics = []
            for row in cursor.fetchall():
                metrics.append({
                    'component': row[0],
                    'operations': row[1],
                    'avg_duration_ms': round(row[2], 2) if row[2] else 0,
                    'total_cost': round(row[3], 4) if row[3] else 0
                })
            
            return {
                'time_range_hours': hours,
                'enrichment_metrics': metrics,
                'fallback': True
            }
    except Exception as e:
        return {'error': str(e), 'fallback': True}

async def _get_fallback_cost_analysis(days: int) -> Dict[str, Any]:
    """Fallback cost analysis"""
    try:
        with get_monitoring_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    service,
                    SUM(cost_usd) as total_cost,
                    COUNT(*) as requests
                FROM api_cost_tracking
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY service
            """.format(days))
            
            costs = []
            total_cost = 0
            for row in cursor.fetchall():
                cost = round(row[1], 4) if row[1] else 0
                costs.append({
                    'service': row[0],
                    'total_cost': cost,
                    'requests': row[2]
                })
                total_cost += cost
            
            return {
                'time_range_days': days,
                'total_cost': total_cost,
                'service_breakdown': costs,
                'fallback': True
            }
    except Exception as e:
        return {'error': str(e), 'fallback': True}

@router.get("/alerts/active")
async def get_active_alerts():
    """Get active performance alerts"""
    try:
        try:
            from services.alert_system import get_alert_system
            alert_system = get_alert_system()
            active_alerts = await alert_system.get_active_alerts()
            
            return {
                "active_alerts": [
                    {
                        "id": alert.id,
                        "severity": alert.severity.value,
                        "component": alert.component,
                        "metric": alert.metric,
                        "current_value": alert.current_value,
                        "threshold": alert.threshold,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in active_alerts
                ],
                "count": len(active_alerts)
            }
        except ImportError:
            return {"error": "Alert system not available", "active_alerts": [], "count": 0}
            
    except Exception as e:
        logger.error(f"❌ Failed to get active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/summary")
async def get_alert_summary():
    """Get alert system summary"""
    try:
        try:
            from services.alert_system import get_alert_system
            alert_system = get_alert_system()
            summary = await alert_system.get_alert_summary()
            return summary
        except ImportError:
            return {
                "error": "Alert system not available",
                "active_alerts_count": 0,
                "system_status": "unknown"
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to get alert summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
