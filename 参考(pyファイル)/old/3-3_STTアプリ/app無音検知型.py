import numpy as np
import streamlit as st
from streamlit_webrtc import webrtc_streamer
import speech_recognition as sr
import wave
import io
import time

### ここから設定項目 ###

# 内部で扱う音声設定
sample_rate = 48000

# 音声認識の無音検知設定
search_time = 2 # 無音検索範囲秒数
pcm_volume_int = 300 # 無音閾値　0-32768の間で設定（16bitなので、-32768から32768）


### ここから機能のための変数群 ###

# メモリ上にwavファイルを保持するための変数群
temp_file_object = io.BytesIO()

# 文字起こしの出力文字
output_text_content = ""

# ブラウザから送信された音声データの断片を蓄積する変数
audio_frame_array = []

# PCM音源としての設定
frame_count = sample_rate * search_time
frame_array_point = frame_count * (-1)

# ホワイトノイズのための参考値（波の最大値ではなくだいたいの平均）
pcm_effective_volume = pcm_volume_int / 3.5

# PCMの総量の値
white_noise_sum = pcm_effective_volume * frame_count

# 音声認識の機能インスタンス化
r = sr.Recognizer()


### ここからコンポーネント配置 ###

## 音声入力部分

# 見た目出力
st.title("リアルタイム通信型音声認識")
st.write("スタートボタンを押して、オーディオコンポーネントが表示されてからしゃべり始めてください。")

# webRTCの機能、フロントからバックへ音声を送る根幹
# 音声加工のためのコールバック関数を活用して、audio_frame_arrayに音声データ蓄積
def audioCallBack(frame):
    audio_frame_array.append(frame)
webrtc_ctx = webrtc_streamer(key="example",                        
    audio_frame_callback=audioCallBack,
    media_stream_constraints={"video": False, "audio": { "enabled": True,"echoCancellation": False }},
    audio_html_attrs={"muted": True, "controls": True},
    )


## 音声認識部分と出力部分

# 見た目出力
st.write("音声認識結果")
output_text = st.empty()
output_text.write("ここに音声認識された結果が出力されます。")
# セッションから文字を取得、初期実行ならセッションないので作成
try:
    if (str(st.session_state["output_text_content"]) != ""):
        output_text.write(str(st.session_state["output_text_content"]))
except:
    st.session_state["output_text_content"] = ""

# ここ音声認識の関数
def recognize_stt():
    audio_file = temp_file_object 
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio, language="ja-JP")
        print(text)
    except:
        text = ""
    return text + " "

# メインルーチン

# 定期的に無音かどうかチェックする。
# 音声認識のために蓄積した音声データをwavファイルに変換して、音声認識のrecognize_stt()関数にwavデータ渡す。
while(True):
    # 待機時間 ※音声認識にかかる時間よりも長くとる
    time.sleep(10)

    if (audio_frame_array != []):

        # 無音検知
        temp_audio_frame_array = audio_frame_array.copy() # 蓄積の邪魔にならないように配列をコピー
        temp_audio_np_array = []
        for audio_frame in temp_audio_frame_array:
            temp_audio_np_array.append(audio_frame.to_ndarray())
        input_sound_sum = np.absolute(temp_audio_np_array[frame_array_point:-1]).sum()

        # 入力された音声データとpcm_volume_intで決めたホワイトノイズ（無音）どっちが大きいかで、wavファイル化を実行するか決める
        if (input_sound_sum > white_noise_sum):
            # 最新蓄積音声データコピー
            temp_audio_frame_array = audio_frame_array.copy()
            audio_frame_array.clear() #蓄積初期化

            temp_file_object.seek(0) # メモリ上のファイルポインタを先頭に戻す
            with wave.open(temp_file_object, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                for audio_frame in temp_audio_frame_array:
                    data = audio_frame.to_ndarray()
                    wf.writeframesraw(data.tobytes())
            temp_audio_frame_array.clear() #初期化
            temp_file_object.seek(0) # ファイルポインタを先頭に戻す
            output_text_content += recognize_stt() # 音声認識
            st.session_state["output_text_content"] = output_text_content # セッションに一時保存
            output_text.write(output_text_content) # 音声認識結果を出力