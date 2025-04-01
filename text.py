from langchain_text_splitters import RecursiveCharacterTextSplitter

# 텍스트 정의
document = """
인공지능(AI)은 현대 사회에서 매우 중요한 역할을 하고 있습니다.
다양한 산업 분야에서 자동화, 효율성 증대, 혁신적인 솔루션 제공을 가능하게 합니다.

그러나 AI가 야기하는 윤리적 문제도 간과할 수 없습니다. 편향성, 프라이버시 침해, 책임소재 등 사회적으로 중요한 논쟁을 일으킵니다책임소재 등 사회적으로 중요한 논쟁을 일으킵니다책임소재 등 사회적으로 중요한 논쟁을 일으킵니다책임소재 등 사회적으로 중요한 논쟁을 일으킵니다책임소재 등 사회적으로 중요한 논쟁을 일으킵니다책임소재 등 사회적으로 중요한 논쟁을 일으킵니다사회적으로 중요한 논쟁을 일으킵니다책임소재 등 사회적으로 중요한 논쟁을 일으킵니다책임소재 등 사회적으로 중요한 논쟁을 일으킵니다사회적으로 중요한 논쟁을 일으킵니다책임소재 등 사회적으로 중요한 논쟁을 일으킵니다책임소재 등 사회적으로 중요한 논쟁을 일으킵니다. 
이에 따라 AI 기술의 책임 있는 사용에 대한 요구가 점점 높아지고 있습니다.

결국, 기술 발전과 윤리적 기준 사이에서 적절한 균형을 찾는 것이 중요합니다. 이를 통해 AI 기술이 더 많은 사람에게 혜택을 제공할 수 있도록 해야 합니다이를 통해 AI 기술이 더 많은 사람에게 혜택을 제공할 수 있도록 해야 합니다이를 통해 AI 기술이 더 많은 사람에게 혜택을 제공할 수 있도록 해야 합니다.
"""

# 텍스트 스플리터 설정
text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", " ", ""],
    chunk_size=250,
    chunk_overlap=50,
    length_function=len,
    is_separator_regex=False
)

# 분할 실행
chunks = text_splitter.split_text(document)

# 결과 출력
for i, chunk in enumerate(chunks):
    print(f"\n--- Chunk {i+1} (Length: {len(chunk)}) ---")
    print(chunk)
