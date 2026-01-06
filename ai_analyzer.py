from openai import OpenAI
from openai import APIError, AuthenticationError, RateLimitError
from typing import Dict, Any, Optional
import json

def get_ai_analysis(font_data: Dict[str, Any], api_key: str, model: str = 'gpt-4o-mini') -> Optional[Dict[str, Any]]:
    """Uses AI to analyze typography and suggest font pairings"""
    
    client = OpenAI(api_key=api_key)
    
    # Prepare font data for AI analysis
    fonts_summary = []
    for index, font in enumerate(font_data.get('fonts', []), 1):
        fonts_summary.append({
            'rank': index,
            'fontFamily': font.get('fontFamily', ''),
            'totalUsageCount': font.get('totalUsageCount', 0),
            'elements': font.get('elements', []),
            'variations': [
                {
                    'fontSize': v.get('fontSize', ''),
                    'fontSizePx': v.get('fontSizePx', 0),
                    'fontWeight': v.get('fontWeight', ''),
                    'fontStyle': v.get('fontStyle', ''),
                    'usageCount': v.get('usageCount', 0),
                    'elements': v.get('elements', []),
                    'sampleText': v.get('sampleText', '')
                }
                for v in font.get('variations', [])
            ]
        })
    
    # Limit font data to prevent token limit issues (keep top 20 fonts)
    limited_fonts_summary = fonts_summary[:20]
    total_fonts_count = len(fonts_summary)
    font_data_note = f"Font Data (Used Fonts)" if total_fonts_count <= 20 else f"Font Data (Used Fonts - showing top 20 of {total_fonts_count} total)"
    
    prompt = f"""You are a typography expert. Analyze the following font usage data from a website and provide:

1. **Typography Analysis**: 
   - Overall typography quality and consistency
   - Font hierarchy assessment
   - Readability evaluation
   - Design style classification (modern, classic, minimalist, etc.)

2. **Font Pairing Suggestions**:
   - Suggest 3-5 complementary font pairings that would work well with the existing fonts
   - Explain why each pairing works
   - Include both serif/sans-serif combinations and alternative options

3. **Recommendations**:
   - Specific improvements for font sizes, weights, and spacing
   - Suggestions for better typography hierarchy
   - Any issues or inconsistencies found

{font_data_note}:
{json.dumps(limited_fonts_summary, indent=2)}

Declared but Unused Fonts:
{json.dumps([f for f in font_data.get('declaredFonts', []) if f not in [font.get('fontFamily', '') for font in font_data.get('fonts', [])]], indent=2)}

External Font Sources:
{json.dumps(font_data.get('externalFonts', []), indent=2)}

@font-face Declarations:
{json.dumps(font_data.get('fontFaces', []), indent=2)}

Font Files Loaded:
{json.dumps(font_data.get('fontFiles', [])[:20], indent=2)}

Variable Fonts:
{json.dumps(font_data.get('variableFonts', []), indent=2)}

Provide your analysis in a structured JSON format with the following structure:
{{
  "analysis": {{
    "overallQuality": "rating and brief description",
    "hierarchy": "assessment of font hierarchy",
    "readability": "readability evaluation",
    "style": "design style classification"
  }},
  "fontPairings": [
    {{
      "primary": "font name",
      "secondary": "font name",
      "reason": "why this pairing works",
      "useCase": "best use case for this pairing"
    }}
  ],
  "recommendations": [
    "specific recommendation 1",
    "specific recommendation 2"
  ],
  "issues": [
    "issue 1 if any",
    "issue 2 if any"
  ]
}}"""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are an expert typographer and web design consultant. Provide detailed, actionable typography analysis and recommendations. Always respond with valid JSON only.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            temperature=0.7,
            response_format={'type': 'json_object'}
        )
        
        content = response.choices[0].message.content
        if not content:
            raise Exception('Empty response from AI')
        
        # Parse JSON with better error handling
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            raise Exception(f'Invalid JSON response from AI: {str(e)}\nResponse: {content[:200]}')
        
        # Validate response structure
        if not isinstance(result, dict):
            raise Exception('AI response is not a JSON object')
        
        # Ensure required fields exist (with defaults if missing)
        if 'analysis' not in result:
            result['analysis'] = {}
        if 'fontPairings' not in result:
            result['fontPairings'] = []
        if 'recommendations' not in result:
            result['recommendations'] = []
        if 'issues' not in result:
            result['issues'] = []
        
        return result
    except AuthenticationError as e:
        raise Exception(f'OpenAI API authentication failed. Please check your API key: {str(e)}')
    except RateLimitError as e:
        raise Exception(f'OpenAI API rate limit exceeded. Please try again later: {str(e)}')
    except APIError as e:
        raise Exception(f'OpenAI API error: {str(e)}')
    except Exception as e:
        if 'AI Analysis failed' in str(e):
            raise
        raise Exception(f'AI Analysis failed: {str(e)}')
