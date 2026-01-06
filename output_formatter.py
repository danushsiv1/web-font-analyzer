from rich.console import Console
from rich.panel import Panel
from typing import Dict, Any, Optional
import json

console = Console()

def format_output(font_data: Dict[str, Any], ai_analysis: Optional[Dict[str, Any]], json_output: bool = False):
    """Formats and displays the analysis results"""
    
    if json_output:
        output = {
            'fonts': font_data.get('fonts', []),
            'fontFaces': font_data.get('fontFaces', []),
            'externalFonts': font_data.get('externalFonts', []),
            'fontFiles': font_data.get('fontFiles', []),
            'declaredFonts': font_data.get('declaredFonts', []),
            'variableFonts': font_data.get('variableFonts', []),
            'cssImports': font_data.get('cssImports', []),
            'loadedFonts': font_data.get('loadedFonts', []),
            'aiAnalysis': ai_analysis
        }
        print(json.dumps(output, indent=2))
        return
    
    # Header
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/]")
    console.print("[bold cyan]           WEB FONT ANALYSIS RESULTS[/]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/]\n")
    
    # Font Usage Section
    console.print("[bold yellow]📝 FONT USAGE:[/]")
    console.print("[gray]─[/]" * 55)
    
    fonts = font_data.get('fonts', [])
    for index, font in enumerate(fonts[:10], 1):
        console.print(f"\n[white]{index}. [bold]{font.get('fontFamily', 'Unknown')}[/][/]")
        console.print(f"[gray]   Total Usage: {font.get('totalUsageCount', 0)} time(s)[/]")
        console.print(f"[gray]   Used in: {', '.join(font.get('elements', []))}[/]")
        
        variations = font.get('variations', [])
        if variations:
            console.print("[gray]   Variations:[/]")
            for variation in variations:
                console.print(f"[gray]     • Size: {variation.get('fontSize', '')} ({variation.get('fontSizePx', 0)}px) | Weight: {variation.get('fontWeight', '')} | Style: {variation.get('fontStyle', '')}[/]")
                console.print(f"[gray]       Used {variation.get('usageCount', 0)} time(s) in: {', '.join(variation.get('elements', []))}[/]")
                sample_text = variation.get('sampleText', '')
                if sample_text:
                    console.print(f"[gray]       Sample: \"{sample_text[:50]}...\"[/]")
    
    if len(fonts) > 10:
        console.print(f"\n[gray]   ... and {len(fonts) - 10} more font family(ies)[/]")
    
    # Declared but potentially unused fonts
    declared_fonts = font_data.get('declaredFonts', [])
    used_font_families = {f.get('fontFamily', '') for f in fonts}
    unused_fonts = [f for f in declared_fonts if f not in used_font_families]
    
    if unused_fonts:
        console.print("\n\n[bold yellow]📋 DECLARED BUT UNUSED FONTS:[/]")
        console.print("[gray]─[/]" * 55)
        for font in unused_fonts[:10]:
            console.print(f"[white]   • {font}[/]")
        if len(unused_fonts) > 10:
            console.print(f"[gray]   ... and {len(unused_fonts) - 10} more[/]")
    
    # Font Files
    font_files = font_data.get('fontFiles', [])
    if font_files:
        console.print("\n\n[bold yellow]📦 FONT FILES LOADED:[/]")
        console.print("[gray]─[/]" * 55)
        for font_file in font_files[:15]:
            url_short = font_file.get('url', '')[:80] + ('...' if len(font_file.get('url', '')) > 80 else '')
            console.print(f"[white]   • {url_short}[/]")
            console.print(f"[gray]     Type: {font_file.get('type', 'unknown')} | Status: {font_file.get('status', 'unknown')}[/]")
        if len(font_files) > 15:
            console.print(f"[gray]   ... and {len(font_files) - 15} more font files[/]")
    
    # External Font Sources
    external_fonts = font_data.get('externalFonts', [])
    if external_fonts:
        console.print("\n\n[bold yellow]🔗 EXTERNAL FONT SOURCES:[/]")
        console.print("[gray]─[/]" * 55)
        for font in external_fonts:
            console.print(f"[white]   {font.get('source', '')}: {font.get('url', '')}[/]")
    
    # Variable Fonts
    variable_fonts = font_data.get('variableFonts', [])
    if variable_fonts:
        console.print("\n\n[bold yellow]🎛️  VARIABLE FONTS DETECTED:[/]")
        console.print("[gray]─[/]" * 55)
        for vf in variable_fonts:
            console.print(f"[white]   • {vf.get('fontFamily', 'unknown')}[/]")
            if vf.get('hasVariationSettings'):
                console.print(f"[gray]     Has font-variation-settings[/]")
    
    # CSS Imports
    css_imports = font_data.get('cssImports', [])
    if css_imports:
        console.print("\n\n[bold yellow]📥 CSS @IMPORT STATEMENTS:[/]")
        console.print("[gray]─[/]" * 55)
        for imp in css_imports[:10]:
            console.print(f"[white]   • {imp.get('url', '')}[/]")
        if len(css_imports) > 10:
            console.print(f"[gray]   ... and {len(css_imports) - 10} more[/]")
    
    # Loaded Fonts (via Font Loading API)
    loaded_fonts = font_data.get('loadedFonts', [])
    if loaded_fonts:
        console.print("\n\n[bold yellow]✅ FONTS VERIFIED AS LOADED:[/]")
        console.print("[gray]─[/]" * 55)
        loaded_by_family = {}
        for lf in loaded_fonts:
            family = lf.get('fontFamily', 'unknown')
            if family not in loaded_by_family:
                loaded_by_family[family] = []
            loaded_by_family[family].append(f"{lf.get('weight', '')}/{lf.get('style', '')}")
        for family, variants in list(loaded_by_family.items())[:10]:
            console.print(f"[white]   • {family}: {', '.join(set(variants))}[/]")
        if len(loaded_by_family) > 10:
            console.print(f"[gray]   ... and {len(loaded_by_family) - 10} more font families[/]")
    
    # AI Analysis Section
    if ai_analysis:
        console.print("\n\n[bold yellow]🤖 AI TYPOGRAPHY ANALYSIS:[/]")
        console.print("[gray]─[/]" * 55)
        
        analysis = ai_analysis.get('analysis', {})
        if analysis:
            console.print("\n[bold white]📊 Overall Assessment:[/]")
            console.print(f"[white]   Quality: {analysis.get('overallQuality', 'N/A')}[/]")
            console.print(f"[white]   Hierarchy: {analysis.get('hierarchy', 'N/A')}[/]")
            console.print(f"[white]   Readability: {analysis.get('readability', 'N/A')}[/]")
            console.print(f"[white]   Style: {analysis.get('style', 'N/A')}[/]")
        
        font_pairings = ai_analysis.get('fontPairings', [])
        if font_pairings:
            console.print("\n[bold white]🎨 Suggested Font Pairings:[/]")
            for index, pairing in enumerate(font_pairings, 1):
                console.print(f"\n[white]   {index}. [bold]{pairing.get('primary', '')}[/] + [bold]{pairing.get('secondary', '')}[/][/]")
                reason = pairing.get('reason', '')
                if reason:
                    console.print(f"[gray]      {reason}[/]")
                use_case = pairing.get('useCase', '')
                if use_case:
                    console.print(f"[gray]      Best for: {use_case}[/]")
        
        recommendations = ai_analysis.get('recommendations', [])
        if recommendations:
            console.print("\n[bold white]💡 Recommendations:[/]")
            for index, rec in enumerate(recommendations, 1):
                console.print(f"[white]   {index}. {rec}[/]")
        
        issues = ai_analysis.get('issues', [])
        if issues:
            console.print("\n[bold red]⚠️  Issues Found:[/]")
            for index, issue in enumerate(issues, 1):
                console.print(f"[red]   {index}. {issue}[/]")
    
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/]\n")
