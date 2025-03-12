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
    def __init__(self, model="o3-mini", language="eng"):
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
        self.language = language

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
        """Generate summary using OpenAI API with streaming."""
        prompts = {
            "simple": {
                "eng": "Provide a brief, simple overview of the main points in 2-3 sentences:",
                "pl": "Przedstaw krótkie podsumowanie głównych punktów w 2-3 zdaniach:"
            },
            "moderate": {
                "eng": "Create a detailed summary that covers the key points and important details in 4-6 sentences:",
                "pl": "Stwórz szczegółowe podsumowanie obejmujące kluczowe punkty i ważne detale w 4-6 zdaniach:"
            },
            "complex": {
                "eng": "Generate a comprehensive analysis including main themes, key arguments, and important details. Include any relevant context and implications:",
                "pl": "Stwórz kompleksową analizę zawierającą główne tematy, kluczowe argumenty i ważne szczegóły. Uwzględnij odpowiedni kontekst i implikacje:"
            }
        }

        try:
            # Base parameters for all models
            params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that summarizes content. " + 
                     ("Respond in Polish." if self.language == "pl" else "Respond in English.")},
                    {"role": "user", "content": f"{prompts[complexity][self.language]}\n\n{text}"}
                ],
                "stream": True  # Enable streaming
            }

            # Add model-specific parameters
            if self.model == "o3-mini":
                params.update({
                    "max_completion_tokens": 4000 if complexity == "complex" else 1000
                })
            else:  # For other OpenAI models
                params.update({
                    "temperature": 0.7,
                    "max_tokens": 4000 if complexity == "complex" else 1000
                })
                
            # Send the request and stream the response
            full_response = ""
            if self.client is None:
                import openai
                stream = openai.chat.completions.create(**params)
            else:
                stream = self.client.chat.completions.create(**params)

            # Process the stream
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    print(content, end='', flush=True)
                    full_response += content

            print()  # New line after streaming completes
            return full_response.strip()
        except Exception as e:
            raise Exception(f"Error generating summary: {str(e)}")

    def summarize_video(self, url: str) -> Dict[str, Dict[str, str]]:
        """Main function to summarize YouTube video."""
        video_id = self.extract_video_id(url)
        transcript = self.get_transcript(video_id)
        
        results = {
            "english": {},
            "polish": {}
        }
        
        for complexity in ["simple", "moderate", "complex"]:
            # Print header in the selected language
            if complexity == "simple":
                print("\n=== {} ===".format(
                    "Podsumowanie Proste" if self.language == "pl" else "Simple Summary"
                ))
            elif complexity == "moderate":
                print("\n=== {} ===".format(
                    "Podsumowanie Średnio Zaawansowane" if self.language == "pl" else "Moderate Summary"
                ))
            else:
                print("\n=== {} ===".format(
                    "Podsumowanie Złożone" if self.language == "pl" else "Complex Summary"
                ))

            # Generate summary in the selected language
            summary = self.generate_summary(transcript, complexity)
            if self.language == "eng":
                results["english"][complexity] = summary
            else:
                results["polish"][complexity] = summary
            
            print("\n")  # Add spacing between sections
        
        return results

def main():
    # Default URL and language if none provided
    default_url = ""
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
    
    # Pass language parameter to the summarizer
    summarizer = YouTubeSummarizer(language=language)

    try:
        summaries = summarizer.summarize_video(youtube_url)
        
        # Store results but don't display them again since they were streamed in real-time
        if language == "eng":
            selected_summaries = summaries["english"]
        else:
            selected_summaries = summaries["polish"]

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 