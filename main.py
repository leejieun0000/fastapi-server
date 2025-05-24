from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime, timedelta
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

@app.get("/")
def root():
    return {"message": "FastAPI 서버 작동 중"}

@app.get("/heatmap")
def get_latest_prediction():
    try:
        # 현재 디렉토리에서 predictions_숫자.json 형식의 파일 찾기
        candidates = list(Path(".").glob("predictions_*.json"))

        if not candidates:
            return {"status": "error", "message": "예측 파일이 존재하지 않습니다."}

        # 숫자를 기준으로 정렬해서 가장 큰 값 찾기
        def extract_number(file):
            try:
                return int(file.stem.split("_")[1])
            except:
                return -1  # 숫자 못 뽑으면 제외

        candidates = sorted(candidates, key=extract_number, reverse=True)
        target_file = candidates[0]

        with open(target_file, "r", encoding="utf-8") as f:
            predictions = json.load(f)  # 📌 JSON으로 읽기

        return {
            "status": "ok",
            "file": target_file.name,
            "predictions": predictions
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ✅ 모델이 파일명 지정해서 업로드하는 POST API
@app.post("/heatmap")
async def upload_heatmap(request: Request):
    try:
        filename = request.headers.get("X-Filename")
        if not filename:
            return {"status": "error", "message": "X-Filename 헤더가 없습니다."}

        data = await request.json()

        file_path = Path(filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {"status": "ok", "message": f"{filename} 업로드 완료!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
