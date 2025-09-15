import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

# OpenAI APIキーを環境変数に設定
os.environ["OPENAI_API_KEY"] = 'ご自身のOPENAI_API_KEYを入力'
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # OpenAIクライアントを初期化

# 指定されたURLから記事をスクレイピングし、テキストを返す関数
def scrape_article(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    text_nodes = soup.find_all("div")
    joined_text = "".join(t.text.replace("\t", "").replace("\n", "") for t in text_nodes)
    return joined_text

# テキストをチャンクに分割する関数
def chunk_text(text, chunk_size, overlap):
    chunks = []
    start = 0
    while start + chunk_size <= len(text):
        chunks.append(text[start:start + chunk_size])
        start += (chunk_size - overlap)
    if start < len(text):
        chunks.append(text[-chunk_size:])
    return chunks

# テキストをベクトル化する関数
def vectorize_text(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

# 質問ベクトルと文書ベクトルを比較して最も類似した文書を見つける関数
def find_most_similar(question_vector, vectors, documents):
    similarities = []
    for index, vector in enumerate(vectors):
        similarity = cosine_similarity([question_vector], [vector])[0][0]
        similarities.append([similarity, index])
    similarities.sort(reverse=True, key=lambda x: x[0])
    top_documents = [documents[index] for similarity, index in similarities[:2]]
    return top_documents

# 質問を基にGPT-4モデルで回答を生成する関数
def ask_question(question, context):
    prompt = f'''以下の質問に以下の情報をベースにして答えて下さい。
    [ユーザーの質問]
    {question}

    [情報]
    {context}
    '''

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=400
    )
    return response.choices[0].message.content

# StreamlitのWebインターフェース
st.title("Webページの内容に答えるRAGアプリ")

url = st.text_input("WebページのURLを入力してください", "https://tech0-jp.com/#program")
question = st.text_input("質問を入力してください", "Step2ではどのようなことが身につけられますか？")

if st.button("質問を送信"):
    with st.spinner("処理中..."):
        # 記事をスクレイピングしてチャンクに分割
        article_text = scrape_article(url)
        text_chunks = chunk_text(article_text, 400, 50)

        # 各チャンクをベクトル化
        vectors = [vectorize_text(doc) for doc in text_chunks]

        # 質問をベクトル化し、最も類似した文書を検索
        question_vector = vectorize_text(question)
        similar_document = find_most_similar(question_vector, vectors, text_chunks)

        # 質問を基に回答を生成
        answer = ask_question(question, similar_document)
        st.write("生成された回答:")
        st.write(answer)
