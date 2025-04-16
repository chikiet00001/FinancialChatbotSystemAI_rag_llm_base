

# chatbot
# api/main.py
from fastapi import FastAPI, Query, BackgroundTasks
from pydantic import BaseModel
from chatbot.services.files_chat_agent import FilesChatAgent  # noqa: E402
from demo.GetDataModel import GetDataModel 
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware

import subprocess
import sys
import os

# # chuẩn bị dữ liệu
from ingestion.ingestion import Ingestion

settings.LLM_NAME = "openai"

# Đảm bảo môi trường ảo được kích hoạt đúng
venv_path = os.path.join(os.getcwd(), '.venv', 'Scripts', 'python.exe')
uvicorn_path = os.path.join(os.getcwd(), '.venv', 'Scripts', 'uvicorn.exe')

# question = "Sáng 14-11 có sự kiện gì??"
def Chat_Bot_Output(_question):
    chat = FilesChatAgent("demo\\data_vector").get_workflow().compile().invoke(
        input={
            "question": _question,
        }
    )
    return chat["generation"]

### tạo api
app = FastAPI(title="Finance Chatbot API")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các phương thức
    allow_headers=["*"],  # Cho phép tất cả các headers
)

# Dùng dictionary để theo dõi trạng thái tác vụ
class QuestionInput(BaseModel):
    question: str

@app.get("/")
def root():
    return {"message": "Finance RAG API đang hoạt động"}

@app.post("/ask")
async def ask_question(data: QuestionInput):
    answer = Chat_Bot_Output(data.question)
    return {"answer": answer}
###
task_status = {}

def update_data():
    Ingestion("openai").ingestion_folder(
        path_input_folder="demo\\data_in",
        path_vector_store="demo\\data_vector",
    )
# Hàm mô phỏng một tác vụ dài
def long_task(task_id: str):
    task_status[task_id] = True  # Đánh dấu là đang hoạt động (True)

    # Tạo một đối tượng của lớp GetDataModel
    data_model = GetDataModel()

    # Gọi phương thức run_get_data() qua đối tượng data_model
    data_model.run_get_data()  # Lưu ý là phải gọi phương thức thông qua đối tượng
    update_data()

    task_status[task_id] = False  # Đánh dấu là hoàn thành (False)

    
@app.post("/start_task/{task_id}")
async def start_task(task_id: str, background_tasks: BackgroundTasks):
    task_status[task_id] = True  # Đánh dấu là đang hoạt động (True)
    background_tasks.add_task(long_task, task_id)  # Thêm tác vụ vào nền (background)
    return {"message": "Task started", "task_id": task_id}

@app.get("/check_task/{task_id}")
async def check_task(task_id: str):
    # Lấy trạng thái của task từ task_status
    status = task_status.get(task_id, None)
    
    if status is None:
        # Trả về False nếu không tìm thấy tác vụ
        return {"result": False}  # Trả về dưới dạng JSON với trường result
    else:
        # Trả về trạng thái (True nếu đang hoạt động, False nếu hoàn thành)
        return {"result": status}  # Trả về dưới dạng JSON với trường result

if __name__ == "__main__":
    subprocess.run([venv_path, uvicorn_path, "main:app", "--host", "127.0.0.1", "--port", "8000", "--workers", "2"])