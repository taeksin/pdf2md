from pdf2md import reformat_markdown

def reformat_markdown_file(input_file: str, output_file: str, mode: str = "sentence"):
    # test.md 파일 읽기
    with open(input_file, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    # reformat_markdown 함수 호출 (mode: "sentence" 또는 "paragraph")
    reformatted_text = reformat_markdown(markdown_text, mode=mode)

    # 결과를 reformatted_test.md 파일로 저장
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(reformatted_text)
    
    print(f"재조정된 Markdown 파일이 저장되었습니다: {output_file}")

if __name__ == "__main__":
    reformat_markdown_file("test.md", "reformatted_test.md", mode="paragraph")
