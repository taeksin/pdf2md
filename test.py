def format_text_to_markdown(text: str) -> str:
    """
    각 줄을 검사하여, 만약 줄 전체가 '---'라면 앞뒤에 개행 문자를 추가합니다.
    일반 텍스트 줄의 경우, 줄 끝에 공백 두 칸을 붙여 Markdown에서 강제 줄바꿈을 적용합니다.
    """
    lines = text.splitlines()
    formatted_lines = []
    for line in lines:
        # 만약 줄 전체가 정확히 '---'라면 앞뒤에 개행 문자를 추가
        if line.strip() == '---':
            formatted_lines.append("\n---\n")
        else:
            # 빈 줄이 아니면 줄 끝에 공백 두 칸 추가
            if line.strip():
                formatted_lines.append(line.rstrip() + "  ")
            else:
                formatted_lines.append("")
    return "\n".join(formatted_lines)

# 사용 예시: process_pdf_to_markdown() 함수로 변환된 텍스트를
# format_text_to_markdown()을 통해 후처리한 후 파일에 저장

import os
from pdf2md import process_pdf_to_markdown

def convert_pdf_and_save_markdown():
    pdf_path = "pdf/hanhwa 오시리아테마파크.pdf"

    if not os.path.exists(pdf_path):
        print(f"파일이 존재하지 않습니다: {pdf_path}")
        return

    with open(pdf_path, 'rb') as f:
        markdown_raw = process_pdf_to_markdown(f)

    # 후처리: 한 줄이 '---'인 경우에만 앞뒤에 줄바꿈 추가
    markdown_formatted = format_text_to_markdown(markdown_raw)

    with open("test.md", "w", encoding="utf-8") as out:
        out.write(markdown_formatted)

    print("✅ test.md 파일로 저장 완료!")

if __name__ == "__main__":
    convert_pdf_and_save_markdown()
