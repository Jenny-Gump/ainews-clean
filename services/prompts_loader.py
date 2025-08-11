#!/usr/bin/env python3
"""
Prompts Loader - загрузчик промптов из файлов
Позволяет легко редактировать промпты без изменения кода
"""
import os
from pathlib import Path
from typing import Dict, Any

class PromptsLoader:
    """Загружает промпты из файлов в папке prompts/"""
    
    def __init__(self, prompts_dir: str = None):
        """
        Инициализация загрузчика промптов
        
        Args:
            prompts_dir: Путь к папке с промптами (по умолчанию prompts/ в корне проекта)
        """
        if prompts_dir is None:
            # Определяем путь к папке prompts относительно корня проекта
            project_root = Path(__file__).parent.parent
            prompts_dir = project_root / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self._cache = {}
        
        if not self.prompts_dir.exists():
            raise ValueError(f"Prompts directory not found: {self.prompts_dir}")
    
    def load_prompt(self, prompt_name: str, variables: Dict[str, Any] = None) -> str:
        """
        Загружает промпт из файла и подставляет переменные
        
        Args:
            prompt_name: Имя файла промпта (без расширения .txt)
            variables: Словарь с переменными для подстановки
            
        Returns:
            Промпт с подставленными переменными
        """
        # Проверяем кэш
        if prompt_name not in self._cache:
            prompt_file = self.prompts_dir / f"{prompt_name}.txt"
            
            if not prompt_file.exists():
                raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self._cache[prompt_name] = f.read()
        
        prompt = self._cache[prompt_name]
        
        # Подставляем переменные если они есть
        if variables:
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                if placeholder in prompt:
                    # Преобразуем значение в строку
                    str_value = str(value) if value is not None else ""
                    prompt = prompt.replace(placeholder, str_value)
        
        return prompt
    
    def reload_prompt(self, prompt_name: str):
        """
        Перезагружает промпт из файла (сбрасывает кэш)
        
        Args:
            prompt_name: Имя файла промпта
        """
        if prompt_name in self._cache:
            del self._cache[prompt_name]
    
    def reload_all(self):
        """Перезагружает все промпты (очищает кэш)"""
        self._cache.clear()
    
    def list_prompts(self) -> list:
        """
        Возвращает список доступных промптов
        
        Returns:
            Список имен промптов (без расширения)
        """
        prompts = []
        for file in self.prompts_dir.glob("*.txt"):
            prompts.append(file.stem)
        return sorted(prompts)


# Глобальный экземпляр загрузчика
_prompts_loader = None

def get_prompts_loader() -> PromptsLoader:
    """Получить глобальный экземпляр загрузчика промптов"""
    global _prompts_loader
    if _prompts_loader is None:
        _prompts_loader = PromptsLoader()
    return _prompts_loader

def load_prompt(prompt_name: str, **kwargs) -> str:
    """
    Удобная функция для загрузки промпта
    
    Args:
        prompt_name: Имя промпта
        **kwargs: Переменные для подстановки
        
    Returns:
        Промпт с подставленными переменными
    """
    loader = get_prompts_loader()
    return loader.load_prompt(prompt_name, kwargs)