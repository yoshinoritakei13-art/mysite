from audio_recorder_streamlit import audio_recorder
# import speech_recognition as sr
import wave
import streamlit as st


from openai import OpenAI
import os

# ローカルの場合
os.environ["OPENAI_API_KEY"] = "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"

# streamlit cloudに登録する用
#os.environ["OPENAI_API_KEY"] = st.secrets.api.key

client = OpenAI()


def recorder():
    contents = audio_recorder(
        energy_threshold = (1000000000,0.0000000002), 
        pause_threshold=0.1, 
        sample_rate = 48_000,
        text="Clickして録音開始　→　"
    )
    return contents

contents = recorder()
if contents == None:
    st.info('①　アイコンボタンを押して回答録音　(アイコンが赤色で録音中)。  \n②　もう一度押して回答終了　(再度アイコンが黒色になれば完了)')
    st.error('録音完了後は10秒程度お待ちください。')
    st.stop()
else:


    wave_data = st.audio(contents)
    print(type(contents)) #　bytesデータ

    with wave.open("audio.wav", "wb") as audio_file:
        audio_file.setnchannels(2)
        audio_file.setsampwidth(2)
        audio_file.setframerate(48000)
        audio_file.writeframes(contents)

    # r = sr.Recognizer()
    # with sr.AudioFile("audio.wav") as source:
    #     audio_data = r.record(source)
    #     recognized_text = r.recognize_google(audio_data, language="ja-JP")


   

    audio_file= open("./audio.wav", "rb")
    transcription = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file,
    )
    recognized_text = transcription.text
        
    st.write(recognized_text)