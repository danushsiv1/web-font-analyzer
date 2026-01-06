#!/usr/bin/env python3

import click
import os
import sys
from rich.console import Console
from rich.panel import Panel
from font_extractor import analyze_fonts
from ai_analyzer import get_ai_analysis
from output_formatter import format_output

console = Console()

@click.command()
@click.argument('url')
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI API key (or set OPENAI_API_KEY env var)')
@click.option('--model', default='gpt-4o-mini', help='OpenAI model to use')
@click.option('--json', is_flag=True, help='Output results as JSON')
@click.option('--verbose', is_flag=True, help='Show verbose output')
def main(url, api_key, model, json, verbose):
    """AI-powered web font analyzer using Chromium (Playwright for Python)"""
    try:
        console.print("[blue]🔍 Starting font analysis...[/]\n")
        
        if verbose:
            console.print(f"[gray]Analyzing: {url}[/]")
            console.print(f"[gray]Model: {model}[/]\n")
        
        # Extract fonts from the webpage
        console.print("[yellow]📊 Extracting font information from webpage...[/]")
        font_data = analyze_fonts(url, verbose)
        
        if not font_data or not font_data.get('fonts') or len(font_data['fonts']) == 0:
            console.print("[red]❌ No fonts found on this webpage.[/]")
            sys.exit(1)
        
        console.print(f"[green]✓ Found {len(font_data['fonts'])} unique font usage(s)[/]\n")
        
        # Get AI analysis
        if not api_key:
            console.print("[yellow]⚠️  No OpenAI API key provided. Showing raw font data only.[/]\n")
            format_output(font_data, None, json)
            return
        
        console.print("[yellow]🤖 Analyzing typography with AI...[/]")
        ai_analysis = get_ai_analysis(font_data, api_key, model)
        console.print("[green]✓ AI analysis complete[/]\n")
        
        # Format and display results
        format_output(font_data, ai_analysis, json)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/]")
        if verbose:
            import traceback
            console.print_exception()
        sys.exit(1)

if __name__ == '__main__':
    main()
