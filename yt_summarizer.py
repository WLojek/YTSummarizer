import os
import sys
from typing import List, Dict
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from openai import OpenAI
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Get the directory containing this script
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file in the same directory as this script
load_dotenv(BASE_DIR / '.env')

class YouTubeSummarizer:
    def __init__(self, model="o3-mini"):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found. Please set it in your .env file.")
        
        # Initialize OpenAI client
        os.environ["OPENAI_API_KEY"] = self.openai_api_key
        
        try:
            self.client = OpenAI(
                api_key=self.openai_api_key
            )
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                self.client = None
                print("WARNING: Failed to initialize OpenAI client with default parameters.")
                print("Will use environment variable for authentication instead.")
            else:
                raise
        
        self.model = model

    def extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        parsed_url = urlparse(url)
        if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
            if parsed_url.path == '/watch':
                return parse_qs(parsed_url.query)['v'][0]
        elif parsed_url.hostname == 'youtu.be':
            return parsed_url.path[1:]
        raise ValueError("Invalid YouTube URL")

    def get_transcript(self, video_id: str) -> str:
        """Get transcript from YouTube video."""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Directly format the transcript as a string
            formatted_transcript = ""
            for entry in transcript:
                if isinstance(entry, dict) and 'text' in entry:
                    formatted_transcript += entry['text'] + " "
            
            if not formatted_transcript:
                raise Exception("Could not extract text from transcript")
                
            return formatted_transcript.strip()
        except Exception as e:
            raise Exception(f"Error getting transcript: {str(e)}")

    def generate_summary(self, text: str, complexity: str) -> str:
        """Generate summary using OpenAI API."""
        prompts = {
            "simple": "Provide a brief, simple overview of the main points in 2-3 sentences:",
            "moderate": "Create a detailed summary that covers the key points and important details in 4-6 sentences:",
            "complex": "Generate a comprehensive analysis including main themes, key arguments, and important details. Include any relevant context and implications:"
        }

        try:
            # Base parameters for all models
            params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that summarizes content."},
                    {"role": "user", "content": f"{prompts[complexity]}\n\n{text}"}
                ]
            }

            # Add model-specific parameters
            if self.model == "o3-mini":
                params.update({
                    "max_completion_tokens": 2000 if complexity == "complex" else 1000
                })
            else:  # For other OpenAI models
                params.update({
                    "temperature": 0.7,
                    "max_tokens": 2000 if complexity == "complex" else 1000
                })
                
            # Send the request
            if self.client is None:
                import openai
                response = openai.chat.completions.create(**params)
            else:
                response = self.client.chat.completions.create(**params)
                
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Error generating summary: {str(e)}")

    def translate_to_polish(self, text: str) -> str:
        """Translate text to Polish using OpenAI API."""
        try:
            params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful translator. Translate the following text to Polish, maintaining the same tone and style:"},
                    {"role": "user", "content": text}
                ]
            }

            # Add model-specific parameters
            if self.model == "o3-mini":
                params.update({
                    "max_completion_tokens": 2000
                })
            else:
                params.update({
                    "temperature": 0.7,
                    "max_tokens": 2000
                })

            if self.client is None:
                import openai
                response = openai.chat.completions.create(**params)
            else:
                response = self.client.chat.completions.create(**params)

            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Error translating to Polish: {str(e)}")

    def summarize_video(self, url: str) -> Dict[str, Dict[str, str]]:
        """Main function to summarize YouTube video."""
        video_id = self.extract_video_id(url)
        transcript = self.get_transcript(video_id)
        
        results = {
            "english": {},
            "polish": {}
        }
        
        for complexity in ["simple", "moderate", "complex"]:
            # Generate English summary
            english_summary = self.generate_summary(transcript, complexity)
            results["english"][complexity] = english_summary
            
            # Translate to Polish
            polish_summary = self.translate_to_polish(english_summary)
            results["polish"][complexity] = polish_summary
        
        return results

def main():
    # Default URL and language if none provided
    default_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    default_language = "eng"
    valid_languages = ["eng", "pl"]
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print(f"No URL provided. Using default URL: {default_url}")
        youtube_url = default_url
        language = default_language
    else:
        youtube_url = sys.argv[1]
        language = sys.argv[2] if len(sys.argv) > 2 else default_language
        
        # Validate language parameter
        if language not in valid_languages:
            print(f"Invalid language parameter: {language}")
            print(f"Valid options are: {', '.join(valid_languages)}")
            print(f"Using default language: {default_language}")
            language = default_language
        
    print(f"Summarizing video: {youtube_url}")
    print(f"Language: {'English' if language == 'eng' else 'Polish'}")
    summarizer = YouTubeSummarizer()

    try:
        summaries = summarizer.summarize_video(youtube_url)
        
        if language == "eng":
            # Print English summaries
            print("\n=== English Summaries ===")
            print("\n--- Simple Summary ---")
            print(summaries["english"]["simple"])
            
            print("\n--- Moderate Summary ---")
            print(summaries["english"]["moderate"])
            
            print("\n--- Complex Summary ---")
            print(summaries["english"]["complex"])
        else:  # language == "pl"
            # Print Polish translations
            print("\n=== Podsumowania po Polsku ===")
            print("\n--- Podsumowanie Proste ---")
            print(summaries["polish"]["simple"])
            
            print("\n--- Podsumowanie Średnio Zaawansowane ---")
            print(summaries["polish"]["moderate"])
            
            print("\n--- Podsumowanie Złożone ---")
            print(summaries["polish"]["complex"])

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 