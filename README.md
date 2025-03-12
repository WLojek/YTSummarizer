# YouTube Video Summarizer

This program takes a YouTube video URL as input and generates three different summaries of varying complexity in both English and Polish using OpenAI's API.

## Features

- Extracts transcripts from YouTube videos
- Generates three different summary levels in English:
  - Simple: A brief overview
  - Moderate: A more detailed summary
  - Complex: A comprehensive analysis
- Automatically translates all summaries to Polish:
  - Podsumowanie Proste: Simple summary in Polish
  - Podsumowanie Średnio Zaawansowane: Moderate summary in Polish
  - Podsumowanie Złożone: Complex summary in Polish
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

Run the script with a YouTube URL:
```bash
python yt_summarizer.py https://www.youtube.com/watch?v=VIDEO_ID
```

If no URL is provided, the script will use a default video URL.

### Output Format

The script will generate:
1. English Summaries:
   - Simple Summary (2-3 sentences)
   - Moderate Summary (4-6 sentences)
   - Complex Summary (comprehensive analysis)

2. Polish Translations:
   - Podsumowanie Proste (2-3 zdania)
   - Podsumowanie Średnio Zaawansowane (4-6 zdań)
   - Podsumowanie Złożone (szczegółowa analiza)

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for accessing YouTube and OpenAI API 