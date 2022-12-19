import sys
import os
import signal
from computer_voice import ComputerVoice
from open_ai_client import OpenAIClient
from speech_listener import SpeechListener
import logging
from exceptions.SpeechRecognitionRequestError import SpeechRecognitionRequestError
from exceptions.CouldNotUnderstandSpeechError import CouldNotUnderstandSpeechError

openai_api_key = os.getenv("OPENAI_API_KEY")
lang = os.getenv("LANGUAGE")
tld = os.getenv("TOP_LEVEL_DOMAIN")
previous_responses = []
computer_voice = ComputerVoice("temp.mp3", lang, tld)


def start_conversation():
    open_ai_client = OpenAIClient(openai_api_key)
    speech_listener = SpeechListener()
    text: str = None

    try:
        text = speech_listener.listen_for_speech()
    except CouldNotUnderstandSpeechError as e:
        logging.error(e)
    except SpeechRecognitionRequestError as e:
        logging.error(e)
        cleanup_and_exit()

    if text == "Exit" or text == "exit":
        cleanup_and_exit()

    if text is None or len(text) <= 1:
        start_conversation()

    response = open_ai_client.get_completion(
        prompt=text,
        previous_responses=previous_responses,
        model="text-davinci-003",
        max_tokens=200
    )

    previous_responses.append(response)
    response_text = response.get_computer_response()

    logging.info(f"Open AI Response: {response_text}")

    with computer_voice as cv:
        cv.speak(response_text)

    if not response.was_cut_short():
        logging.debug("Starting to listen again...")
        start_conversation()

    # If the response was cut short, let the user know they hit the max token limit
    with computer_voice as cv:
        cv.speak("I apologize, but I ran out of tokens to finish my response.")


def cleanup_and_exit():
    logging.debug("Making sure temp files are cleaned up...")
    computer_voice.cleanup_temp_files()
    logging.debug('Closing conversation...')
    sys.exit(0)


def signal_handler(sig, frame):
    cleanup_and_exit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    start_conversation()
