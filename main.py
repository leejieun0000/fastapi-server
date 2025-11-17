from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime, timedelta, timezone
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
SUPABASE_URL = "https://wdcifdkjxlblbxxupvjk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndkY2lmZGtqeGxibGJ4eHVwdmprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMzNTQzOTQsImV4cCI6MjA3ODkzMDM5NH0.PrDqBg35G2nsCDfPEW-1SB1lRniWfyI-mUmq2q8-hgU"
BUCKET_NAME = "predictions"

@app.get("/")
def root():
    return {"message": "FastAPI 서버 작동 중"}


@app.get("/heatmap")
def get_latest_prediction():
    try:
        print("🔍 Supabase 파일 목록 조회 중...")

        # Supabase에서 파일 목록 가져오기
        list_url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        res = requests.post(
            list_url,
            headers=headers,
            json={"prefix": ""}
        )

        if res.status_code != 200:
            return {"status": "error", "message": "Supabase 파일 목록을 불러올 수 없습니다."}

        files: List[dict] = res.json()

        # 파일이 비어있는지 확인
        if not files or files[0]['name'] == '.emptyFolderPlaceholder':
            return {"status": "error", "message": "Supabase 버킷에 예측 파일이 존재하지 않습니다."}

        # ✅ (파일이 하나만 있다는 전제 하에) 첫 번째 파일을 target_filename으로 지정합니다.
        #    파일 이름의 정렬 순서와 관계없이 존재하는 파일을 무조건 가져옵니다.
        target_filename = files[0]["name"]

        print(f"✅ Supabase에서 가져온 파일: {target_filename}")

        # 해당 파일의 내용 가져오기
        file_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{target_filename}"
        data_res = requests.get(file_url)

        if data_res.status_code != 200:
            # 파일을 찾았으나 다운로드에 실패했을 경우
            return {"status": "error", "message": f"파일({target_filename})을 불러오지 못했습니다. (HTTP {data_res.status_code})"}

        predictions = data_res.json()
        return {
            "status": "ok",
            "file": target_filename,
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