from flask import Flask, request, jsonify
import pdfplumber
import io
import re
import logging
from collections import defaultdict, Counter
from statistics import median

app = Flask(__name__)

###############################
# 상수 및 사전 컴파일된 정규표현식
###############################

# 헤더/푸터 후보 영역 비율 (PDF 상단/하단에서 추출)
HEADER_HEIGHT_RATIO = 0.2   # 상단 10%
FOOTER_HEIGHT_RATIO = 0.1   # 하단 10%

# 텍스트 유사도 임계값 (자카드 유사도)
JACCARD_THRESHOLD = 0.5

# 빈도 임계값: 전체 페이지의 몇 % 이상에서 유사한 후보가 있어야 공통으로 간주할지
FREQUENCY_THRESHOLD = 0.7

# 기본 설정: 로그 레벨과 출력 포맷 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

###############################
# 텍스트 유사도 계산 함수 (자카드 유사도)
###############################
def jaccard_similarity(s1, s2):
    """
    두 문자열의 자카드 유사도를 계산합니다.
    단어 단위로 소문자 비교합니다.
    """
    set1 = set(s1.lower().split())
    set2 = set(s2.lower().split())
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)

###############################
# 단어들을 그룹화해서 라인 생성 (수정됨)
###############################
def group_words_to_lines(words, threshold=3):
    """
    pdfplumber의 extract_words() 결과를 이용하여
    y 좌표가 가까운 단어들을 하나의 라인으로 그룹화합니다.
    반환값은 (min_top, max_bottom, line_text) 튜플의 리스트로 생성됩니다.
    """
    if not words:
        return []
    words = sorted(words, key=lambda w: w["top"])
    lines = []
    current_line = [words[0]]
    current_top = float(words[0]["top"])
    current_bottom = float(words[0]["bottom"])
    
    for word in words[1:]:
        word_top = float(word["top"])
        word_bottom = float(word["bottom"])
        # y 좌표 차이가 threshold 이하이면 같은 라인으로 봄
        if abs(word_top - current_top) <= threshold:
            current_line.append(word)
            current_bottom = max(current_bottom, word_bottom)
        else:
            current_line = sorted(current_line, key=lambda w: float(w["x0"]))
            line_text = " ".join(w["text"] for w in current_line)
            lines.append((current_top, current_bottom, line_text))
            current_line = [word]
            current_top = word_top
            current_bottom = word_bottom
    # 마지막 라인 추가
    if current_line:
        current_line = sorted(current_line, key=lambda w: float(w["x0"]))
        line_text = " ".join(w["text"] for w in current_line)
        lines.append((current_top, current_bottom, line_text))
    return lines

###############################
# 전역 헤더/푸터 영역(비율) 산출 함수 (텍스트 유사도 기반 추가)
###############################
def compute_global_header_footer_bounds(pdf, header_candidate_ratio=HEADER_HEIGHT_RATIO, footer_candidate_ratio=FOOTER_HEIGHT_RATIO):
    """
    각 페이지의 상단/하단 후보 영역(각각 10%)에서 그룹화한 라인들을 대상으로,
    자카드 유사도를 이용하여 여러 페이지에 걸쳐 공통으로 등장하는 (즉, 헤더/푸터로 판단되는) 
    후보 라인을 찾습니다.
    - 헤더: 각 페이지에서 (y 중심이 상단 후보 영역에 해당) 라인의 max_bottom 비율을 후보로 함.
    - 푸터: 각 페이지에서 (y 중심이 하단 후보 영역에 해당) 라인의 min_top 비율을 후보로 함.
    
    각 페이지마다, 공통으로 등장하는 후보 (빈도 기준 FREQUENCY_THRESHOLD 이상) 중
    헤더는 최대 bottom 비율, 푸터는 최소 top 비율을 추출한 후, 전체 문서의 중앙값을 반환합니다.
    
    반환 값: (median_header_frac, median_footer_frac)
    """
    total_pages = len(pdf.pages)
    header_candidates_per_page = []
    footer_candidates_per_page = []
    
    # 각 페이지별 후보 라인 추출
    for idx, page in enumerate(pdf.pages):
        height = page.height
        lines = group_words_to_lines(page.extract_words(), threshold=3)
        
        header_candidates = []
        footer_candidates = []
        for (line_top, line_bottom, line_text) in lines:
            center_y = (line_top + line_bottom) / 2.0
            # 헤더 후보: 상단 10% 내의 라인
            if center_y <= header_candidate_ratio * height:
                ratio = line_bottom / height
                header_candidates.append({"text": line_text, "ratio": ratio})
            # 푸터 후보: 하단 10% 내의 라인
            if center_y >= (1 - footer_candidate_ratio) * height:
                ratio = line_top / height
                footer_candidates.append({"text": line_text, "ratio": ratio})
        header_candidates_per_page.append(header_candidates)
        footer_candidates_per_page.append(footer_candidates)
    
    # 공통으로 등장하는 헤더 후보 찾기 (텍스트 유사도로 비교)
    common_header_ratios = []
    for i, candidates in enumerate(header_candidates_per_page):
        for cand in candidates:
            count = 0
            for other in header_candidates_per_page:
                if any(jaccard_similarity(cand["text"], ocand["text"]) >= JACCARD_THRESHOLD for ocand in other):
                    count += 1
            if count / total_pages >= FREQUENCY_THRESHOLD:
                common_header_ratios.append(cand["ratio"])
    
    # 공통으로 등장하는 푸터 후보 찾기 (텍스트 유사도로 비교)
    common_footer_ratios = []
    for i, candidates in enumerate(footer_candidates_per_page):
        for cand in candidates:
            count = 0
            for other in footer_candidates_per_page:
                if any(jaccard_similarity(cand["text"], ocand["text"]) >= JACCARD_THRESHOLD for ocand in other):
                    count += 1
            if count / total_pages >= FREQUENCY_THRESHOLD:
                common_footer_ratios.append(cand["ratio"])
    
    if common_header_ratios:
        median_header_frac = median(common_header_ratios)
    else:
        median_header_frac = header_candidate_ratio  # 기본값
    
    if common_footer_ratios:
        median_footer_frac = median(common_footer_ratios)
    else:
        median_footer_frac = 1 - footer_candidate_ratio  # 기본값
    
    return median_header_frac, median_footer_frac

###############################
# PDF -> Markdown 변환 함수들 (실제 헤더/푸터 영역 제거 적용)
###############################
def convert_table_to_markdown(table_data):
    """
    추출한 표 데이터를 Markdown 형식의 테이블 문자열로 변환합니다.
    첫 행은 헤더로, 나머지 행은 데이터로 처리합니다.
    """
    if not table_data:
        return ""
    md_lines = []
    header = table_data[0]
    md_lines.append("| " + " | ".join(header) + " |")
    md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in table_data[1:]:
        md_lines.append("| " + " | ".join(row) + " |")
    return "\n".join(md_lines)

def process_pdf_to_markdown(pdf_file):
    """
    PDF 파일의 각 페이지에서 상단과 하단 10% 영역에서
    실제 헤더와 푸터 영역(픽셀 단위)을 산출한 후,
    해당 영역의 텍스트를 제거하고 나머지 텍스트와 표 객체를
    좌표 기반으로 추출하여 Markdown 형식 문자열로 변환합니다.
    각 페이지의 내용은 구분자 '---'로 연결됩니다.
    """
    page_contents = []
    with pdfplumber.open(pdf_file) as pdf:
        # 전역적으로 실제 헤더와 푸터의 비율을 산출 (텍스트 유사도 기반)
        median_header_frac, median_footer_frac = compute_global_header_footer_bounds(pdf)
        logging.info(f"산출된 실제 헤더 비율: {median_header_frac:.3f}, 푸터 비율: {median_footer_frac:.3f}")
        
        for p_idx, page in enumerate(pdf.pages):
            width, height = page.width, page.height
            # 실제 헤더와 푸터 경계 (픽셀 단위)
            actual_header_bound = median_header_frac * height
            actual_footer_bound = median_footer_frac * height
            
            # 전체 페이지에서 단어 추출 (테이블 제외용)
            cropped_page = page
            
            # 표 객체 추출 (좌표 정보 포함)
            tables = []
            for table in cropped_page.find_tables():
                try:
                    table_data = table.extract()
                    if table_data:
                        md_table = convert_table_to_markdown(table_data)
                        tables.append({
                            "type": "table",
                            "y": table.bbox[1],
                            "content": md_table,
                            "bbox": table.bbox
                        })
                except Exception:
                    continue

            # 텍스트 객체 추출: extract_words()로 단어 단위 추출 후 그룹화
            words = cropped_page.extract_words()
            filtered_words = []
            for w in words:
                cx = (float(w["x0"]) + float(w["x1"])) / 2
                cy = (float(w["top"]) + float(w["bottom"])) / 2
                # 테이블 내부 단어 제외
                inside_table = False
                for t in tables:
                    if (t["bbox"][0] <= cx <= t["bbox"][2]) and (t["bbox"][1] <= cy <= t["bbox"][3]):
                        inside_table = True
                        break
                if inside_table:
                    continue
                # 실제 헤더 영역 (0 ~ actual_header_bound)와 푸터 영역 (actual_footer_bound ~ 하단)에 해당하면 제외
                if float(w["bottom"]) <= actual_header_bound or float(w["top"]) >= actual_footer_bound:
                    continue
                filtered_words.append(w)
                
            text_lines = group_words_to_lines(filtered_words)
            text_objects = [{"type": "text", "y": t, "content": txt} for t, _, txt in text_lines]

            # 텍스트와 표를 y 좌표 기준으로 합쳐 원본 순서를 재현
            all_objects = text_objects + tables
            all_objects = sorted(all_objects, key=lambda obj: obj["y"])
            page_lines = []
            for obj in all_objects:
                if obj["type"] == "text":
                    page_lines.append(obj["content"])
                elif obj["type"] == "table":
                    page_lines.append("\n" + obj["content"] + "\n")
            page_contents.append("\n".join(page_lines))
    # \n---\n를 기준으로 조각을 나누고 각 조각의 맨 앞에 page_를 붙여 지게 함
    numbered_pages = []
    for i, content in enumerate(page_contents, start=1):
        numbered_pages.append(f"page_{i}\n\n{content}")
    return "\n---\n".join(numbered_pages)

@app.route('/convert', methods=['POST'])
def convert_pdf_endpoint():
    """
    PDF 파일을 POST로 업로드하면, PDF의 텍스트와 표를 추출하여 Markdown 형식 문자열을
    JSON으로 반환합니다. 페이지 구분자는 '---'입니다.
    """
    if 'file' not in request.files:
        return jsonify({"error": "파일이 제공되지 않았습니다."}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "선택된 파일이 없습니다."}), 400
    
    try:
        markdown_text = process_pdf_to_markdown(file)
        return jsonify({"markdown": markdown_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

###############################
# Markdown 분할(split) 함수들
###############################
def split_markdown_by_page(markdown_text):
    """
    Markdown 문서를 '---' 구분자를 기준으로 페이지별로 분할합니다.
    각 분할된 결과는 페이지 내용(문자열)을 포함하는 리스트로 반환합니다.
    """
    # 구분자가 양쪽에 여백이 있을 수 있으므로 패턴에 유의
    pages = re.split(r'\n\s*---\s*\n', markdown_text)
    # 빈 문자열은 제거한 후 반환
    return [page.strip() for page in pages if page.strip()]

def split_markdown_by_paragraph(markdown_text):
    """
    앞서 작성한 정교한 문단 분할 로직 (코드 블록 및 표 영역 고려)
    """
    lines = markdown_text.splitlines()
    paragraphs = []
    current_block = []
    current_block_type = None  # "normal", "table", "code"
    in_code_block = False
    code_block_delimiter = None

    def flush_block():
        nonlocal current_block, current_block_type
        if current_block:
            block_text = "\n".join(current_block).strip()
            if block_text:
                paragraphs.append(block_text)
            current_block = []
            current_block_type = None

    i = 0
    while i < len(lines):
        line = lines[i]
        # 코드 블록 처리 (백틱으로 시작)
        code_block_match = re.match(r'^(```+)', line)
        if code_block_match:
            delimiter = code_block_match.group(1)
            if not in_code_block:
                flush_block()
                in_code_block = True
                current_block_type = "code"
                code_block_delimiter = delimiter
            current_block.append(line)
            if in_code_block and line.strip().endswith(code_block_delimiter) and i != 0:
                flush_block()
                in_code_block = False
                code_block_delimiter = None
            i += 1
            continue

        # 테이블 라인 판단: 시작이 파이프(|)로 시작하면 테이블 라인으로 판단
        is_table_line = bool(re.match(r'^\s*\|', line))
        if is_table_line:
            if current_block_type != "table":
                flush_block()
                current_block_type = "table"
            current_block.append(line)
            i += 1
            continue

        # 일반 텍스트 줄 처리
        if line.strip() == "":
            if current_block_type == "table":
                j = i + 1
                found_table = False
                while j < len(lines):
                    if lines[j].strip():
                        if re.match(r'^\s*\|', lines[j]):
                            found_table = True
                        break
                    j += 1
                if found_table:
                    i += 1
                    continue
            flush_block()
            i += 1
            continue

        if current_block_type != "normal":
            flush_block()
            current_block_type = "normal"
        current_block.append(line)
        i += 1

    flush_block()
    return paragraphs

def split_markdown(markdown_text, split_method="page"):
    """
    split_method에 따라 Markdown 문서를 분할합니다.
    - "page": '---' 구분자 기준 분할
    - "paragraph": 코드 블록 및 표 영역을 고려한 문단 단위 분할
    """
    if split_method == "page":
        return split_markdown_by_page(markdown_text)
    elif split_method == "paragraph":
        return split_markdown_by_paragraph(markdown_text)
    else:
        raise ValueError("지원하지 않는 분할 방식입니다. 'page' 또는 'paragraph' 선택 가능.")

@app.route('/split', methods=['POST'])
def split_markdown_endpoint():
    """
    JSON 형식의 요청에서 'markdown'과 'split_method' 값을 받아서,
    지정한 기준으로 Markdown 문서를 분할한 결과를 JSON으로 반환합니다.
    예시 요청 JSON:
    {
      "markdown": "전체 Markdown 내용...",
      "split_method": "page"   // 또는 "paragraph"
    }
    """
    data = request.get_json()
    if not data or "markdown" not in data:
        return jsonify({"error": "요청 JSON에 'markdown' 필드가 필요합니다."}), 400
    
    markdown_text = data["markdown"]
    split_method = data.get("split_method", "page")
    
    try:
        split_result = split_markdown(markdown_text, split_method)
        return jsonify({"split_result": split_result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

###############################
# 문단/문장 분할 재조정
###############################

def reformat_markdown(markdown_text, mode="sentence"):
    """
    Markdown 텍스트를 단락/문장 단위로 재조정합니다.
    
    - 먼저 빈 줄(\n\n)을 기준으로 단락을 분리합니다.
    - mode가 "sentence"인 경우, 각 단락 내에서 문장 경계를 기준으로 분리한 후,
      각 문장을 새로운 줄에 배치합니다.
    - mode가 "paragraph"인 경우, 단락별로 공백을 정리하여 반환합니다.
    """
    # 단락 단위 분할: 연속된 빈 줄로 구분
    paragraphs = re.split(r'\n\s*\n', markdown_text.strip())
    
    if mode == "sentence":
        reformatted_paragraphs = []
        for para in paragraphs:
            # 코드 블록 등 특별한 영역이 포함되어 있다면 해당 부분은 건너뛰도록 할 수 있음.
            # 여기서는 단순하게 문장 분리를 진행합니다.
            # 문장 경계: 마침표, 느낌표, 물음표 뒤에 공백이 있는 경우 분할
            sentences = re.split(r'(?<=[.?!])\s+', para.strip())
            # 각 문장을 개별 줄로 배치 (문장 사이에 개행문자 삽입)
            reformatted_para = "\n".join(sentences)
            reformatted_paragraphs.append(reformatted_para)
        # 각 단락은 빈 줄로 구분
        return "\n\n".join(reformatted_paragraphs)
    
    elif mode == "paragraph":
        # 단락별로 양쪽 공백 제거 후 다시 합침
        return "\n\n".join([para.strip() for para in paragraphs])
    else:
        raise ValueError("지원하지 않는 mode입니다. 'sentence' 또는 'paragraph'를 선택하세요.")

@app.route('/reformat', methods=['POST'])
def reformat_markdown_endpoint():
    """
    JSON 형식의 요청에서 'markdown'과 선택적으로 'mode' 값을 받아,
    단락/문장 단위로 재조정한 Markdown 텍스트를 JSON으로 반환합니다.
    
    예시 요청 JSON:
    {
      "markdown": "전체 Markdown 내용...",
      "mode": "sentence"  // 또는 "paragraph"
    }
    """
    data = request.get_json()
    if not data or "markdown" not in data:
        return jsonify({"error": "요청 JSON에 'markdown' 필드가 필요합니다."}), 400
    
    markdown_text = data["markdown"]
    mode = data.get("mode", "sentence")
    
    try:
        reformatted = reformat_markdown(markdown_text, mode=mode)
        return jsonify({"reformatted_markdown": reformatted})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

###############################
# 메인 실행부
###############################
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8021, debug=True)
