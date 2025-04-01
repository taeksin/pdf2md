# splitter/semantic.py

import re
import sys
sys.dont_write_bytecode = True

class SemanticChunker:
    """
    의미 기반 스플리터 예시 클래스.
    실제 구현에서는 ML 모델 등을 활용해 의미 단위로 분할할 수 있습니다.
    여기서는 단순히 250자 내외로 문장들을 모아주는 예시만 보여줍니다.
    """

    def __init__(self):
        pass

    def split_text(self, text):
        """
        간단히 문장 단위로 분할 후, 250자를 넘지 않도록 병합.
        """
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > 250:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        if current_chunk:
            chunks.append(current_chunk)
        return chunks
