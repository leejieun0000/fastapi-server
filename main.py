# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from pathlib import Path

app = FastAPI()

# ✅ CORS 설정: 모든 출처 허용 (Android 앱 접근 가능)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 시에는 특정 도메인만 허용하는 것이 안전
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "FastAPI 서버 작동 중"}

@app.get("/heatmap")
def get_heatmap():
    file_path = Path("predictions_test.json")

    if not file_path.exists():
        return {"status": "error", "message": f"{file_path} 파일이 존재하지 않습니다."}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            predictions = json.load(f)
        return {
            "status": "ok",
            "predictions": predictions
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
