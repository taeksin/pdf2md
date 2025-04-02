import streamlit as st
import os
import re
import pandas as pd
import io
from PyPDF2 import PdfReader
from pdf2md import process_pdf_to_markdown

# ---------------------------------------------------------------------------
# splitter 폴더 내 각 스플리터 모듈 import
# ---------------------------------------------------------------------------
from splitter.recursive import RecursiveCharacterTextSplitter
from splitter.character import CharacterTextSplitter
from splitter.token import TokenTextSplitter
from splitter.line import LineTextSplitter
from splitter.sentence import SentenceTextSplitter
from splitter.paragraph import ParagraphTextSplitter
from splitter.semantic import SemanticChunker
from splitter.markdown_header import MarkdownHeaderTextSplitter
from splitter.customSplitter import CustomSplitter  # PageSplitter 대신 CustomSplitter 사용

# ---------------------------------------------------------------------------
# loader 폴더 내 각 로더 import (pdf2md는 루트에 있음)
# ---------------------------------------------------------------------------
from loader.pypdf2_loader import load_pdf as load_pdf_pypdf2
from loader.pdfplumber_loader import load_pdf as load_pdf_pdfplumber
from loader.pdfminer_loader import load_pdf as load_pdf_pdfminer

# =============================================================================
# 세션 초기화
# =============================================================================
if "splitted_list" not in st.session_state:
    st.session_state["splitted_list"] = []
if "result_md" not in st.session_state:
    st.session_state["result_md"] = ""
if "xlsx_file_name" not in st.session_state:
    st.session_state["xlsx_file_name"] = ""
if "md_file_name" not in st.session_state:
    st.session_state["md_file_name"] = ""

# =============================================================================
# Markdown 포맷팅 함수
# =============================================================================
def format_text_to_markdown(text: str) -> str:
    """
    각 줄을 검사하여,
    - 만약 줄 전체가 '---'라면 앞뒤에 개행 문자를 추가합니다.
    - 빈 줄이 아니면 줄 끝에 공백 두 칸을 추가하여 Markdown 강제 줄바꿈을 적용합니다.
    - 예) "| --- |" 등 표 구분자에는 영향을 주지 않습니다.
    """
    lines = text.splitlines()
    formatted_lines = []
    for line in lines:
        # 줄 전체가 정확히 '---'인 경우
        if line.strip() == '---':
            formatted_lines.append("\n---\n")
        else:
            # 빈 줄이 아니면 줄 끝에 공백 두 칸 추가
            if line.strip():
                formatted_lines.append(line.rstrip() + "  ")
            else:
                formatted_lines.append("")
    return "\n".join(formatted_lines)

# =============================================================================
# 메인 Streamlit UI 함수
# =============================================================================
def main():
    st.title("PDF Loader & Splitter")
    
    # PDF 파일 업로드 (직접 업로드 방식)
    pdf_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])
    
    # pdf 폴더에 있는 PDF 파일 목록 (예: 프로젝트 내 "pdf" 폴더)
    pdf_folder = "pdf"
    pdf_list = []
    if os.path.exists(pdf_folder):
        pdf_list = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
    else:
        pdf_list = []
    
    # 라디오 버튼으로 PDF 사용 여부 선택: 기본은 None, 선택 시 pdf 폴더의 파일 사용
    pdf_choice = st.radio(
        "PDF 파일 선택 (라디오 버튼 선택 시, 해당 폴더의 파일을 사용합니다)",
        options=["None"] + pdf_list,
        index=0,
        key="pdf_choice"
    )
    
    st.markdown("---")
    
    # 만약 라디오 버튼에서 "None"이 아닌 PDF가 선택되면, 해당 파일을 사용하도록 함
    if pdf_choice != "None":
        pdf_file = open(os.path.join(pdf_folder, pdf_choice), "rb")
    
    # 좌우 3열 레이아웃
    col1, col2, col3 = st.columns([3, 0.2, 3])
    
    # ------------------
    # Loader 선택 및 설명
    # ------------------
    with col1:
        st.markdown("#### Loader 선택")
        loader_option = st.radio(
            "Loader 옵션 선택",
            [
                "PDF2MD",
                "PyPDF2",
                "PDFPlumber",
                "PDFMiner"
            ],
            index=0,
            horizontal=False,
            key="loader_option"
        )
        
    # ------------------
    # 세로 구분선
    # ------------------
    with col2:
        st.markdown(
            """
            <div style="border-left: 1px solid #CCC; height: 100%; margin: 0 10px;"></div>
            """,
            unsafe_allow_html=True
        )

    # ------------------
    # Splitter 선택 및 설명
    # ------------------
    with col3:
        st.markdown("#### Splitter 선택")
        splitter_option = st.radio(
            "Splitter 옵션 선택",
            [
                "None",  # 선택 시 분할하지 않고 Loader 결과만 표시
                "Recursive Text Splitter",
                # "Token-based Splitter",
                "Line-based Splitter",
                "Sentence-based Splitter",
                "Paragraph-based Splitter",
                # "Semantic-based Splitter",
                "MarkdownHeaderTextSplitter",
                "Custom Splitter"  # 기존 Page Splitter 대신 Custom Splitter 선택
            ],
            index=0,
            horizontal=False,
            key="splitter_option"
        )
    st.markdown("---")
    
    loader_descriptions = {
        "PDF2MD": "PDF2MD: PDF 파일을 Markdown 형식으로 변환하여 텍스트를 추출합니다.",
        "PyPDF2": "PyPDF2: 기본 PDF 텍스트 추출 라이브러리입니다.",
        "PDFPlumber": "PDFPlumber: 표와 레이아웃을 보존하며 텍스트를 추출합니다.",
        "PDFMiner": "PDFMiner: 텍스트 추출 정밀도가 우수한 라이브러리입니다."
    }
    st.markdown(f"**선택된 Loader :** {loader_option} - {loader_descriptions.get(loader_option, '')}")
    
    if splitter_option != "None":
        splitter_descriptions = {
            "Recursive Text Splitter": "재귀적 분할: '\\n\\n', '\\n', ' ' 등으로 분할",
            "Token-based Splitter": "토큰 기반 분할: 기본 구분자는 공백",
            "Line-based Splitter": "줄 기반 분할: 기본 구분자는 '\\n'",
            "Sentence-based Splitter": "문장 기반 분할: 기본 구분자는 '. '",
            "Paragraph-based Splitter": "단락 기반 분할: 기본 구분자는 '\\n\\n'",
            "Semantic-based Splitter": "의미 기반 분할: 문장 단위로 의미 고려",
            "MarkdownHeaderTextSplitter": "Markdown 헤더 분할: '#'으로 시작하는 헤더 기준",
            "Custom Splitter": "사용자가 입력한 문자열 앞에서 분할"
        }
        st.markdown(f"**선택된 Splitter :** {splitter_option} - {splitter_descriptions.get(splitter_option, '')}")
    else:
        st.markdown("**선택된 Splitter :** None (분할하지 않고 Loader 결과만 표시)")
    st.markdown("---")
    
    # 만약 Custom Splitter가 선택되면, 사용자로부터 분할 기준 문자열을 입력받음
    custom_keyword = ""
    if splitter_option == "Custom Splitter":
        custom_keyword = st.text_input("분할 기준 문자열 입력 (예: Chapter, Section 등)", value="")
    
    # Start 버튼
    if st.button("Start"):
        if pdf_file is None:
            st.warning("먼저 PDF 파일을 업로드하세요.")
            return

        file_name = os.path.splitext(pdf_file.name)[0]
        st.session_state["xlsx_file_name"] = f"{file_name}_{loader_option}_{splitter_option}.xlsx"
        st.session_state["md_file_name"]   = f"{file_name}_{loader_option}_{splitter_option}.md"

        # 임시 파일로 저장
        temp_path = None
        with open("temp.pdf", "wb") as tmp:
            if hasattr(pdf_file, "getbuffer"):
                tmp.write(pdf_file.getbuffer())
            else:
                tmp.write(pdf_file.read())
            temp_path = tmp.name

        # Loader 처리
        if loader_option == "PDF2MD":
            # process_pdf_to_markdown로 PDF를 Markdown으로 변환 후, 형식 적용
            text = process_pdf_to_markdown(temp_path)
            text = format_text_to_markdown(text)
        elif loader_option == "PyPDF2":
            text = load_pdf_pypdf2(temp_path)
        elif loader_option == "PDFPlumber":
            text = load_pdf_pdfplumber(temp_path)
        elif loader_option == "PDFMiner":
            text = load_pdf_pdfminer(temp_path)
        else:
            text = ""
        
        # Splitter 처리
        if splitter_option == "None":
            splitted_list = [text]
            md_result = text
        else:
            splitted_list = []
            if splitter_option == "Recursive Text Splitter":
                text_splitter = RecursiveCharacterTextSplitter(
                    separators=["\n\n", "\n", " ", ""],
                    chunk_size=250,
                    chunk_overlap=50,
                    length_function=len,
                    is_separator_regex=False
                )
                splitted_list = text_splitter.split_text(text)
            elif splitter_option == "Character-based Splitter":
                text_splitter = CharacterTextSplitter(separator="\n\n")
                splitted_list = text_splitter.split_text(text)
            elif splitter_option == "Token-based Splitter":
                text_splitter = TokenTextSplitter()
                splitted_list = text_splitter.split_text(text)
            elif splitter_option == "Line-based Splitter":
                text_splitter = LineTextSplitter()
                splitted_list = text_splitter.split_text(text)
            elif splitter_option == "Sentence-based Splitter":
                text_splitter = SentenceTextSplitter()
                splitted_list = text_splitter.split_text(text)
            elif splitter_option == "Paragraph-based Splitter":
                text_splitter = ParagraphTextSplitter()
                splitted_list = text_splitter.split_text(text)
            elif splitter_option == "Semantic-based Splitter":
                text_splitter = SemanticChunker()
                splitted_list = text_splitter.split_text(text)
            elif splitter_option == "MarkdownHeaderTextSplitter":
                text_splitter = MarkdownHeaderTextSplitter()
                splitted_list = text_splitter.split_text(text)
            elif splitter_option == "Custom Splitter":
                if not custom_keyword:
                    st.warning("Custom Splitter를 사용하려면 분할 기준 문자열을 입력하세요.")
                    splitted_list = [text]
                else:
                    text_splitter = CustomSplitter(custom_keyword)
                    splitted_list = text_splitter.split_text(text)
            
            md_result = ""
            for chunk in splitted_list:
                md_result += chunk + "\n---\n"

        st.session_state["splitted_list"] = splitted_list
        st.session_state["result_md"] = md_result

    st.markdown("---")
    st.subheader("결과")
    if len(st.session_state["splitted_list"]) == 0 and not st.session_state["result_md"]:
        st.info("아직 결과가 없습니다. 먼저 파일을 첨부하고 'Start' 버튼을 눌러주세요.")
    else:
        tabs = st.tabs(["Markdown View", "Text View", "Table View"])
        with tabs[0]:
            st.markdown("#### Markdown View")
            st.download_button(
                label="Download Markdown",
                data=st.session_state["result_md"],
                file_name=st.session_state["md_file_name"],
                mime="text/markdown"
            )
            st.markdown(st.session_state["result_md"])
            
        with tabs[1]:
            st.markdown("#### Text View")
            text_result = "\n".join(st.session_state["splitted_list"])
            txt_file_name = st.session_state["md_file_name"].replace(".md", ".txt") if st.session_state["md_file_name"] else "result.txt"
            st.download_button(
                label="Download Text",
                data=text_result,
                file_name=txt_file_name,
                mime="text/plain"
            )
            st.text_area("Text", text_result, height=10000)
            
        with tabs[2]:
            st.markdown("#### Table View")
            df = pd.DataFrame(st.session_state["splitted_list"], columns=["Chunk"])
            if not df.empty:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="split_result")
                output.seek(0)
                st.download_button(
                    label="Download XLSX",
                    data=output,
                    file_name=st.session_state["xlsx_file_name"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            st.dataframe(df, width=10000, height=1200)

if __name__ == "__main__":
    main()
