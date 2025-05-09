from flask import Flask, jsonify, request
from flask_cors import CORS
import speech_recognition as sr
import threading
import pygame
import tempfile
from gtts import gTTS
import os
import requests
import time
import logging



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('url_tracker.log')
    ]
)

app = Flask(__name__)
# CORS(app)


CORS(app, resources={
    r"/*": {
        "origins": ["chrome-extension://*", "http://localhost:*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Global variables for storing browser data
browser_data = {
    'current_url': '',
    'urls': [],
    'token': '0'
}

class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.wake_words = ["hey vista", "hi vista", "hello vista"]
        
        # Configure speech recognition settings
        self.recognizer.energy_threshold = 800
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 1.2
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 1.0
        
        # Initialize audio playback
        pygame.mixer.init()
        self.temp_dir = tempfile.mkdtemp()
        logging.info("Voice Assistant initialized")

    def text_to_speech(self, text, filename=None):
        """
        Convert text to speech and play it at 1.3x speed
        
        Args:
            text (str): Text to convert to speech
            filename (str, optional): Output filename for the audio file
            
        Raises:
            Exception: If there's an error during TTS conversion or playback
        """
        temp_file = None
        try:
            # Create a temporary file if filename not provided
            if filename is None:
                import tempfile
                temp_fd, temp_file = tempfile.mkstemp(suffix='.mp3', dir=self.temp_dir)
                os.close(temp_fd)  # Close file descriptor
                filename = temp_file
            
            # Create TTS file
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(filename)
            
            # Verify file exists before attempting playback
            if not os.path.exists(filename):
                raise FileNotFoundError(f"Generated audio file not found: {filename}")
            
            # Initialize pygame mixer with higher frequency for faster playback
            pygame.mixer.quit()
            pygame.mixer.init(frequency=114530)  # 88100 * 1.3 for 30% faster playback
            
            # Load and configure audio
            sound = pygame.mixer.Sound(filename)
            channel = sound.play()
            
            if channel:
                # Set additional playback properties for speed
                channel.set_volume(1.0)  # Maintain clear volume
                
                # More efficient playback loop
                clock = pygame.time.Clock()
                while channel.get_busy():
                    clock.tick(60)  # Higher tick rate for smoother playback
                    pygame.time.wait(1)  # Small wait to reduce CPU usage
            
            # Cleanup
            pygame.mixer.quit()
            pygame.mixer.init()  # Reset to default settings
            
            # Only delete the file if it was a temporary file we created
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            
        except Exception as e:
            logging.error(f"Error in text to speech: {str(e)}")
            # Cleanup in case of error
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            raise  # Re-raise exception for better error handling

    def play_acknowledgment(self):
        """Play a short acknowledgment sound"""
        self.text_to_speech("Hi! How can I help you today?", os.path.join(self.temp_dir, 'ack.mp3'))

    def speech_to_text(self, timeout=None, phrase_time_limit=None):
        """Listen for speech and convert to text"""
        try:
            with sr.Microphone() as source:
                logging.info("Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
                try:
                    text = self.recognizer.recognize_google(
                        audio,
                        language="en-US",
                        show_all=False
                    ).lower()
                    logging.info(f"Recognized: {text}")
                    return text
                except sr.UnknownValueError:
                    logging.info("Could not understand audio")
                except sr.RequestError:
                    logging.error("Could not request results from speech recognition service")
        except sr.WaitTimeoutError:
            logging.info("No speech detected within timeout period")
        except Exception as e:
            logging.error(f"Error in speech recognition: {str(e)}")
        
        return None

    def is_wake_word(self, text):
        """Check if the spoken text contains any wake words"""
        if text:
            return any(wake_word in text.lower() for wake_word in self.wake_words)
        return False

def send_command_to_backend(command, voice_assistant=None):
    """
    Send command to backend and wait for response
    
    Args:
        command (str): Command to send to backend
        voice_assistant: Voice assistant instance for audio feedback
        
    Returns:
        str: Response from backend or error message
    """
    try:
        import random
        
        # List of varied waiting messages
        waiting_messages = [
            "almost there",
            "still processing",
            "gathering information",
            "analyzing the data",
            "just a moment longer",
            "retrieving your results",
            "working on it",
            "processing your request",
            "nearly done",
            "getting there",
            "hold on a moment",
            "collecting the information",
            "compiling the results",
            "please wait a bit longer"
        ]
        
        payload = {
            'token': browser_data['token'],
            'command': command,
            'urls': browser_data['urls']
        }
        
        logging.info("\n" + "="*50)
        logging.info("DATA SENT TO BACKEND:")
        logging.info("="*50)
        logging.info(f"COMMAND: {command}")
        logging.info(f"TOKEN: '{browser_data['token']}'")
        logging.info(f"CURRENT URL: {browser_data['current_url']}")
        logging.info("\nALL URLS:")
        for idx, url in enumerate(browser_data['urls'], 1):
            logging.info(f"{idx}. {url}")
        logging.info("="*50)
        
        # Create a daemon thread for the randomized waiting messages
        waiting_event = threading.Event()
        
        def say_waiting_message():
            used_messages = set()  # Track used messages to avoid immediate repetition
            while not waiting_event.is_set():
                # If we've used all messages, reset the used messages set
                if len(used_messages) == len(waiting_messages):
                    used_messages.clear()
                
                # Get available messages (ones we haven't used recently)
                available_messages = [msg for msg in waiting_messages if msg not in used_messages]
                
                # Select and speak a random message
                message = random.choice(available_messages)
                used_messages.add(message)
                voice_assistant.text_to_speech(message)
                time.sleep(8)
        
        if voice_assistant:
            waiting_thread = threading.Thread(target=say_waiting_message, daemon=True)
            waiting_thread.start()
        
        # Send request to backend
        response = requests.post(
            'http://195.242.13.147:50001/generate',
            json=payload
        )
        
        # Stop the waiting messages
        if voice_assistant:
            waiting_event.set()
        
        if response.ok:
            response_data = response.json()
            logging.info("\n" + "="*50)
            logging.info("BACKEND RESPONSE:")
            logging.info("="*50)
            logging.info(response_data.get('response', 'Response not received'))
            logging.info("="*50 + "\n")
            print(response_data)
            
            # Set token to '1' after successful request
            browser_data['token'] = '1'
            
            return response_data.get('response', 'Response not received')
        return "Response not received"
            
    except Exception as e:
        if voice_assistant:
            waiting_event.set()  # Make sure to stop the waiting messages on error
        logging.error(f"Error sending command to backend: {str(e)}")
        return "Response not received"

def run_voice_assistant():
    """Main function to run the voice assistant"""
    assistant = VoiceAssistant()
    
    while True:
        try:
            logging.info(f"Listening for wake words: {', '.join(assistant.wake_words)}")
            wake_word = assistant.speech_to_text(timeout=None, phrase_time_limit=2.0)
            
            if wake_word and assistant.is_wake_word(wake_word):
                logging.info("Wake word detected!")
                assistant.play_acknowledgment()
                
                logging.info("Listening for command...")
                command = assistant.speech_to_text(timeout=None, phrase_time_limit=10.0)

                if browser_data['token'] == '0':
                    logging.info("Retrieving Data. Please be patient")
                    assistant.text_to_speech("Retrieving Data. Please be patient")
                
                if command:
                    logging.info(f"Command received: {command}")
                    
                    if browser_data['urls']:
                        backend_response = send_command_to_backend(command, voice_assistant=assistant)
                        assistant.text_to_speech(backend_response)
                        assistant.text_to_speech("Done. Please let me know if you have more questions.")
                    else:
                        assistant.text_to_speech("No page data available. Please wait for a page to load.")
            
            time.sleep(0.1)
                
        except Exception as e:
            logging.error(f"Error in voice assistant loop: {str(e)}")
            continue

@app.route('/process-links', methods=['POST'])
def process_links():
    """Handle incoming links from the Chrome extension"""
    logging.info("Received request to process links")
    try:
        global browser_data
        
        browser_update = request.get_json()
        # print(browser_data)
        
        if not browser_update:
            raise ValueError("No JSON data received")
        
        buffer = browser_update.get('token', '0')
        browser_data = {
            'current_url': browser_update.get('currentUrl', ''),
            'urls': browser_update.get('allUrls',  []),
            'token': str(buffer)
        }
        
        logging.info("\n" + "="*50)
        logging.info("Updated Browser Data:")
        logging.info("="*50)
        logging.info(f"Current URL: {browser_data['current_url']}")
        logging.info(f"Token: '{browser_data['token']}'")
        logging.info(f"URLs found: {len(browser_data['urls'])}")
        logging.info("="*50 + "\n")
        
        return jsonify({'status': 'success', 'message': 'Links processed successfully'})
        
    except Exception as e:
        error_msg = f"Error processing links: {str(e)}"
        logging.error(error_msg)
        return jsonify({'status': 'error', 'message': error_msg}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'current_page': browser_data['current_url'],
        'urls_collected': len(browser_data['urls'])
    })

def start_server():
    """Function to start the Flask server"""
    logging.info("\n" + "="*50)
    logging.info("Server starting on http://localhost:50001")
    logging.info("="*50 + "\n")
    app.run(host='0.0.0.0', port=50001, debug=False)

if __name__ == '__main__':
    try:
        # Start voice assistant in a separate thread
        voice_thread = threading.Thread(target=run_voice_assistant, daemon=True)
        voice_thread.start()
        logging.info("Voice assistant thread started")
        
        # Start the Flask server
        start_server()
        
    except KeyboardInterrupt:
        logging.info("\nShutting down server...")
    except Exception as e:
        logging.error(f"Error starting server: {str(e)}")