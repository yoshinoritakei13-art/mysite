import streamlit as st
from supabase import create_client, Client
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("画像投稿アプリ")

# --- 画像＆コメント投稿 ---
st.subheader("画像をアップロード")

uploaded_file = st.file_uploader("画像を選択", type=["png", "jpg", "jpeg"])
comment = st.text_area("コメントを入力")

if st.button("アップロード"):
    if uploaded_file and comment:
        image_id = str(uuid.uuid4())
        file_path = f"{image_id}.png"

        image_data = uploaded_file.read()
        # 画像を Supabase Storage にアップロード
        res = supabase.storage.from_("image-storage").upload(file_path, image_data)
        if isinstance(res, dict) and "error" in res:
            st.error("画像のアップロードに失敗しました: " + str(res["error"]))
        else:
            image_url = f"{SUPABASE_URL}/storage/v1/object/public/image-storage/{file_path}"

            # DBにデータを保存（ユーザーIDなし）
            supabase.table("image_posts").insert({
                "id": str(uuid.uuid4()),
                "image_url": image_url,
                "comment": comment,
                "created_at": datetime.utcnow().isoformat()
            }).execute()

            st.success("画像をアップロードしました！")

# --- 投稿一覧の表示 ---
st.subheader("投稿一覧")
posts = supabase.table("image_posts").select("*").execute()

if posts.data:
    for post in posts.data:
        st.image(post["image_url"], caption=post["comment"], width=300)
        st.write("---")
else:
    st.write("まだ投稿がありません。")
