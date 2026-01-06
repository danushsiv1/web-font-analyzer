# Web Font Analyzer (Python)

An AI-powered web font analyzer that uses Playwright (Chromium) to extract typography information from websites and provides intelligent analysis and font pairing suggestions.

## Features

- 🔍 **Automatic Font Extraction**: Uses Playwright (Chromium) to analyze web pages and extract all font usage
- 🤖 **AI-Powered Analysis**: Leverages OpenAI to provide typography analysis and recommendations
- 🎨 **Font Pairing Suggestions**: Get intelligent suggestions for complementary font combinations
- 📊 **Detailed Reports**: View font sizes, weights, usage counts, and element types
- 🔗 **External Font Detection**: Identifies Google Fonts and other external font sources
- 🐍 **Python Implementation**: Built with Python and Playwright

## Installation

1. Navigate to the project directory:
```bash
cd web-font-analyzer-python
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install chromium
```

5. Set up your OpenAI API key (required for AI analysis):
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or pass it as a command-line argument.

## Usage

### Basic Usage

```bash
python main.py https://example.com
```

### With API Key

```bash
python main.py https://example.com --api-key your-api-key
```

### Options

- `--api-key`: OpenAI API key (or set `OPENAI_API_KEY` env var)
- `--model`: OpenAI model to use (default: `gpt-4o-mini`)
- `--json`: Output results as JSON
- `--verbose`: Show verbose output

### Examples

```bash
# Analyze a website
python main.py https://www.apple.com

# Use a specific model
python main.py https://www.apple.com --model gpt-4

# Output as JSON
python main.py https://www.apple.com --json

# Without AI analysis (just font extraction)
python main.py https://www.apple.com
```

## Output

The tool provides:

1. **Font Usage**: List of all fonts found on the page grouped by family with:
   - Font family name
   - Total usage count
   - All size/weight/style variations
   - Usage count per variation
   - Element types using each variation
   - Sample text

2. **External Font Sources**: Google Fonts and other external font links

3. **AI Analysis** (when API key is provided):
   - Overall typography quality assessment
   - Font hierarchy evaluation
   - Readability analysis
   - Design style classification
   - Font pairing suggestions
   - Specific recommendations
   - Issues found

## Requirements

- Python 3.8+
- OpenAI API key (for AI analysis features)
- Internet connection

## How It Works

1. **Font Extraction**: Uses Playwright to launch a headless Chromium browser, navigate to the target URL, and extract computed font styles from all elements on the page.

2. **Data Processing**: Groups fonts by family, aggregates font usage, identifies unique font combinations, and collects metadata about font sources.

3. **AI Analysis**: Sends the font data to OpenAI's API for intelligent typography analysis and pairing suggestions.

4. **Output Formatting**: Displays results in a human-readable format with rich colors and formatting, or as JSON.

## License

MIT
