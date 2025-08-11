#!/usr/bin/env python3
"""
Command Line Interface for Code2API
"""
import click
import os
import json
import tempfile
import zipfile
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.panel import Panel

from src.parsers.code_parser import CodeParser
from src.ai.analyzer import AIAnalyzer
from src.generators.api_generator import APIGenerator
from src.github.repo_fetcher import GitHubRepoFetcher
from src.config import config

console = Console()

def check_api_key():
    """Check if OpenAI API key is configured"""
    api_key = config.OPENAI_API_KEY or os.getenv('OPENAI_API_KEY')
    if not api_key:
        console.print(Panel(
            """❌ OpenAI API Key Required

To use Code2API, you need an OpenAI API key:

1. Get your API key from: https://platform.openai.com/api-keys
2. Copy your API key
3. Set it in the .env file:
   OPENAI_API_KEY=your_api_key_here

Or set it as an environment variable:
   set OPENAI_API_KEY=your_api_key_here (Windows)
   export OPENAI_API_KEY=your_api_key_here (Linux/Mac)
""", 
            style="red", 
            title="Setup Required"
        ))
        raise click.ClickException("OpenAI API key not found. Please set up your API key.")

@click.group()
def cli():
    """Code2API - Convert source code into APIs using AI"""
    pass

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', default='generated_api', help='Output directory name')
@click.option('--no-auth', is_flag=True, help='Disable authentication for all endpoints')
@click.option('--format', type=click.Choice(['json', 'yaml']), default='json', help='Output format for analysis')
def analyze(file_path, output, no_auth, format):
    """Analyze a source code file and generate API"""
    
    # Check API key first
    check_api_key()
    
    console.print(Panel(f"🔍 Analyzing: {file_path}", style="blue"))
    
    try:
        # Initialize components
        parser = CodeParser()
        analyzer = AIAnalyzer()
        generator = APIGenerator()
        
        # Parse code
        with console.status("Parsing code..."):
            parsed_code = parser.parse_file(file_path)
        
        console.print(f"✅ Found {len(parsed_code.functions)} functions and {len(parsed_code.classes)} classes")
        
        # Analyze with AI
        with console.status("Analyzing with AI..."):
            analysis = analyzer.analyze_code(parsed_code)
        
        # Override auth if requested
        if no_auth:
            for endpoint in analysis.get("api_endpoints", []):
                endpoint["needs_auth"] = False
        
        # Generate documentation
        with console.status("Generating documentation..."):
            documentation = analyzer.generate_documentation(analysis)
            analysis["documentation"] = documentation
            
            optimizations = analyzer.suggest_optimizations(parsed_code)
            analysis["optimization_suggestions"] = optimizations
        
        # Display results
        display_analysis_results(analysis)
        
        # Generate API
        with console.status("Generating API..."):
            api_path = generator.generate_api(analysis, output)
        
        console.print(f"\n🚀 API generated successfully at: {api_path}")
        console.print(f"📝 To run the API: cd {api_path} && python main.py")
        
        # Save analysis to file
        analysis_file = Path(api_path) / f"analysis.{format}"
        with open(analysis_file, 'w') as f:
            if format == 'json':
                json.dump(analysis, f, indent=2)
            else:
                import yaml
                yaml.dump(analysis, f, default_flow_style=False)
        
        console.print(f"💾 Analysis saved to: {analysis_file}")
        
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
        raise click.Abort()

@cli.command()
@click.argument('repo_url')
@click.option('--output', '-o', default=None, help='Output directory name (auto-generated if not specified)')
@click.option('--branch', '-b', default='main', help='Git branch to analyze')
@click.option('--max-files', default=50, help='Maximum number of files to analyze')
@click.option('--extensions', '-e', multiple=True, default=['.py', '.js', '.java'], help='File extensions to analyze')
def analyze_repo(repo_url, output, branch, max_files, extensions):
    """Analyze a GitHub repository and generate API"""
    
    # Check API key first
    check_api_key()
    
    console.print(Panel(f"📦 Analyzing GitHub Repository: {repo_url}", style="blue"))
    
    try:
        # Initialize components
        parser = CodeParser()
        analyzer = AIAnalyzer()
        generator = APIGenerator()
        github_fetcher = GitHubRepoFetcher()
        
        # Parse GitHub URL
        console.print("🔍 Parsing repository URL...")
        repo_info = github_fetcher.parse_github_url(repo_url)
        owner = repo_info["owner"]
        repo = repo_info["repo"]
        
        console.print(f"📁 Repository: {owner}/{repo}")
        
        # Get repository information
        console.print("📡 Fetching repository information...")
        repo_data = github_fetcher.get_repo_info(owner, repo)
        
        console.print(f"⭐ Stars: {repo_data.get('stargazers_count', 0)}")
        console.print(f"🍴 Forks: {repo_data.get('forks_count', 0)}")
        console.print(f"📝 Language: {repo_data.get('language', 'Unknown')}")
        
        # Clone repository
        console.print(f"📥 Cloning repository (branch: {branch})...")
        with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    repo_path = github_fetcher.clone_repo(owner, repo, temp_dir, branch)
                except Exception:
                    # Fallback to ZIP download
                    console.print("Git clone failed, downloading as ZIP...", style="yellow")
                    zip_path = github_fetcher.download_repo_zip(owner, repo, branch)
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    extracted_dirs = [d for d in Path(temp_dir).iterdir() if d.is_dir()]
                    repo_path = str(extracted_dirs[0]) if extracted_dirs else temp_dir
                    os.unlink(zip_path)
                
                # Extract supported files
                console.print("🔍 Scanning for source code files...")
                supported_files = github_fetcher.extract_supported_files(repo_path, extensions)
                
                if len(supported_files) > max_files:
                    console.print(f"⚠️  Found {len(supported_files)} files, limiting to {max_files}", style="yellow")
                    supported_files = supported_files[:max_files]
                
                if not supported_files:
                    console.print("❌ No supported source code files found", style="red")
                    return
                
                console.print(f"📄 Found {len(supported_files)} source files to analyze")
                
                # Get repository statistics
                repo_stats = github_fetcher.get_repo_statistics(supported_files)
                
                # Display statistics
                console.print("\n📊 Repository Statistics:")
                for lang, count in repo_stats["languages"].items():
                    console.print(f"  {lang}: {count} files")
                console.print(f"  Total lines: {repo_stats['total_lines']:,}")
                
                # Analyze files
                all_endpoints = []
                all_security_recommendations = []
                all_optimization_suggestions = []
                
                console.print(f"\n🔄 Analyzing {len(supported_files)} files...")
                for i, file_path in enumerate(supported_files, 1):
                    console.print(f"  [{i}/{len(supported_files)}] {Path(file_path).name}")
                    try:
                        # Parse the file
                        parsed_code = parser.parse_file(file_path)
                        
                        # Skip files with no functions or classes
                        if not parsed_code.functions and not parsed_code.classes:
                            continue
                        
                        # Analyze with AI
                        analysis = analyzer.analyze_code(parsed_code)
                        
                        # Collect results
                        all_endpoints.extend(analysis.get("api_endpoints", []))
                        all_security_recommendations.extend(analysis.get("security_recommendations", []))
                        all_optimization_suggestions.extend(analysis.get("optimization_suggestions", []))
                        
                    except Exception as e:
                        console.print(f"    ⚠️  Error: {e}", style="yellow")
                        continue
                
                # Combine results
                combined_analysis = {
                    "api_endpoints": all_endpoints,
                    "security_recommendations": list(set(all_security_recommendations)),
                    "optimization_suggestions": list(set(all_optimization_suggestions)),
                    "repository_info": {
                        "name": repo_data.get("name"),
                        "description": repo_data.get("description"),
                        "language": repo_data.get("language"),
                        "stars": repo_data.get("stargazers_count"),
                        "forks": repo_data.get("forks_count"),
                        "url": repo_data.get("html_url")
                    },
                    "statistics": repo_stats,
                    "files_analyzed": len(supported_files)
                }
                
                # Display results
                display_analysis_results(combined_analysis)
                
                # Generate documentation
                with console.status("Generating documentation..."):
                    documentation = analyzer.generate_documentation(combined_analysis)
                    combined_analysis["documentation"] = documentation
                
                # Generate API
                if not output:
                    output = f"{owner}_{repo}".replace("-", "_").replace(".", "_")
                
                with console.status("Generating API..."):
                    api_path = generator.generate_api(combined_analysis, output)
                
                console.print(f"\n🚀 API generated successfully at: {api_path}")
                console.print(f"📁 Repository: {owner}/{repo}")
                console.print(f"📊 Files analyzed: {len(supported_files)}")
                console.print(f"🔗 Endpoints generated: {len(all_endpoints)}")
                console.print(f"📝 To run the API: cd {api_path} && python main.py")
                
                # Save analysis to file
                analysis_file = Path(api_path) / "repository_analysis.json"
                with open(analysis_file, 'w') as f:
                    json.dump(combined_analysis, f, indent=2)
                
                console.print(f"💾 Full analysis saved to: {analysis_file}")
        
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
        raise click.Abort()

@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--output', '-o', default='batch_apis', help='Output directory for all APIs')
@click.option('--extensions', '-e', multiple=True, default=['.py', '.js', '.java'], help='File extensions to process')
def batch(directory, output, extensions):
    """Analyze multiple files in a directory"""
    
    directory = Path(directory)
    files = []
    
    for ext in extensions:
        files.extend(directory.rglob(f"*{ext}"))
    
    if not files:
        console.print("❌ No files found with specified extensions", style="red")
        return
    
    console.print(f"📁 Found {len(files)} files to process")
    
    parser = CodeParser()
    analyzer = AIAnalyzer()
    generator = APIGenerator()
    
    results = []
    
    for file_path in track(files, description="Processing files..."):
        try:
            # Parse and analyze
            parsed_code = parser.parse_file(str(file_path))
            analysis = analyzer.analyze_code(parsed_code)
            
            # Generate API
            project_name = file_path.stem.replace('.', '_')
            api_path = generator.generate_api(analysis, f"{output}/{project_name}")
            
            results.append({
                "file": str(file_path),
                "api_path": api_path,
                "endpoints": len(analysis.get("api_endpoints", [])),
                "status": "success"
            })
            
        except Exception as e:
            results.append({
                "file": str(file_path),
                "error": str(e),
                "status": "failed"
            })
    
    # Display results table
    table = Table(title="Batch Processing Results")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Endpoints", justify="right")
    table.add_column("API Path", style="blue")
    
    for result in results:
        status = "✅" if result["status"] == "success" else "❌"
        endpoints = str(result.get("endpoints", "N/A"))
        api_path = result.get("api_path", result.get("error", ""))
        
        table.add_row(
            result["file"],
            status,
            endpoints,
            api_path
        )
    
    console.print(table)

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def security_scan(file_path):
    """Perform security analysis on a source code file"""
    
    console.print(Panel(f"🔒 Security Scanning: {file_path}", style="yellow"))
    
    try:
        parser = CodeParser()
        analyzer = AIAnalyzer()
        
        parsed_code = parser.parse_file(file_path)
        recommendations = analyzer._analyze_security(parsed_code)
        
        if not recommendations:
            console.print("✅ No security issues detected!", style="green")
        else:
            console.print("⚠️  Security Recommendations:", style="yellow")
            for i, rec in enumerate(recommendations, 1):
                console.print(f"{i}. {rec}")
        
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")

@cli.command()
def list_generated():
    """List all generated APIs"""
    
    if not config.GENERATED_DIR.exists():
        console.print("No APIs generated yet", style="yellow")
        return
    
    apis = [d for d in config.GENERATED_DIR.iterdir() if d.is_dir()]
    
    if not apis:
        console.print("No APIs found", style="yellow")
        return
    
    table = Table(title="Generated APIs")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="blue")
    table.add_column("Files", justify="right")
    table.add_column("Size", justify="right")
    
    for api_dir in apis:
        files = list(api_dir.rglob("*"))
        file_count = len([f for f in files if f.is_file()])
        
        # Calculate directory size
        size = sum(f.stat().st_size for f in files if f.is_file())
        size_str = f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.1f} MB"
        
        table.add_row(
            api_dir.name,
            str(api_dir),
            str(file_count),
            size_str
        )
    
    console.print(table)

@cli.command()
@click.option('--host', default='localhost', help='Host to run the server on')
@click.option('--port', default=8000, type=int, help='Port to run the server on')
def serve(host, port):
    """Start the Code2API web server"""
    
    console.print(Panel(f"🌐 Starting Code2API server on http://{host}:{port}", style="green"))
    
    try:
        import uvicorn
        from src.api.main import app
        
        uvicorn.run(app, host=host, port=port)
    except ImportError:
        console.print("❌ uvicorn not installed. Run: pip install uvicorn", style="red")
    except Exception as e:
        console.print(f"❌ Error starting server: {str(e)}", style="red")

def display_analysis_results(analysis):
    """Display analysis results in a formatted way"""
    
    # API Endpoints
    endpoints = analysis.get("api_endpoints", [])
    if endpoints:
        table = Table(title="🚀 Generated API Endpoints")
        table.add_column("Method", style="cyan")
        table.add_column("Path", style="blue")
        table.add_column("Function", style="green")
        table.add_column("Auth", justify="center")
        table.add_column("Description")
        
        for endpoint in endpoints:
            auth = "🔒" if endpoint.get("needs_auth") else "🔓"
            table.add_row(
                endpoint["http_method"],
                endpoint["endpoint_path"],
                endpoint["function_name"],
                auth,
                endpoint.get("description", "")[:50] + "..." if len(endpoint.get("description", "")) > 50 else endpoint.get("description", "")
            )
        
        console.print(table)
    
    # Security Recommendations
    security = analysis.get("security_recommendations", [])
    if security:
        console.print("\n🔒 Security Recommendations:", style="yellow")
        for i, rec in enumerate(security, 1):
            console.print(f"  {i}. {rec}")
    
    # Optimization Suggestions
    optimizations = analysis.get("optimization_suggestions", [])
    if optimizations:
        console.print("\n⚡ Optimization Suggestions:", style="cyan")
        for i, opt in enumerate(optimizations, 1):
            console.print(f"  {i}. {opt}")

if __name__ == '__main__':
    cli()
