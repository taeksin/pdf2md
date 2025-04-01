import sys
sys.dont_write_bytecode = True
# splitter/character.py

class CharacterTextSplitter:
    """
    문자 단위 스플리터.
    기본적으로 지정된 separator(기본 "\n\n")를 기준으로 텍스트를 분할합니다.
    """

    def __init__(self, separator="\n\n"):
        """
        Parameters:
            separator (str): 분할에 사용할 구분자 (기본값: 두 줄바꿈)
        """
        self.separator = separator

    def split_text(self, text):
        """
        separator를 기준으로 텍스트를 분할합니다.
        """
        return text.split(self.separator)
