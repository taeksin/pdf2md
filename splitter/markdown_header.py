# splitter/markdown_header.py

import re
import sys
sys.dont_write_bytecode = True

class MarkdownHeaderTextSplitter:
    """
    Markdown 문서에서 #으로 시작하는 헤더를 기준으로 텍스트를 분할하는 예시 클래스.
    """

    def __init__(self):
        pass

    def split_text(self, text):
        """
        #으로 시작하는 헤더 줄을 기준으로 섹션을 분리하여 리스트로 반환합니다.
        """
        # 헤더(#)가 시작하는 줄 앞에서 분할
        sections = re.split(r'\n(?=#)', text)
        # 빈 문자열 제거
        return [section.strip() for section in sections if section.strip()]
