# flow0
flow0_sys_prompt = """
You are an expert in extracting the structure of COBOL programs. Strictly follow the instructions below and output only the module structure from the provided JSON input.
"""
flow0_prompt = """
Task
From the COBOL program requirements given in JSON format, detect how many parts the program can be divided into, and output only the result in the following format.

Output format
The program is divided into <N> parts: <Part 1>（要素）, 2. <Part 2>（要素）, …

※ Output only the result, and do not include any other text.
※ The result must indicate whether each part is a main program, a function, or another type.

Example:
Input (JSON):
{shot0_json}
Output (TEXT):
{shot0_text}
---
Actual Input (JSON):
{input_json}
Output (TEXT):(In Japanese)
"""
# flow1
flow1_process_prompt = """
▼ Supplementary Notes on Conditional Logic (effective only if `process_input_record_list` is present)
- If `process_input_record_list` contains items, it includes keys necessary for conditional branching.
- Each key contains the following information:
  - Record name (e.g., ITF1-REC)
  - Multiple layout IDs (e.g., JSMIGFD1120-LAY)
  - Used fields: each item listed in `physical_field_list`, including:
    - `data_project_name`: the logical field name (e.g.,利用法人カード番号)
    - `physical_project_name`: the actual physical field name used in COBOL (e.g.,`GFD11-ABCDE-CD`)
- When needed, the model must generate conditional branching logic using the correct record name and `physical_project_name`.
"""
flow1_sys_prompt = """
You are an experienced COBOL program design engineer. Based on the provided JSON-formatted program specifications and overall code structure, you are required to generate detailed and accurate COBOL code construction steps.
You must strictly follow the specified JSON output format and must not include any additional explanations or annotations in your response.
"""
flow1_prompt_1st = """
Based on the following two input sources, generate ダミーの手順 JSON that strictly follows the exact same format and writing style as the output sample.
The goal is only to learn the format and style of expression.
(The correctness of the processing content is not important at this stage.)

You must return only **structured JSON**. Do not include any other text, explanations, or comments.

▼ Output Format (Strictly Follow)
[
  {{
    "content": "第1のパート名",
    "steps": ["手順1", "手順2", "..."]
  }},
  {{
    "content": "第2のパート名",
    "steps": ["手順1", "手順2", "..."]
  }},
...
  {{
    "content": "第nのパート名",
    "steps": ["手順1", "手順2", "..."]
  }}
]
▼ Formatting and Style Rules
- The numbering and hyphen levels at the beginning of each line must match the output sample exactly (e.g., "--1. ", "----1. ")
- Add one more "--" for each deeper substep level.
- Do not create your own expressions that do not appear in the sample (reuse vocabulary and phrasing from the output sample only).

✦ No explanations or supplemental notes outside of JSON are allowed

 [Example: Format Reference]
Input:
【Input 1】Program Specification JSON:
{shot1_json}
【Input 2】Overall Program Structure:
{shot1_text}
Output Sample:
【Output】Detailed Code Steps:
{shot1_steps_json}
---
Actual Task Input (focus is on format, not content correctness):
【Input 1】Program Specification JSON:
{input_json}
【Input 2】Overall Program Structure:
{input_text}
【Output】Detailed Code Steps (ダミーの手順 in JSON for format imitation): (In Japanese)

Carefully analyze the program specification JSON from 【Input 1】 and the overall program structure in 【Input 2】, and write the required detailed steps for COBOL program development in a clear and structured JSON format according to the provided output sample format.
Do not include any explanations, comments, or non-JSON content.
If there are loops or conditionals within the steps, prefix substeps with "--". Add an extra "--" for each level of nesting.
"""

flow1_prompt_2nd = """
Based on the two input sources and the "First-Generated JSON", revise **only the content** to create the final version of the procedure.
The format, writing style, step hierarchy, and sentence endings must **exactly follow the First-Generated JSON**.
The core logic must strictly comply with the `processing_steps.description`.
(You have already learned the format; therefore, no changes to it are allowed.)

You must return **only structured JSON**, and absolutely no other text, explanations, or annotations.

▼ Rules on Editable Elements
- text of `steps[]`: You may revise or add content based on the program specification.
- Array structure, order, numbering, and hyphen-based hierarchy: Do not modify.
- Follow logic decisions such as "出力する", "読み飛ばす", etc. exactly as indicated in `processing_steps.description`.

▼ Special Rule (Important):
- If a record name (e.g., OTF1-REC) is specified in layout_output_record_list, use that record name (i.e., the key of layout_output_record_list) directly when describing the write step. You do not need to include any reasoning (such as “空でないため”); simply describe the action.
  ➤ In this case, before calling the WRITE function within the main processing メイン処理 (function), you must explicitly include a step to set the input record (e.g., ITF1-REC) to the record name specified in layout_output_record_list (e.g., OTF1-REC).
  Example:
  × ITF1-RECをOTF1-RECとして出力ファイルに書き込む（関数実行）
  〇 ITF1-RECをOTF1-RECに設定する。OTF1-RECとして出力ファイルに書き込む（関数実行）

  ➤ Similarly, in the “「OTF1情報を書き込む（関数）” section, the first input record should also be set to the record name specified in layout_output_record_list.

- On the other hand, if layout_output_record_list is empty, the first input record (e.g., ITF1-REC) should be written to OTF1, and you must also explicitly include the step to set this record.

{flow1_process_prompt}

▼ Output Format (Strictly Required)
Follow the structure exactly as shown below.
[
  {{
    "content": "第1のパート名",
    "steps": ["手順1", "手順2", "..."]
  }},
  {{
    "content": "第2のパート名",
    "steps": ["手順1", "手順2", "..."]
  }},
...
  {{
    "content": "第nのパート名",
    "steps": ["手順1", "手順2", "..."]
  }}
]

▼ Formatting & Style Rules
- The numbering and hyphen levels at the beginning of each line must match the output sample exactly (e.g., "--1. ", "----1. ")
- Add one more "--" for each deeper substep level.
- Do not create your own expressions that do not appear in the sample (reuse vocabulary and phrasing from the output sample only).

✦ No explanations or supplemental notes outside of JSON are allowed

Actual Inputs:
【First Output】Detailed Code Steps (used as formatting reference):
{output_step_json}
【Input 1】Program Specification JSON:
{input_json}
【Input 2】Overall Program Structure:
{input_text}

---
【Output】Final Detailed Code Steps (Keep format exactly the same, revise only the content based on the inputs): (In Japanese)

Carefully analyze the program specification JSON from 【Input 1】 and the overall program structure in 【Input 2】, and write the required detailed steps for COBOL program development in a clear and structured JSON format according to the provided output sample format.
Do not include any explanations, comments, or non-JSON content.
If there are loops or conditionals within the steps, prefix substeps with "--". Add an extra "--" for each level of nesting.
"""
