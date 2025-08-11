"""
Code2API - AI-powered system that converts source code into APIs
"""

__version__ = "1.0.0"
__author__ = "Code2API Team"
__email__ = "team@code2api.com"
__description__ = "Transform source code into production-ready APIs using AI"

from .src.parsers.code_parser import CodeParser
from .src.ai.analyzer import AIAnalyzer
from .src.generators.api_generator import APIGenerator

__all__ = [
    "CodeParser",
    "AIAnalyzer", 
    "APIGenerator"
]
