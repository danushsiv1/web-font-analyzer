from playwright.sync_api import sync_playwright
from typing import Dict, List, Any
import re

def analyze_fonts(url: str, verbose: bool = False) -> Dict[str, Any]:
    """Extracts comprehensive font information from a webpage using Chromium (Playwright)"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Track network requests for font files
        font_files = []
        
        def handle_response(response):
            content_type = response.headers.get('content-type', '').lower()
            url_path = response.url.lower()
            # Only track actual font files, not SVG images
            if any(ext in url_path for ext in ['.woff', '.woff2', '.ttf', '.otf', '.eot']):
                font_files.append({
                    'url': response.url,
                    'type': content_type or 'font',
                    'status': response.status
                })
            elif ('font' in content_type and 'svg' not in content_type) or 'woff' in content_type or 'ttf' in content_type or 'opentype' in content_type:
                font_files.append({
                    'url': response.url,
                    'type': content_type,
                    'status': response.status
                })
        
        page.on("response", handle_response)
        
        page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Wait for fonts to actually load
        page.wait_for_function("document.fonts && document.fonts.ready", timeout=10000)
        
        # Scroll to trigger lazy-loaded content
        page.evaluate("""
            () => {
                window.scrollTo(0, document.body.scrollHeight);
                return new Promise(resolve => setTimeout(resolve, 1000));
            }
        """)
        
        # Wait a bit more for any lazy-loaded fonts
        page.wait_for_timeout(2000)
        
        # Extract font information using JavaScript
        fonts_data = page.evaluate("""
            () => {
                const fontsByFamily = new Map();
                const allElements = document.querySelectorAll('*');
                
                allElements.forEach(element => {
                    const computedStyle = window.getComputedStyle(element);
                    const fontFamily = computedStyle.fontFamily;
                    const fontSize = computedStyle.fontSize;
                    const fontWeight = computedStyle.fontWeight;
                    const fontStyle = computedStyle.fontStyle;
                    const lineHeight = computedStyle.lineHeight;
                    const letterSpacing = computedStyle.letterSpacing;
                    const textTransform = computedStyle.textTransform;
                    const color = computedStyle.color;
                    const tagName = element.tagName.toLowerCase();
                    
                    if (!element.textContent || element.textContent.trim().length === 0) {
                        return;
                    }

                    const cleanFontFamily = fontFamily.split(',')[0].replace(/['"]/g, '').trim();
                    
                    if (!fontsByFamily.has(cleanFontFamily)) {
                        fontsByFamily.set(cleanFontFamily, {
                            fontFamily: cleanFontFamily,
                            variations: new Map(),
                            allElements: new Set(),
                            totalUsageCount: 0
                        });
                    }
                    
                    const fontFamilyInfo = fontsByFamily.get(cleanFontFamily);
                    fontFamilyInfo.allElements.add(tagName);
                    fontFamilyInfo.totalUsageCount++;
                    
                    const variationKey = `${fontSize}|${fontWeight}|${fontStyle}`;
                    
                    if (!fontFamilyInfo.variations.has(variationKey)) {
                        fontFamilyInfo.variations.set(variationKey, {
                            fontSize: fontSize,
                            fontSizePx: parseFloat(fontSize),
                            fontWeight: fontWeight,
                            fontStyle: fontStyle,
                            lineHeight: lineHeight,
                            lineHeightValue: lineHeight === 'normal' ? null : parseFloat(lineHeight),
                            letterSpacing: letterSpacing,
                            letterSpacingValue: letterSpacing === 'normal' ? 0 : parseFloat(letterSpacing),
                            textTransform: textTransform,
                            color: color,
                            usageCount: 0,
                            elements: [],
                            sampleText: element.textContent.trim().substring(0, 100)
                        });
                    }
                    
                    const variation = fontFamilyInfo.variations.get(variationKey);
                    variation.usageCount++;
                    
                    if (!variation.elements.includes(tagName)) {
                        variation.elements.push(tagName);
                    }
                });

                return Array.from(fontsByFamily.values())
                    .map(font => ({
                        fontFamily: font.fontFamily,
                        totalUsageCount: font.totalUsageCount,
                        elements: Array.from(font.allElements),
                        variations: Array.from(font.variations.values())
                            .sort((a, b) => b.usageCount - a.usageCount)
                    }))
                    .sort((a, b) => b.totalUsageCount - a.totalUsageCount);
            }
        """)
        
        # Get @font-face declarations
        font_faces = page.evaluate("""
            () => {
                const faces = [];
                const styleSheets = Array.from(document.styleSheets);
                
                styleSheets.forEach(sheet => {
                    try {
                        const rules = Array.from(sheet.cssRules || []);
                        rules.forEach(rule => {
                            if (rule instanceof CSSFontFaceRule) {
                                faces.push({
                                    fontFamily: rule.style.fontFamily,
                                    fontStyle: rule.style.fontStyle || 'normal',
                                    fontWeight: rule.style.fontWeight || 'normal',
                                    src: rule.style.src
                                });
                            }
                        });
                    } catch (e) {
                        // Cross-origin stylesheets may throw errors
                    }
                });
                
                return faces;
            }
        """)
        
        # Get external font links and preloads
        external_fonts = page.evaluate("""
            () => {
                const fonts = [];
                const links = document.querySelectorAll('link');
                
                links.forEach(link => {
                    const href = link.href;
                    const rel = link.rel || '';
                    const asAttr = link.getAttribute('as') || '';
                    
                    // Check for font preloading
                    if (rel.includes('preload') && (asAttr === 'font' || href.match(/\\.(woff|woff2|ttf|otf|eot)/i))) {
                        fonts.push({
                            source: 'Preloaded Font',
                            url: href,
                            type: asAttr || 'font'
                        });
                    }
                    // Google Fonts
                    else if (href.includes('fonts.googleapis.com') || href.includes('fonts.gstatic.com')) {
                        fonts.push({
                            source: 'Google Fonts',
                            url: href
                        });
                    }
                    // Adobe Fonts
                    else if (href.includes('use.typekit.net') || href.includes('adobe.com/fonts')) {
                        fonts.push({
                            source: 'Adobe Fonts',
                            url: href
                        });
                    }
                    // Fonts.com
                    else if (href.includes('fonts.com') || href.includes('fast.fonts.net')) {
                        fonts.push({
                            source: 'Fonts.com',
                            url: href
                        });
                    }
                    // Other font-related links
                    else if (rel.includes('stylesheet') && (href.includes('font') || href.includes('typeface'))) {
                        fonts.push({
                            source: 'External Stylesheet',
                            url: href
                        });
                    }
                });
                
                return fonts;
            }
        """)
        
        # Discover all fonts declared in CSS (even if not used)
        declared_fonts = page.evaluate("""
            () => {
                const declaredFontFamilies = new Set();
                const fontFamilyRegex = /font-family\\s*:\\s*([^;]+)/gi;
                const styleSheets = Array.from(document.styleSheets);
                
                styleSheets.forEach(sheet => {
                    try {
                        const rules = Array.from(sheet.cssRules || []);
                        rules.forEach(rule => {
                            let cssText = '';
                            if (rule.cssText) {
                                cssText = rule.cssText;
                            } else if (rule.style && rule.style.cssText) {
                                cssText = rule.style.cssText;
                            }
                            
                            // Extract font-family declarations
                            let match;
                            while ((match = fontFamilyRegex.exec(cssText)) !== null) {
                                const fontFamilies = match[1].split(',').map(f => f.trim().replace(/['"]/g, ''));
                                fontFamilies.forEach(f => {
                                    if (f && f !== 'inherit' && f !== 'initial' && f !== 'unset') {
                                        declaredFontFamilies.add(f);
                                    }
                                });
                            }
                        });
                    } catch (e) {
                        // Cross-origin stylesheets may throw errors
                    }
                });
                
                // Also check inline styles
                const allElements = document.querySelectorAll('*');
                allElements.forEach(element => {
                    const inlineStyle = element.getAttribute('style');
                    if (inlineStyle) {
                        let match;
                        while ((match = fontFamilyRegex.exec(inlineStyle)) !== null) {
                            const fontFamilies = match[1].split(',').map(f => f.trim().replace(/['"]/g, ''));
                            fontFamilies.forEach(f => {
                                if (f && f !== 'inherit' && f !== 'initial' && f !== 'unset') {
                                    declaredFontFamilies.add(f);
                                }
                            });
                        }
                    }
                });
                
                return Array.from(declaredFontFamilies);
            }
        """)
        
        # Get all font-face rules with more details
        detailed_font_faces = page.evaluate("""
            () => {
                const faces = [];
                const styleSheets = Array.from(document.styleSheets);
                
                styleSheets.forEach(sheet => {
                    try {
                        const rules = Array.from(sheet.cssRules || []);
                        rules.forEach(rule => {
                            if (rule instanceof CSSFontFaceRule) {
                                const style = rule.style;
                                faces.push({
                                    fontFamily: style.fontFamily || 'unknown',
                                    fontStyle: style.fontStyle || 'normal',
                                    fontWeight: style.fontWeight || 'normal',
                                    fontStretch: style.fontStretch || 'normal',
                                    fontDisplay: style.fontDisplay || 'auto',
                                    unicodeRange: style.unicodeRange || '',
                                    src: style.src || '',
                                    fontVariationSettings: style.fontVariationSettings || ''
                                });
                            }
                        });
                    } catch (e) {
                        // Cross-origin stylesheets may throw errors
                    }
                });
                
                return faces;
            }
        """)
        
        # Check for variable fonts
        variable_fonts = page.evaluate("""
            () => {
                const variableFonts = [];
                const styleSheets = Array.from(document.styleSheets);
                
                styleSheets.forEach(sheet => {
                    try {
                        const rules = Array.from(sheet.cssRules || []);
                        rules.forEach(rule => {
                            if (rule instanceof CSSFontFaceRule) {
                                const style = rule.style;
                                const src = style.src || '';
                                // Check for variable font indicators
                                if (src.includes('variable') || 
                                    src.includes('VF') || 
                                    style.fontVariationSettings ||
                                    (style.fontWeight && style.fontWeight.includes(' '))) {
                                    variableFonts.push({
                                        fontFamily: style.fontFamily || 'unknown',
                                        src: src,
                                        hasVariationSettings: !!style.fontVariationSettings
                                    });
                                }
                            }
                        });
                    } catch (e) {
                        // Cross-origin stylesheets may throw errors
                    }
                });
                
                return variableFonts;
            }
        """)
        
        # Get CSS @import statements that might load fonts
        css_imports = page.evaluate("""
            () => {
                const imports = [];
                const styleSheets = Array.from(document.styleSheets);
                
                styleSheets.forEach(sheet => {
                    try {
                        const rules = Array.from(sheet.cssRules || []);
                        rules.forEach(rule => {
                            if (rule instanceof CSSImportRule) {
                                imports.push({
                                    url: rule.href,
                                    media: rule.media.mediaText || 'all'
                                });
                            }
                        });
                    } catch (e) {
                        // Cross-origin stylesheets may throw errors
                    }
                });
                
                return imports;
            }
        """)
        
        # Check document.fonts API for loaded fonts
        loaded_fonts = page.evaluate("""
            () => {
                if (!document.fonts || !document.fonts.check) {
                    return [];
                }
                
                const loaded = [];
                const fontFamilies = new Set();
                
                // Get all unique font families from the page
                const allElements = document.querySelectorAll('*');
                allElements.forEach(element => {
                    const style = window.getComputedStyle(element);
                    const families = style.fontFamily.split(',');
                    families.forEach(f => {
                        const clean = f.trim().replace(/['"]/g, '');
                        if (clean && !['inherit', 'initial', 'unset', 'serif', 'sans-serif', 'monospace', 'cursive', 'fantasy'].includes(clean)) {
                            fontFamilies.add(clean);
                        }
                    });
                });
                
                // Check which fonts are actually loaded
                fontFamilies.forEach(family => {
                    try {
                        // Try different weights/styles
                        for (let weight of ['400', '700']) {
                            for (let style of ['normal', 'italic']) {
                                if (document.fonts.check(`12px "${family}"`, weight)) {
                                    loaded.push({
                                        fontFamily: family,
                                        weight: weight,
                                        style: style,
                                        status: 'loaded'
                                    });
                                    break;
                                }
                            }
                        }
                    } catch (e) {
                        // Font check failed
                    }
                });
                
                return loaded;
            }
        """)
        
        # Extract fonts from iframes (if accessible)
        iframe_fonts = []
        try:
            for frame in page.frames:
                if frame != page.main_frame:  # Skip main frame (already processed)
                    try:
                        iframe_font_data = frame.evaluate("""
                            () => {
                                const fontsByFamily = new Map();
                                const allElements = document.querySelectorAll('*');
                                
                                allElements.forEach(element => {
                                    const computedStyle = window.getComputedStyle(element);
                                    const fontFamily = computedStyle.fontFamily;
                                    const fontSize = computedStyle.fontSize;
                                    const fontWeight = computedStyle.fontWeight;
                                    const fontStyle = computedStyle.fontStyle;
                                    const tagName = element.tagName.toLowerCase();
                                    
                                    if (!element.textContent || element.textContent.trim().length === 0) {
                                        return;
                                    }
                                    
                                    const cleanFontFamily = fontFamily.split(',')[0].replace(/['"]/g, '').trim();
                                    
                                    if (!fontsByFamily.has(cleanFontFamily)) {
                                        fontsByFamily.set(cleanFontFamily, {
                                            fontFamily: cleanFontFamily,
                                            variations: new Map(),
                                            allElements: new Set(),
                                            totalUsageCount: 0
                                        });
                                    }
                                    
                                    const fontFamilyInfo = fontsByFamily.get(cleanFontFamily);
                                    fontFamilyInfo.allElements.add(tagName);
                                    fontFamilyInfo.totalUsageCount++;
                                    
                                    const variationKey = `${fontSize}|${fontWeight}|${fontStyle}`;
                                    
                                    if (!fontFamilyInfo.variations.has(variationKey)) {
                                        fontFamilyInfo.variations.set(variationKey, {
                                            fontSize: fontSize,
                                            fontSizePx: parseFloat(fontSize),
                                            fontWeight: fontWeight,
                                            fontStyle: fontStyle,
                                            usageCount: 0,
                                            elements: [],
                                            sampleText: element.textContent.trim().substring(0, 100)
                                        });
                                    }
                                    
                                    const variation = fontFamilyInfo.variations.get(variationKey);
                                    variation.usageCount++;
                                    
                                    if (!variation.elements.includes(tagName)) {
                                        variation.elements.push(tagName);
                                    }
                                });
                                
                                return Array.from(fontsByFamily.values())
                                    .map(font => ({
                                        fontFamily: font.fontFamily,
                                        totalUsageCount: font.totalUsageCount,
                                        elements: Array.from(font.allElements),
                                        variations: Array.from(font.variations.values())
                                            .sort((a, b) => b.usageCount - a.usageCount)
                                    }))
                                    .sort((a, b) => b.totalUsageCount - a.totalUsageCount);
                            }
                        """)
                        if iframe_font_data:
                            iframe_fonts.extend(iframe_font_data)
                    except Exception:
                        # Cross-origin iframes or other errors - skip silently
                        pass
        except Exception:
            # Iframe access failed - continue without iframe fonts
            pass
        
        # Merge iframe fonts with main page fonts
        all_fonts = fonts_data or []
        if iframe_fonts:
            # Create a map to merge fonts by family
            fonts_dict = {f['fontFamily']: f for f in all_fonts}
            for iframe_font in iframe_fonts:
                family = iframe_font['fontFamily']
                if family in fonts_dict:
                    # Merge variations and update counts
                    existing = fonts_dict[family]
                    existing['totalUsageCount'] += iframe_font['totalUsageCount']
                    existing_variations = {f"{v['fontSize']}|{v['fontWeight']}|{v['fontStyle']}": v 
                                          for v in existing['variations']}
                    for var in iframe_font['variations']:
                        var_key = f"{var['fontSize']}|{var['fontWeight']}|{var['fontStyle']}"
                        if var_key in existing_variations:
                            existing_variations[var_key]['usageCount'] += var['usageCount']
                        else:
                            existing['variations'].append(var)
                    existing['elements'] = list(set(existing['elements'] + iframe_font['elements']))
                else:
                    all_fonts.append(iframe_font)
        
        browser.close()
        
        return {
            'fonts': all_fonts,
            'fontFaces': detailed_font_faces or [],
            'externalFonts': external_fonts or [],
            'fontFiles': font_files,
            'declaredFonts': declared_fonts or [],
            'variableFonts': variable_fonts or [],
            'cssImports': css_imports or [],
            'loadedFonts': loaded_fonts or [],
            'url': url
        }
