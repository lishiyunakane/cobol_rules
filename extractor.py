from pathlib import Path
import pandas as pd
import json
import re
import os

OUTPUT_DIR = Path("output_json")
OUTPUT_DIR.mkdir(exist_ok=True)

# 指定要遍历的文件夹
INPUT_DIR = Path(".")  # 当前目录，也可以写成 Path("your_folder")

# 遍历所有包含“詳細設計書”的xlsx文件
for file_path in INPUT_DIR.glob("*詳細設計書*.xlsx"):
    xls = pd.ExcelFile(file_path)
    shori_id_match = re.search(r'[A-Z]{2}-[A-Z]-\d+', os.path.basename(file_path))
    shori_id = shori_id_match.group() if shori_id_match else None

    results = []

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)

        if 'ロジック' in sheet_name:
            data_type = 'ロジック'

            name_match = df.apply(lambda x: x.astype(str).str.contains('名称')).stack()
            name_pos = name_match[name_match].index[0]
            logic_name = df.iloc[name_pos[0], name_pos[1]+1]

            summary_match = df.apply(lambda x: x.astype(str).str.contains('概要')).stack()
            summary_pos = summary_match[summary_match].index[0]
            logic_summary = df.iloc[summary_pos[0], summary_pos[1]+1]

            logic_detail_match = df.apply(lambda x: x.astype(str).str.contains('処理ロジック詳細')).stack()
            logic_detail_start = logic_detail_match[logic_detail_match].index[0][0] + 1
            logic_detail_end = df.iloc[logic_detail_start:, 2].first_valid_index()
            logic_detail = df.iloc[logic_detail_start:logic_detail_end, :].dropna(how='all').stack().tolist()
            logic_detail_str = '\n'.join(logic_detail)

            sql_ids = sorted(set(re.findall(r'SQL-\d+', logic_detail_str)))

            results.append({
                '処理ID': shori_id,
                'sheet_name': sheet_name,
                'file_name': os.path.basename(file_path),
                'file_path': str(Path(file_path).resolve()),
                'タイプ': data_type,
                '概要': logic_summary,
                'ロジック名称': logic_name,
                'ロジック詳細': logic_detail_str if logic_detail_str else None,
                'SQLID': sql_ids if sql_ids else None,
            })

        elif 'SQL定義' in sheet_name:
            data_type = 'SQL定義'

            sql_id = None
            sqlid_cell = df[df.apply(lambda x: x.astype(str).str.contains('SQL-ID')).any(axis=1)]
            if not sqlid_cell.empty:
                row_idx = sqlid_cell.index[0]
                col_idx = df.columns[df.iloc[row_idx].astype(str).str.contains('SQL-ID')][0] + 5
                sql_id = df.iloc[row_idx, col_idx]

            purpose = None
            purpose_cell = df[df.apply(lambda x: x.astype(str).str.contains('使用目的')).any(axis=1)]
            if not purpose_cell.empty:
                header_row_idx = purpose_cell.index[0]
                col_idx = df.columns[df.iloc[header_row_idx].astype(str).str.contains('使用目的')][0]
                purpose_row_idx = header_row_idx + 1
                purpose_row = df.iloc[purpose_row_idx, col_idx:].dropna().astype(str).tolist()
                purpose = '\n'.join(purpose_row)

            operation = None
            oper_cell = df[df.apply(lambda x: x.astype(str).str.contains('操作')).any(axis=1)]
            if not oper_cell.empty:
                row_idx = oper_cell.index[0]
                col_idx = df.columns[df.iloc[row_idx].astype(str).str.contains('操作')][0] + 5
                operation = df.iloc[row_idx, col_idx]

            sql_code = ''
            logic_sql_row = df[df.apply(lambda x: x.astype(str).str.contains('論理SQL')).any(axis=1)]
            if not logic_sql_row.empty:
                start_row = logic_sql_row.index[0] + 1
                sql_area = df.iloc[start_row:, :20].dropna(how='all')
                sql_code_cells = sql_area.stack().reset_index()
                sql_code_cells.columns = ['row', 'col', 'content']
                sql_code = '\n'.join(sql_code_cells['content'].astype(str).tolist())

            results.append({
                '処理ID': shori_id,
                'sheet_name': sheet_name,
                'file_name': os.path.basename(file_path),
                'file_path': str(Path(file_path).resolve()),
                'タイプ': data_type,
                '使用目的': purpose if pd.notna(purpose) else None,
                'SQLID': sql_id if pd.notna(sql_id) else None,
                '操作': operation if pd.notna(operation) else None,
                '論理SQL': sql_code,
            })

    # 输出为每个文件一个JSON
    output_path = OUTPUT_DIR / (Path(file_path).stem + ".json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"已输出到: {output_path.resolve()}")
