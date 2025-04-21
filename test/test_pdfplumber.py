import os
import json
import pdfplumber
import pandas as pd
import openpyxl
from openpyxl.styles import Alignment

# 표 추출을 위한 설정 (필요에 따라 조정)
TABLE_SETTINGS = {
    "vertical_strategy": "lines",  # 세로 방향에서 셀 구분을 결정하는 전략입니다.
                                    # 가능한 값: "lines", "lines_strict", "text", "explicit"
                                    # 기본값: "lines"

    "horizontal_strategy": "lines",  # 가로 방향에서 셀 구분을 결정하는 전략입니다.
                                        # 가능한 값: "lines", "lines_strict", "text", "explicit"
                                        # 기본값: "lines"

    "snap_tolerance": 3,  # 병합 가능한 선 간의 거리 허용 오차 (px 단위)
                            # 가까운 선들을 정렬 시 하나로 인식함
                            # 일반 범위: 1 ~ 5

    "snap_x_tolerance": 2,  # x 방향 병합 허용 오차
                            # snap_tolerance보다 정밀한 조정이 필요할 때 사용

    "snap_y_tolerance": 2,  # y 방향 병합 허용 오차

    "join_tolerance": 3,  # 서로 다른 선을 하나로 합칠 수 있는 최대 거리
                            # 예: 연결된 테이블 선의 불완전한 연결 보완

    "join_x_tolerance": 3,  # x 방향에서 선을 병합하는 기준 거리

    "join_y_tolerance": 3,  # y 방향에서 선을 병합하는 기준 거리

    "edge_min_length": 3,  # 셀을 나누는 선으로 간주하기 위한 최소 선 길이 (px)
                            # 짧은 선은 무시됨

    "min_words_vertical": 3,  # vertical_strategy가 "text"일 때
                                # 수직으로 정렬된 최소 단어 수 기준

    "min_words_horizontal": 1,  # horizontal_strategy가 "text"일 때
                                # 수평으로 정렬된 최소 단어 수 기준

    "intersection_tolerance": 3,  # 선들이 교차한다고 판단할 수 있는 허용 거리

    "intersection_x_tolerance": 3,  # x 방향 교차 판단 거리

    "intersection_y_tolerance": 3,  # y 방향 교차 판단 거리

    "text_tolerance": 3,  # 텍스트를 병합하거나 셀 내에서 판단할 때 위치 오차 허용값

    "text_x_tolerance": 3,  # x 방향 텍스트 위치 판단 오차

    "text_y_tolerance": 3,  # y 방향 텍스트 위치 판단 오차
}


def set_wrap_text_in_excel(excel_path):
    """openpyxl을 이용해 Excel 파일의 모든 셀에 자동 줄바꿈을 활성화합니다."""
    wb = openpyxl.load_workbook(excel_path)
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is not None:
                    cell.alignment = Alignment(wrap_text=True)
    wb.save(excel_path)

def extract_tables_only(pdf_path):
    """
    PDF의 각 페이지에서 표로 인식되는 부분만 추출하여,
    표 데이터는 JSON 및 Excel 파일로 저장하고,
    추가로 해당 표 영역이 어디에서 추출되었는지 캡쳐한 이미지를 저장합니다.
    Excel 저장 시, 모든 셀에 자동 줄바꿈과 열 너비 자동 조정이 활성화됩니다.
    """
    base_output_dir = "test/pdfplumber"
    # PDF 파일명(확장자 제외)을 접두사로 사용
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    output_dir = os.path.join(base_output_dir, filename)
    os.makedirs(output_dir, exist_ok=True)

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            # 표 데이터를 추출 (데이터 저장용)
            tables_data = page.extract_tables(TABLE_SETTINGS)
            # 표 객체 추출 (이미지 저장용) → bbox 정보를 포함
            table_objs = page.find_tables(TABLE_SETTINGS)

            if not tables_data or not table_objs:
                print(f"페이지 {page_number}: 표 없음")
                continue

            # 두 리스트가 같은 순서로 있다고 가정
            for table_index, (table, table_obj) in enumerate(zip(tables_data, table_objs), start=1):
                # JSON 파일로 저장
                json_path = os.path.join(output_dir, f"page_{page_number}_table_{table_index}.json")
                with open(json_path, "w", encoding="utf-8") as json_file:
                    json.dump(table, json_file, ensure_ascii=False, indent=4)
                print(f"페이지 {page_number}의 표 {table_index}가 {json_path}에 저장되었습니다.")

                # Excel 파일로 저장: DataFrame으로 변환 후 저장
                df = pd.DataFrame(table)
                excel_path = os.path.join(output_dir, f"page_{page_number}_table_{table_index}.xlsx")
                df.to_excel(excel_path, index=False, engine="openpyxl")
                set_wrap_text_in_excel(excel_path)
                print(f"페이지 {page_number}의 표 {table_index}가 {excel_path}에 저장되었으며, 자동 줄바꿈을 활성화했습니다.")

                # 표 영역 이미지 저장
                # table_obj.bbox는 (x0, top, x1, bottom) 형식입니다.
                orig_bbox = table_obj.bbox
                # 부모 페이지 bbox: (page_x0, page_y0, page_x1, page_y1)
                page_bbox = page.bbox
                page_x0, page_y0, page_x1, page_y1 = page_bbox
                # table_obj.bbox가 부모 페이지 bbox 내에 있지 않을 경우, 좌표를 클램핑(clamping)합니다.
                clamped_bbox = (
                    max(orig_bbox[0], page_x0),
                    max(orig_bbox[1], page_y0),
                    min(orig_bbox[2], page_x1),
                    min(orig_bbox[3], page_y1)
                )
                # 클램핑된 bbox를 사용해 페이지에서 해당 영역만 추출
                try:
                    table_region = page.within_bbox(clamped_bbox)
                except ValueError as e:
                    print(f"페이지 {page_number}의 표 {table_index} bbox 에러: {e}")
                    continue

                # 추출한 영역을 이미지로 생성 (해상도 300dpi)
                table_img = table_region.to_image(resolution=300)
                # 표 영역에 하이라이팅 (초록색 사각형)
                table_img.draw_rect(clamped_bbox, stroke="green", stroke_width=2)
                table_img_path = os.path.join(output_dir, f"page_{page_number}_table_{table_index}_image.png")
                table_img.save(table_img_path, format="PNG")
                print(f"페이지 {page_number}의 표 {table_index} 이미지가 {table_img_path}에 저장되었습니다.")

if __name__ == '__main__':
    pdf_path = "./test/pdf/정처기4~5p.pdf"  # PDF 파일 경로를 필요에 맞게 수정하세요.
    extract_tables_only(pdf_path)