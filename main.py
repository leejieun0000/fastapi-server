from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import json

app = FastAPI()

# ✅ CORS 설정: 모든 출처 허용 (Android 앱 접근 가능)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 운영 환경에서는 도메인 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Supabase 직접 설정
SUPABASE_URL = "https://itadfihnzqpzndktlggf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0YWRmaWhuenFwem5ka3RsZ2dmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwNzgyMjMsImV4cCI6MjA2MzY1NDIyM30.4uMjgEdIdggzSyfZGCc0m3mRYImZsuVnupsn0LdRI50"
BUCKET_NAME = "predictions"

@app.get("/")
def root():
    return {"message": "FastAPI 서버 작동 중"}

# ✅ 최신 파일명 가져오기
def get_latest_prediction_filename():
    url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        raise HTTPException(status_code=500, detail="Supabase 파일 목록 요청 실패")

    files = res.json()

    max_num = -1
    latest_file = None
    for file in files:
        name = file.get("name", "")
        if name.startswith("predictions_") and name.endswith(".json"):
            try:
                num = int(name.split("_")[1].split(".")[0])
                if num > max_num:
                    max_num = num
                    latest_file = name
            except ValueError:
                continue

    if not latest_file:
        raise HTTPException(status_code=404, detail="적절한 predictions 파일이 없습니다.")

    return latest_file

# ✅ 최신 파일 다운로드
def download_prediction_file(filename: str):
    file_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{filename}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    res = requests.get(file_url, headers=headers)
    if res.status_code != 200:
        raise HTTPException(status_code=500, detail="Supabase에서 파일 다운로드 실패")

    return res.json()

# ✅ FastAPI 엔드포인트
@app.get("/heatmap")
def get_heatmap():
    filename = get_latest_prediction_filename()
    data = download_prediction_file(filename)
    return data


