import re

class CustomSplitter:
    def __init__(self, keyword):
        """
        사용자가 지정한 키워드를 기준으로 분할합니다.
        keyword: 사용자가 입력한 분할 기준 문자열 (예: "Chapter")
        """
        # 정규표현식에서 특수문자 처리를 위해 keyword를 escape 처리
        self.keyword = re.escape(keyword)
        # lookahead 패턴으로 해당 키워드가 등장하기 전에서 분할하도록 설정 (대소문자 무시)
        self.pattern = re.compile(rf'(?i)(?={self.keyword})')

    def split_text(self, text):
        """
        주어진 텍스트를 사용자가 지정한 키워드 앞에서 분할합니다.
        텍스트가 없거나 키워드가 비어있으면 원본 텍스트를 그대로 반환합니다.
        """
        if not text:
            return []
        if not self.keyword:
            return [text]
        chunks = self.pattern.split(text)
        # 빈 문자열 및 공백만 있는 항목 제거
        return [chunk.strip() for chunk in chunks if chunk.strip()]
