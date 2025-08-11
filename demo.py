#!/usr/bin/env python3
"""
Demo CLI for Code2API - Works without OpenAI API key
"""
import click
import os
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.parsers.code_parser import CodeParser

console = Console()

@click.group()
def demo():
    """Code2API Demo - Test parsing without AI analysis"""
    pass

@demo.command()
@click.argument('file_path', type=click.Path(exists=True))
def parse(file_path):
    """Parse a source code file and show structure (no AI needed)"""
    
    console.print(Panel(f"🔍 Parsing: {file_path}", style="blue"))
    
    try:
        # Initialize parser
        parser = CodeParser()
        
        # Parse code
        with console.status("Parsing code..."):
            parsed_code = parser.parse_file(file_path)
        
        console.print(f"✅ Language: {parsed_code.language}")
        console.print(f"✅ Found {len(parsed_code.functions)} functions and {len(parsed_code.classes)} classes")
        
        # Display functions
        if parsed_code.functions:
            func_table = Table(title="Functions Found")
            func_table.add_column("Name", style="cyan")
            func_table.add_column("Parameters", style="magenta")
            func_table.add_column("Line", style="green")
            
            for func in parsed_code.functions:
                params = ", ".join([f"{p.name}: {p.type}" for p in func.parameters])
                func_table.add_row(func.name, params, str(func.line_number))
            
            console.print(func_table)
        
        # Display classes
        if parsed_code.classes:
            class_table = Table(title="Classes Found")
            class_table.add_column("Name", style="cyan")
            class_table.add_column("Methods", style="magenta")
            class_table.add_column("Line", style="green")
            
            for cls in parsed_code.classes:
                methods = ", ".join([m.name for m in cls.methods])
                class_table.add_row(cls.name, methods, str(cls.line_number))
            
            console.print(class_table)
        
        # Generate mock API suggestions
        console.print(Panel("🤖 Mock API Suggestions (no AI)", style="green"))
        
        api_table = Table(title="Suggested API Endpoints")
        api_table.add_column("Method", style="cyan")
        api_table.add_column("Endpoint", style="magenta")
        api_table.add_column("Description", style="white")
        
        for func in parsed_code.functions[:5]:  # Show first 5 functions
            if func.name.startswith('_'):
                continue
                
            method = "POST" if any(p.name in ['data', 'input', 'payload'] for p in func.parameters) else "GET"
            endpoint = f"/api/{func.name.lower()}"
            description = f"Execute {func.name} function"
            
            api_table.add_row(method, endpoint, description)
        
        console.print(api_table)
        
        console.print(Panel(
            "ℹ️  This is a demo mode. For full AI analysis, set up your OpenAI API key and use 'python cli.py analyze'",
            style="yellow"
        ))
        
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
        raise click.Abort()

@demo.command()
def examples():
    """Show example commands"""
    
    console.print(Panel("Code2API Demo Examples", style="blue"))
    
    examples_text = """
📝 Parse a Python file:
   python demo.py parse src/example.py

📝 Parse a JavaScript file:
   python demo.py parse examples/calculator.js

📝 Parse a Java file:
   python demo.py parse examples/UserService.java

🔧 Full analysis (requires OpenAI API key):
   python cli.py analyze src/example.py
   python cli.py analyze-repo https://github.com/user/repo.git

🌐 Web interface:
   python -m uvicorn src.api.main:app --reload
   # Then visit http://localhost:8000
"""
    
    console.print(examples_text)

if __name__ == '__main__':
    demo()
