# ---------- 1. Prompt Template (for GPT/Agent) ----------
PROMPT = """
You are a COBOL code formatting expert.

For the given COBOL code, your task is to analyze the logical structure (such as IF blocks, PERFORM blocks, etc.) and suggest formatting modifications.

Please group all necessary line modifications that belong to the same logical unit (for example, one IF block, or one PERFORM block) together as a single modification.

For each group, specify:
- The line numbers to be modified (0-based, first line is 0)
- For each line, the target starting column (e.g., 12 or 15)
- A brief reason for the modification

Output as a JSON array, where each element represents a logical modification batch, for example:

[
  {
    "lines": [
      {"line": 1, "target_col": 12},
      {"line": 3, "target_col": 12}
    ],
    "reason": "IF control structure block"
  },
  {
    "lines": [
      {"line": 2, "target_col": 15}
    ],
    "reason": "Statement inside IF block"
  }
]

Only output the JSON array. Do not explain further.
"""

# ---------- 2. Python formatting function ----------
def apply_format_batches(lines, batch_suggestions):
    """
    Adjust COBOL code indentation according to GPT/Agent suggestions.

    Args:
        lines (List[str]): Original COBOL code as a list of strings (one line per item).
        batch_suggestions (List[Dict]): List of formatting instructions, each for a logical block.
                                         Each dict has a "lines" array and a "reason".

    Returns:
        formatted_lines (List[str]): COBOL code after indentation adjustment.
        change_log (List[Dict]): Log of changes for each batch (for auditing or UI feedback).
    """
    result = lines[:]
    change_log = []
    for batch in batch_suggestions:
        changed_lines = []
        for item in batch["lines"]:
            idx = item["line"]
            col = item["target_col"]
            stripped = result[idx].strip()
            padded = " " * (col - 1) + stripped
            result[idx] = padded.ljust(72)
            changed_lines.append({"line": idx, "content": result[idx]})
        change_log.append({"reason": batch.get("reason", ""), "changed_lines": changed_lines})
    return result, change_log

# ---------- 3. Example: Full Workflow Demo ----------
if __name__ == "__main__":
    # Sample COBOL code (as plain lines, no indentation)
    cobol_lines = [
        "IDENTIFICATION DIVISION.",
        "PROGRAM-ID. SAMPLE.",
        "PROCEDURE DIVISION",
        "IF A > B",
        "MOVE A TO B",
        "END-IF",
        "PERFORM CALC-ROUTINE",
        "END-PERFORM"
    ]
    
    # Simulated output from GPT/Agent (in reality, you would call GPT API and parse JSON)
    batch_suggestions = [
        {
            "lines": [
                {"line": 3, "target_col": 12},  # IF
                {"line": 5, "target_col": 12},  # END-IF
                {"line": 6, "target_col": 12},  # PERFORM
                {"line": 7, "target_col": 12}   # END-PERFORM
            ],
            "reason": "Control statements should start from column 12"
        },
        {
            "lines": [
                {"line": 4, "target_col": 15}  # MOVE
            ],
            "reason": "Statement inside IF block"
        }
    ]

    # Apply formatting based on GPT/Agent suggestions
    formatted_code, change_log = apply_format_batches(cobol_lines, batch_suggestions)

    print("------ Formatted COBOL Code ------")
    print("\n".join(formatted_code))
    print("\n------ Change Log (by batch) ------")
    for i, batch in enumerate(change_log, 1):
        print(f"[Batch {i}] {batch['reason']}")
        for line in batch["changed_lines"]:
            print(f"  Line {line['line']}: {line['content']}")
