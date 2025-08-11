#!/usr/bin/env python3
"""
Change Tracking Module
Отслеживание изменений на веб-страницах источников новостей
"""

from .monitor import ChangeMonitor
from .database import ChangeTrackingDB

__version__ = '2.0'
__author__ = 'AI News Parser'

__all__ = ['ChangeMonitor', 'ChangeTrackingDB']