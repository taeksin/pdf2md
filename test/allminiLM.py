import tkinter as tk
from tkinter import ttk
import platform
import torch
import numpy as np
from sentence_transformers import SentenceTransformer

# 임베딩 생성 클래스
class EmbeddingGenerator:
    def __init__(self):
        print("BERT 모델 로딩 중...")
        # SentenceTransformer 모델 로딩 (모델은 로컬 캐시에 저장됨)
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='./model_cache')
        print("BERT 모델 로딩 완료")
        # 디바이스 설정 (Mac의 MPS, CUDA, 또는 CPU)
        if platform.system() == 'Darwin' and torch.backends.mps.is_available():
            self.device = torch.device("mps")
            self.model = self.model.to(self.device)
            print("M1/M2 Mac MPS 사용 중")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
            self.model = self.model.to(self.device)
            print(f"GPU 사용 중: {torch.cuda.get_device_name(0)}")
        else:
            self.device = torch.device("cpu")
            print("CPU 사용 중")
    
    def generate_embedding(self, text: str):
        # 단일 텍스트의 임베딩을 생성 (배치 크기 1)
        return self.model.encode(text, show_progress_bar=False, device=self.device, batch_size=1)

def compute_l2_distance(vec1: np.ndarray, vec2: np.ndarray):
    # 두 벡터 간의 L2(유클리드) 거리를 계산
    return np.linalg.norm(vec1 - vec2)

def compute_similarity_score(l2_distance: float):
    # L2 거리를 바탕으로 유사도 점수를 계산하는 예시
    # (점수가 높을수록 유사한 것으로 간주)
    # 예: 유사도 = 100 / (1 + L2 거리)
    score = 100 / (1 + l2_distance)
    return score

# GUI 애플리케이션 클래스 (tkinter 사용)
class EmbeddingApp(tk.Tk):
    def __init__(self, embedding_generator: EmbeddingGenerator):
        super().__init__()
        self.title("임베딩 비교")
        self.geometry("600x400")
        self.embedding_generator = embedding_generator
        self.create_widgets()
        
    def create_widgets(self):
        # A 텍스트 입력 레이블 및 텍스트 박스
        label_a = ttk.Label(self, text="A 텍스트:")
        label_a.pack(pady=(10, 0))
        self.text_a = tk.Text(self, height=5, width=70)
        self.text_a.pack(pady=(0, 10))
        
        # B 텍스트 입력 레이블 및 텍스트 박스
        label_b = ttk.Label(self, text="B 텍스트:")
        label_b.pack(pady=(10, 0))
        self.text_b = tk.Text(self, height=5, width=70)
        self.text_b.pack(pady=(0, 10))
        
        # 임베딩 비교 버튼
        compare_button = ttk.Button(self, text="임베딩 비교", command=self.compare_embeddings)
        compare_button.pack(pady=10)
        
        # 결과 출력 레이블
        self.output_label = ttk.Label(self, text="", font=("Arial", 12))
        self.output_label.pack(pady=10)
        
    def compare_embeddings(self):
        # A와 B 텍스트를 가져옴
        text_a = self.text_a.get("1.0", tk.END).strip()
        text_b = self.text_b.get("1.0", tk.END).strip()
        if not text_a or not text_b:
            self.output_label.config(text="두 텍스트 모두 입력해주세요.")
            return
        
        # 임베딩 생성
        embedding_a = self.embedding_generator.generate_embedding(text_a)
        embedding_b = self.embedding_generator.generate_embedding(text_b)
        
        # L2 거리 계산
        l2_distance = compute_l2_distance(embedding_a, embedding_b)
        # 유사도 점수 계산 (예시 방식)
        similarity = compute_similarity_score(l2_distance)
        
        output_text = f"L2 Distance: {l2_distance:.4f}\n유사도 점수: {similarity:.2f} 점"
        self.output_label.config(text=output_text)

if __name__ == "__main__":
    # EmbeddingGenerator 인스턴스 생성
    embedding_generator = EmbeddingGenerator()
    # GUI 애플리케이션 실행
    app = EmbeddingApp(embedding_generator)
    app.mainloop()
