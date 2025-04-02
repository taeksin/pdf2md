from flask import Flask, request, jsonify
import os
import tempfile
import logging
import pypandoc
from pdf2docx import Converter

app = Flask(__name__)

# 로깅 설정: INFO 레벨 이상 메시지 출력
logging.basicConfig(level=logging.INFO)

def pdf_to_docx(pdf_file: str, docx_file: str) -> None:
    """
    PDF 파일을 DOCX 파일로 변환하는 함수.
    변환 과정에서 가능한 한 원본과 유사한 레이아웃을 보존하도록 합니다.
    """
    try:
        cv = Converter(pdf_file)
        # pdf2docx의 기본 옵션을 사용하되, 필요시 옵션을 추가하여 레이아웃 보존 효과를 높일 수 있습니다.
        cv.convert(docx_file, start=0, end=None)
        cv.close()
        logging.info("PDF -> DOCX 변환 성공: %s -> %s", pdf_file, docx_file)
    except Exception as e:
        logging.error("PDF -> DOCX 변환 중 오류 발생: %s", e)
        raise e

def convert_docx_to_markdown(docx_file: str) -> str:
    """
    DOCX 파일을 Markdown 형식의 텍스트로 변환하는 함수.
    Pandoc의 옵션을 활용하여 원본 DOCX의 구조와 레이아웃을 최대한 유지합니다.
    """
    try:
        # Pandoc 옵션: 줄바꿈 보존 및 ATX 스타일 헤더 사용
        extra_args = ["--wrap=preserve", "--atx-headers"]
        markdown_text = pypandoc.convert_file(docx_file, 'md', extra_args=extra_args)
        logging.info("DOCX -> Markdown 변환 성공: %s", docx_file)
    except Exception as e:
        logging.error("DOCX -> Markdown 변환 중 오류 발생: %s", e)
        raise Exception(f"DOCX -> Markdown 변환 중 오류 발생: {e}")
    return markdown_text

def extract_combined_markdown(pdf_file: str) -> str:
    """
    PDF 파일을 DOCX로 변환한 후, 변환된 DOCX 파일을 Markdown 형식의 텍스트로 변환하는 함수.
    """
    tmp_docx_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp_docx_path = tmp.name

        # PDF -> DOCX 변환
        pdf_to_docx(pdf_file, tmp_docx_path)
        # DOCX -> Markdown 변환
        markdown_text = convert_docx_to_markdown(tmp_docx_path)
    finally:
        if tmp_docx_path and os.path.exists(tmp_docx_path):
            os.remove(tmp_docx_path)
            logging.info("임시 DOCX 파일 삭제: %s", tmp_docx_path)
    return markdown_text

###############################
# Flask API 엔드포인트
###############################

@app.route("/convert", methods=["POST"])
def convert_file_to_markdown():
    if "file" not in request.files:
        return jsonify({"error": "파일이 제공되지 않았습니다."}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "빈 파일 이름입니다."}), 400

    filename = file.filename.lower()
    ext = os.path.splitext(filename)[1]
    tmp_path = None
    try:
        # 업로드된 파일을 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        if ext in [".pdf"]:
            markdown = extract_combined_markdown(tmp_path)
        elif ext in [".doc", ".docx"]:
            markdown = convert_docx_to_markdown(tmp_path)
        else:
            return jsonify({"error": "지원되지 않는 파일 형식입니다."}), 400

        return jsonify({"markdown": markdown})
    except Exception as e:
        logging.error("파일 변환 중 오류 발생: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
            logging.info("임시 업로드 파일 삭제: %s", tmp_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8021, debug=True)
