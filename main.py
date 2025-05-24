from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import UploadFile, File
from typing import List
import requests
import json

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

@app.get("/")
def root():
    return {"message": "FastAPI 서버 작동 중"}

@app.get("/heatmap")
def get_latest_prediction():
    try:
        # Supabase에서 파일 리스트 가져오기
        list_url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }

        # 💡 디버깅 로그
        print("📡 list_url:", list_url)
        print("📡 headers:", {k: (v[:8] + "..." if k == "Authorization" else v) for k, v in headers.items()})

        res = requests.get(list_url, headers=headers)
        if res.status_code != 200:
            return {"status": "error", "message": "Supabase 파일 목록을 불러올 수 없습니다."}

        files: List[dict] = res.json()

        # 💡 응답 타입 확인
        if not isinstance(files, list):
            return {"status": "error", "message": f"예상과 다른 응답 형식: {files}"}

        if not files:
            return {"status": "error", "message": "저장된 예측 파일이 없습니다."}

        # 가장 숫자가 큰 predictions_숫자.json 파일 선택
        def extract_number(file):
            try:
                return int(file["name"].split("_")[1].split(".")[0])
            except:
                return -1

        files.sort(key=extract_number, reverse=True)
        latest_file = files[0]["name"]

        # 해당 파일의 내용 가져오기
        file_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{latest_file}"
        data_res = requests.get(file_url)
        if data_res.status_code != 200:
            return {"status": "error", "message": "예측 파일을 불러오지 못했습니다."}

        predictions = data_res.json()
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