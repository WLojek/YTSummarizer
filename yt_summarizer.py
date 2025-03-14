import os
import sys
from typing import List, Dict
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from openai import OpenAI
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Custom exception classes
class TranscriptNotFoundError(Exception):
    """Raised when the transcript list cannot be retrieved for a video."""
    pass

class NoTranscriptAvailableError(Exception):
    """Raised when no transcript is available in any attempted format."""
    pass

class TranslationError(Exception):
    """Raised when translation of the transcript fails."""
    pass

class TranscriptProcessingError(Exception):
    """Raised when there's an error processing or formatting the transcript."""
    pass

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
            # Map our language codes to YouTube's language codes
            language_map = {
                "eng": "en",
                "pl": "pl"
            }
            
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            except Exception as e:
                raise TranscriptNotFoundError(f"Could not retrieve transcript list for video {video_id}: {str(e)}")
            
            transcript = None
            manual_error = None
            auto_error = None
            translation_error = None
            
            # Try different methods to get the transcript
            try:
                # First try to get manual transcript in the requested language
                transcript = transcript_list.find_transcript([language_map[self.language]]).fetch()
            except Exception as e:
                manual_error = f"Manual transcript not available in {self.language}: {str(e)}"
                try:
                    # Then try to get auto-generated transcript in the requested language
                    transcript = transcript_list.find_generated_transcript([language_map[self.language]]).fetch()
                except Exception as e:
                    auto_error = f"Auto-generated transcript not available in {self.language}: {str(e)}"
                    try:
                        # Try to find any available auto-generated transcript and translate it
                        for transcript_data in transcript_list._manually_created_transcripts.values():
                            if transcript_data.is_generated:
                                if self.language == "eng":
                                    # If English is requested, translate to English
                                    transcript = transcript_data.translate('en').fetch()
                                else:
                                    # If target language is requested, try to translate to it
                                    if transcript_data.language_code != language_map[self.language]:
                                        transcript = transcript_data.translate(language_map[self.language]).fetch()
                                    else:
                                        transcript = transcript_data.fetch()
                                break
                        
                        if transcript is None:
                            # If no transcript found in manually created, try generated ones
                            for transcript_data in transcript_list._generated_transcripts.values():
                                if self.language == "eng":
                                    # If English is requested, translate to English
                                    transcript = transcript_data.translate('en').fetch()
                                else:
                                    # If target language is requested, try to translate to it
                                    if transcript_data.language_code != language_map[self.language]:
                                        transcript = transcript_data.translate(language_map[self.language]).fetch()
                                    else:
                                        transcript = transcript_data.fetch()
                                break
                                
                        if transcript is None:
                            raise NoTranscriptAvailableError("No transcripts available for this video")
                    except Exception as e:
                        translation_error = f"Could not get or translate available transcript: {str(e)}"
                        raise NoTranscriptAvailableError(
                            f"All transcript retrieval methods failed:\n"
                            f"- {manual_error}\n"
                            f"- {auto_error}\n"
                            f"- {translation_error}"
                        )
            
            if transcript is None:
                raise TranscriptProcessingError("No transcript was retrieved despite no errors being raised")
            
            # Format the transcript, handling both dictionary and object formats
            formatted_transcript = ""
            for entry in transcript:
                text = None
                if isinstance(entry, dict):
                    text = entry.get('text', '')
                else:
                    # Handle object format
                    text = getattr(entry, 'text', '')
                
                if text:
                    formatted_transcript += text + " "
            
            formatted_transcript = formatted_transcript.strip()
            if not formatted_transcript:
                raise TranscriptProcessingError("Transcript was retrieved but contained no text")
            
            return formatted_transcript
        
        except (TranscriptNotFoundError, NoTranscriptAvailableError, TranslationError, TranscriptProcessingError) as e:
            # Re-raise these specific errors as they already have descriptive messages
            raise
        except Exception as e:
            raise TranscriptProcessingError(f"Unexpected error while processing transcript: {str(e)}")

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