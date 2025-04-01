# splitter/line.py

import re
import sys
sys.dont_write_bytecode = True

class LineTextSplitter:
    """
    줄바꿈(기본적으로 "\n")을 기준으로 텍스트를 분할하는 예시 클래스.
    """

    def __init__(self, delimiters=None):
        """
        Parameters:
            delimiters (list): 구분자 목록 (기본값: ["\n"])
        """
        if delimiters is None or not delimiters:
            delimiters = ["\n"]
        self.delimiters = delimiters

    def split_text(self, text):
        """
        delimiters에 지정된 구분자(들)을 이용해 텍스트를 분할합니다.
        """
        pattern = "|".join(map(re.escape, self.delimiters))
        return re.split(pattern, text)
