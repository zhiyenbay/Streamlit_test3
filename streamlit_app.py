import os
import sys
import datetime
import openai
import json
import dotenv
import streamlit as st

from audio_recorder_streamlit import audio_recorder

# import API key from .env file
dotenv.load_dotenv()
# openai.api_key = os.getenv("asd")

openai_api_key = st.sidebar.text_input('OpenAI API Key')
client = openai.OpenAI(api_key = openai_api_key)




def transcribe(audio_file):
    # transcript = openai.Audio.transcribe("whisper-1", audio_file)
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcript  #.text


def save_audio_file(audio_bytes, file_extension):
    """
    Save audio bytes to a file with the specified extension.

    :param audio_bytes: Audio data in bytes
    :param file_extension: The extension of the output audio file
    :return: The name of the saved audio file
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"audio_{timestamp}.{file_extension}"

    with open(file_name, "wb") as f:
        f.write(audio_bytes)

    return file_name


def transcribe_audio(file_path):
    """
    Transcribe the audio file at the specified path.

    :param file_path: The path of the audio file to transcribe
    :return: The transcribed text
    """
    with open(file_path, "rb") as audio_file:
        transcript = transcribe(audio_file)

    return transcript.text


def main():
    """
    Main function to run the Whisper Transcription app.
    """
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Document",
        "type": "object",
        "properties": {
            "document": {
                "type": "object",
                "properties": {
                    "falling_down_in_3_month": {"type": "string", "enum": ["Да", "Нет"],"description": "This field answers to the question if the patient has fallen recently or not"},
                    "accompanying_illness":  {"type": "string", "enum": ["Да", "Нет"], "description": "are there any signs of concomitant diseasess"},
                    "walking_difficulties": {"type": "string", "enum": ["ходит сам (даже если при помощи кого-то) или строгий постельный режим (неподвжино)", "Костыли/ходунки/трость", "Опирается о мебель или стены для поддержания"], "description":"This field answers to the question: does patient walk independently?"},
                    "intravenous_drip": {"type": "string", "enum": ["Да", "Нет"], "description":"This field answers to the question: if the patient is taking intravenous infusion?" },
                    "mobility":  {"type": "string", "enum": ["Нормально (ходи свободно)", "Слегка несвободная (ходит с остановками, шаги короткие, иногда с зарежкой)", "Нарушения (не может встать, ходит опираясь, смотрит вниз)"], "description": "Does the patient have walking problems?"},
                    "psychology": {"type": "string", "enum": ["Осознает свою способность двигаться", "Не знает или забывает, что нужна помощь при движении"], "description" : "what is the patient's mental state?"},
                  }
              },
        "required": ["document"]
        }
    }
    
    st.title(" AI Medical Assistant ")
    st.text(' Powered by 3MIS ')
    tab1, tab2 = st.tabs(["Record Audio", "Upload Audio"])

    # Record Audio tab
    with tab1:
        audio_bytes = audio_recorder()
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            save_audio_file(audio_bytes, "mp3")

    # Upload Audio tab
    with tab2:
        audio_file = st.file_uploader("Upload Audio", type=["mp3", "mp4", "wav", "m4a"])
        if audio_file:
            file_extension = audio_file.type.split('/')[1]
            save_audio_file(audio_file.read(), file_extension)

    # Transcribe button action
    if st.button("Transcribe"):
        # Find the newest audio file
        audio_file_path = max(
            [f for f in os.listdir(".") if f.startswith("audio")],
            key=os.path.getctime,
        )

        # Transcribe the audio file
        transcript_text = transcribe_audio(audio_file_path)

        # Display the transcript
        st.header("Transcript")
        st.write(transcript_text)

        # Save the transcript to a text file
        with open("transcript.txt", "w") as f:
            f.write(transcript_text)

        # Provide a download button for the transcript
        st.download_button("Download Transcript", transcript_text)

        # Display the Json
        st.header("JSON")
        # st.write(transcript_text)

        # text = st.text_area('Enter text:', 'What are the three key pieces of advice for learning how to code?')
        prompt = "Map information to a valid  JSON output according to the provided JSON Schema. Information: " + transcript_text
  

        if openai_api_key.startswith('sk-'):
            chat_completion = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                response_format={"type":"json_object"},
                messages=[
                    {"role":"system","content":"Answer according to following Json Schema: "+ json.dumps(schema)},
                    {"role":"user","content":prompt}
                ],
                temperature = 0
            )
        
            finish_reason = chat_completion.choices[0].finish_reason
        
            if(finish_reason == "stop"):
                data = chat_completion.choices[0].message.content
                st.info(data)
        
            else :
                st.info("Error! provide more tokens please")
            
            with open("sample.json", "w") as f:
                f.write(data)
            # with open("sample.json", "w") as outfile:
            #     json.dump(dictionary, outfile)
            
            # Provide a download button for the JSON file
            st.download_button("Download JSON file", {data})

if __name__ == "__main__":
    # Set up the working directory
    working_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(working_dir)

    # Run the main function
    main()
