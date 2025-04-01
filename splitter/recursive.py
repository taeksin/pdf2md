# splitter/recursive.py
import sys
sys.dont_write_bytecode = True

class RecursiveCharacterTextSplitter:
    """
    재귀적 텍스트 분할 (문자 단위 기준) 예시 클래스.
    separators, chunk_size 등을 사용하여 텍스트를 나누는 방식을 구현합니다.
    """

    def __init__(self, separators=None, chunk_size=250, chunk_overlap=50, length_function=len, is_separator_regex=False):
        """
        Parameters:
            separators (list): 우선순위대로 시도할 구분자 목록 (예: ["\n\n", "\n", " ", ""])
            chunk_size (int): 각 청크의 최대 길이
            chunk_overlap (int): 청크 간 겹칠 문자 수
            length_function (callable): 문자열 길이를 계산하는 함수
            is_separator_regex (bool): separators를 정규식으로 해석할지 여부
        """
        if separators is None:
            separators = ["\n\n", "\n", " ", ""]
        self.separators = separators
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function
        self.is_separator_regex = is_separator_regex

    def split_text(self, text):
        """
        입력 텍스트를 재귀적으로 분할한 뒤, 리스트 형태로 반환합니다.
        """
        if self.length_function(text) <= self.chunk_size:
            return [text]

        # separators를 순회하며 분할 시도
        for sep in self.separators:
            if sep and sep in text:
                parts = text.split(sep)
                chunks = []
                current_chunk = ""
                for part in parts:
                    candidate = current_chunk + sep + part if current_chunk else part
                    if self.length_function(candidate) > self.chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = part
                    else:
                        current_chunk = candidate
                if current_chunk:
                    chunks.append(current_chunk)

                # 만들어진 chunks 중 여전히 chunk_size를 넘는 것이 있으면 재귀적으로 처리
                final_chunks = []
                for c in chunks:
                    if self.length_function(c) > self.chunk_size:
                        final_chunks.extend(self.split_text(c))
                    else:
                        final_chunks.append(c)
                return final_chunks

        # 어떤 구분자도 통하지 않을 경우, chunk_size 간격으로 잘라 반환
        return [text[i:i+self.chunk_size] for i in range(0, self.length_function(text), self.chunk_size)]
