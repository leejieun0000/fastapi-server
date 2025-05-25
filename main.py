from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import UploadFile, File
from typing import List
import requests
import json
import os



app = FastAPI()

# ✅ CORS 설정: 모든 출처 허용 (Android 앱 접근 가능)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 시에는 특정 도메인만 허용하는 것이 안전
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase 설정
SUPABASE_URL = "https://itadfihnzqpzndktlggf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0YWRmaWhuenFwem5ka3RsZ2dmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwNzgyMjMsImV4cCI6MjA2MzY1NDIyM30.4uMjgEdIdggzSyfZGCc0m3mRYImZsuVnupsn0LdRI50"
BUCKET_NAME = "predictions"

@app.get("/debug-env")
def debug_env():
    return {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY")[:10] if os.getenv("SUPABASE_KEY") else None,
        "BUCKET_NAME": os.getenv("BUCKET_NAME")
    }

@app.get("/")
def root():
    return {"message": "FastAPI 서버 작동 중"}

@app.get("/heatmap")
def get_latest_prediction():
    try:
        list_url = f"{SUPABASE_URL}/storage/v1/bucket/{BUCKET_NAME}/o"
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "apikey": SUPABASE_KEY
        }
        params = {
            "limit": 100,
            "offset": 0,
            "sortBy": "name",
            "order": "desc"
        }

        res = requests.get(list_url, headers=headers, params=params)
        print("📥 status:", res.status_code)
        print("📥 response:", res.text)

        if res.status_code != 200:
            return {"status": "error", "message": "Supabase 파일 목록을 불러올 수 없습니다."}

        files = res.json()
        if not isinstance(files, list):
            return {"status": "error", "message": f"예상과 다른 응답 형식: {files}"}
        if not files:
            return {"status": "error", "message": "예측 파일이 없습니다."}

        files.sort(key=lambda f: int(f["name"].split("_")[1].split(".")[0]), reverse=True)
        latest_file = files[0]["name"]

        file_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{latest_file}"
        file_res = requests.get(file_url)
        if file_res.status_code != 200:
            return {"status": "error", "message": "예측 파일을 불러오지 못했습니다."}

        predictions = file_res.json()
        return {
            "status": "ok",
            "file": latest_file,
            "predictions": predictions
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/upload-to-supabase/")
async def upload_json_to_supabase(file: UploadFile = File(...)):
    try:
        # 업로드할 경로 및 헤더 구성
        now = datetime.utcnow().strftime("%Y%m%d_%H%M")
        filename = f"predictions_{now}.json"
        url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{filename}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }

        # 파일 읽어서 업로드
        contents = await file.read()
        res = requests.post(url, headers=headers, data=contents)

        if res.status_code in (200, 201):
            return {"status": "ok", "file": filename, "message": "Supabase 업로드 성공!"}
        else:
            return {"status": "error", "code": res.status_code, "detail": res.text}

    except Exception as e:
        return {"status": "error", "message": str(e)}