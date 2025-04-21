import os
import json
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal
import pdfplumber

# 헤더/푸터 제거 비율 (현재는 사용하지 않음; 전체 페이지 내용 포함)
HEADER_HEIGHT_RATIO = 0.01  # 상단 (참고용)
FOOTER_HEIGHT_RATIO = 0.01  # 하단 (참고용)

def extract_text_layout(pdf_path):
    # 결과를 저장할 리스트들
    all_left = []
    all_right = []
    all_text = []        # 좌우 구분 없이 전체 텍스트
    all_bbox = []        # 전체 bbox 정보 (문자열 형태)
    left_bbox_all = []   # 좌측 컬럼 bbox 정보 (문자열 형태)
    right_bbox_all = []  # 우측 컬럼 bbox 정보 (문자열 형태)
    all_bbox_json_data = []  # 페이지별 bbox 정보를 구조화된 JSON 형태로 저장 (리스트의 dict 형태)

    # 페이지별 레이아웃 데이터를 저장 (하이라이팅용)
    layout_data_list = []  # 각 원소: {"left": [ (x0, y0, x1, y1, text), ... ], "right": [...] }

    # 각 페이지별로 처리 (pdfminer 이용)
    for page_num, page_layout in enumerate(extract_pages(pdf_path), start=1):
        # 페이지 전체 영역 (bbox: (x0, y0, x1, y1))
        x0_page, y0_page, x1_page, y1_page = page_layout.bbox
        page_width = x1_page - x0_page
        page_height = y1_page - y0_page
        half_width = page_width / 2

        # 전체 페이지(헤더/푸터 포함)를 대상으로 처리
        left_column = []
        right_column = []
        page_all_elements = []
        page_all_bbox = []
        left_elements_bbox = []
        right_elements_bbox = []
        # 페이지별 레이아웃 데이터 (하이라이팅용)
        page_layout_data = {"left": [], "right": []}
        # JSON용 bbox 데이터를 저장할 리스트 (각 요소를 구조화된 dict로 저장)
        page_bbox_info_json = []

        for element in page_layout:
            if isinstance(element, LTTextBoxHorizontal):
                text = element.get_text()
                # 기존 파일 출력을 위한 문자열 형태의 bbox 정보
                bbox_info = (f"pdf_width={page_width} pdf_height={page_height} | "
                             f"bbox=({element.x0}, {element.y0}, {element.x1}, {element.y1})\n{text}")
                
                # JSON 저장을 위한 구조화된 bbox 데이터 (pdf_width, pdf_height는 페이지 단위로 저장)
                bbox_data = {
                    "bbox": [element.x0, element.y0, element.x1, element.y1],
                    "text": text.strip()
                }
                page_bbox_info_json.append(bbox_data)

                # 전체 요소 저장 (all.txt, all_bbox.txt 용)
                page_all_elements.append((element.y0, text))
                page_all_bbox.append((element.y0, bbox_info))

                # 좌우 컬럼 분리: 시작점(x0) 기준 판단
                if element.x0 < (x0_page + half_width):
                    left_column.append((element.y0, text))
                    left_elements_bbox.append((element.y0, bbox_info))
                    page_layout_data["left"].append((element.x0, element.y0, element.x1, element.y1, text))
                else:
                    right_column.append((element.y0, text))
                    right_elements_bbox.append((element.y0, bbox_info))
                    page_layout_data["right"].append((element.x0, element.y0, element.x1, element.y1, text))

        # 각 페이지 내에서 y 좌표(높은 값 → 위쪽)를 기준으로 정렬
        left_column.sort(key=lambda x: -x[0])
        right_column.sort(key=lambda x: -x[0])
        page_all_elements.sort(key=lambda x: -x[0])
        page_all_bbox.sort(key=lambda x: -x[0])
        left_elements_bbox.sort(key=lambda x: -x[0])
        right_elements_bbox.sort(key=lambda x: -x[0])

        # 각 페이지의 텍스트를 이어붙임 (마지막에 페이지 구분자로 'page_{번호}' 추가)
        all_left.append("".join([text for _, text in left_column]) + f"\npage_{page_num}")
        all_right.append("".join([text for _, text in right_column]) + f"\npage_{page_num}")
        all_text.append("".join([text for _, text in page_all_elements]) + f"\npage_{page_num}")
        all_bbox.append("\n".join([bbox for _, bbox in page_all_bbox]) + f"\npage_{page_num}")
        left_bbox_all.append("\n".join([bbox for _, bbox in left_elements_bbox]) + f"\npage_{page_num}")
        right_bbox_all.append("\n".join([bbox for _, bbox in right_elements_bbox]) + f"\npage_{page_num}")

        # JSON용 bbox 데이터 (페이지 번호와 구조화된 bbox 리스트, pdf의 width/height를 페이지 단위로 저장)
        all_bbox_json_data.append({
            "page": page_num,
            "pdf_width": page_width,
            "pdf_height": page_height,
            "contents": page_bbox_info_json
        })

        # 페이지별 레이아웃 데이터 저장 (하이라이팅용)
        layout_data_list.append(page_layout_data)

    # 페이지별 줄바꿈으로 결합
    left_text = "\n".join(all_left)
    right_text = "\n".join(all_right)
    all_text_combined = "\n".join(all_text)
    all_bbox_text = "\n".join(all_bbox)
    left_bbox_text = "\n".join(left_bbox_all)
    right_bbox_text = "\n".join(right_bbox_all)

    return left_text, right_text, all_text_combined, all_bbox_text, left_bbox_text, right_bbox_text, layout_data_list, all_bbox_json_data


if __name__ == "__main__":
    pdf_path = r"C:\Users\yoyo2\바탕화면\pdf2md\test\pdf\정처기4~5p.pdf"
    # 추출 결과 7종류의 텍스트, 페이지별 레이아웃 데이터, 그리고 JSON용 bbox 데이터
    (left, right, all_txt, all_bbox, left_bbox, right_bbox,
     layout_data_list, all_bbox_json_data) = extract_text_layout(pdf_path)

    # PDF 파일 이름 추출 (확장자 제거)
    pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]

    output_dir = "test"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 텍스트 파일 저장 (총 6종류)
    left_file = os.path.join(output_dir, f"{pdf_filename}_left_column.txt")
    right_file = os.path.join(output_dir, f"{pdf_filename}_right_column.txt")
    all_file = os.path.join(output_dir, f"{pdf_filename}_all.txt")
    all_bbox_file = os.path.join(output_dir, f"{pdf_filename}_all_bbox.txt")
    left_bbox_file = os.path.join(output_dir, f"{pdf_filename}_left_bbox.txt")
    right_bbox_file = os.path.join(output_dir, f"{pdf_filename}_right_bbox.txt")

    with open(left_file, "w", encoding="utf-8") as f:
        f.write(left)
    with open(right_file, "w", encoding="utf-8") as f:
        f.write(right)
    with open(all_file, "w", encoding="utf-8") as f:
        f.write(all_txt)
    with open(all_bbox_file, "w", encoding="utf-8") as f:
        f.write(all_bbox)
    with open(left_bbox_file, "w", encoding="utf-8") as f:
        f.write(left_bbox)
    with open(right_bbox_file, "w", encoding="utf-8") as f:
        f.write(right_bbox)

    print("총 6개의 텍스트 파일이 저장되었습니다:")
    print(left_file)
    print(right_file)
    print(all_file)
    print(all_bbox_file)
    print(left_bbox_file)
    print(right_bbox_file)

    # 추가: {파일명}_all_bbox.json 파일 저장 (구조화된 JSON 형식으로 bbox 데이터 저장)
    all_bbox_json_file = os.path.join(output_dir, f"{pdf_filename}_all_bbox.json")
    with open(all_bbox_json_file, "w", encoding="utf-8") as f:
        json.dump(all_bbox_json_data, f, ensure_ascii=False, indent=2)
    print("JSON 파일이 저장되었습니다:")
    print(all_bbox_json_file)

    # -------------------------------------------------------------------------
    # 추가: PDFPlumber를 사용하여 페이지별로 하이라이팅 캡쳐 이미지 저장
    # 전체 페이지 영역(헤더/푸터 포함)을 사용합니다.
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            # 페이지 전체 영역 (MediaBox) 및 계산
            x0_page, y0_page, x1_page, y1_page = page.bbox
            page_width = x1_page - x0_page
            half_x = x0_page + (page_width / 2)

            # 해상도를 720dpi로 지정하여 캡쳐 (더 선명한 이미지)
            im = page.to_image(resolution=720)
            # 좌우 구분선 (빨간색, 두께 2) - 좌표 리스트로 전달
            im.draw_line([(half_x, y0_page), (half_x, y1_page)], stroke="red", stroke_width=2)

            # 미리 저장한 layout_data_list에서 해당 페이지의 레이아웃 정보 가져오기
            page_layout_data = layout_data_list[i-1]
            # 좌측 컬럼: 초록색
            for (x0, y0, x1, y1, txt) in page_layout_data["left"]:
                im.draw_rect((x0, y0, x1, y1), stroke="green", stroke_width=2)
            # 우측 컬럼: 파란색
            for (x0, y0, x1, y1, txt) in page_layout_data["right"]:
                im.draw_rect((x0, y0, x1, y1), stroke="blue", stroke_width=2)

            # 페이지별 하이라이트 이미지 저장 (PNG 형식)
            highlight_file = os.path.join(output_dir, f"{pdf_filename}_highlight_page{i}.png")
            im.save(highlight_file)
            print(f"페이지 {i} 하이라이트 이미지 저장: {highlight_file}")

    print("PDF 페이지별 하이라이트 이미지 저장이 완료되었습니다.")
