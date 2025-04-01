import re

class PageSplitter:
    def __init__(self, split_pattern=r'(?i)(?=\bpage\b)'):
        """
        초기화 함수입니다.
        기본 split_pattern은 대소문자 구분 없이 'page'라는 단어가 나오기 전 위치를 기준으로 분할합니다.
        (?i)  : 대소문자 무시, (?=\bpage\b) : 'page'라는 단어 앞에서 분할
        """
        self.split_pattern = split_pattern

    def split_text(self, text):
        """
        주어진 텍스트를 'page'라는 단어가 등장하기 전 위치에서 분할합니다.
        만약 텍스트가 없으면 빈 리스트를 반환합니다.
        """
        if not text:
            return []
        # lookahead 패턴을 사용하여 분할
        chunks = re.split(self.split_pattern, text)
        # 빈 문자열과 공백만 있는 항목 제거
        return [chunk.strip() for chunk in chunks if chunk.strip()]
