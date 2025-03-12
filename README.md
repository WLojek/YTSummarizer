# YouTube Video Summarizer

This program takes a YouTube video URL as input and generates three different summaries of varying complexity in English or Polish using OpenAI's API.

## Features

- Extracts transcripts from YouTube videos
- Generates three different summary levels:
  - Simple: A brief overview
  - Moderate: A more detailed summary
  - Complex: A comprehensive analysis
- Supports two languages:
  - English (eng): Default language
  - Polish (pl): Full Polish translation
- Uses OpenAI's o3-mini model by default
- Secure API key handling through environment variables

## Installation

1. Clone this repository

2. Create and activate a virtual environment:
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate on macOS/Linux:
   source venv/bin/activate
   # OR on Windows:
   .\venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and add your OpenAI API key:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` and replace `your_openai_api_key_here` with your actual OpenAI API key

## Usage

Run the script with a YouTube URL and optional language parameter:
```bash
# For English summaries (default)
python yt_summarizer.py https://www.youtube.com/watch?v=VIDEO_ID

# For Polish summaries
python yt_summarizer.py https://www.youtube.com/watch?v=VIDEO_ID pl
```

If no URL is provided, the script will use a default video URL.
If no language is specified, English (eng) will be used.

Valid language options:
- eng: English summaries
- pl: Polish summaries (Podsumowania po Polsku)

### Output Format

The script will generate three levels of summaries in the selected language:

For English (eng):
- Simple Summary (2-3 sentences)
- Moderate Summary (4-6 sentences)
- Complex Summary (comprehensive analysis)

For Polish (pl):
- Podsumowanie Proste (2-3 zdania)
- Podsumowanie Średnio Zaawansowane (4-6 zdań)
- Podsumowanie Złożone (szczegółowa analiza)

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for accessing YouTube and OpenAI API 