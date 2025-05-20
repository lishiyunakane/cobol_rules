import json, os, re, openai

# ---------- Load Coding Rules ----------
with open("rules.json", encoding="utf-8") as f:
    RULES = json.load(f)

def rule_id(idx: int) -> str:
    """Generate rule ID like R001, R002, etc."""
    return f"R{idx+1:03d}"

def lookup_rules(rule_ids: list[str]) -> str:
    """Return structured content for a list of rule IDs"""
    blocks = []
    for rule_id in rule_ids:
        i = int(rule_id[1:]) - 1
        if 0 <= i < len(RULES):
            r = RULES[i]
            block = (
                f"[{rule_id}]\n"
                f"【内容】{r['content']}\n"
                f"【示例】{r['example']}"
            )
            blocks.append(block)
    return "\n\n".join(blocks)

# ---------- Build Summary Table ----------
summary_table = "\n".join(
    f"{i+1}. [{rule_id(i)}] {r['summary']}" for i, r in enumerate(RULES)
)

# ---------- Define local tool ----------
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_rule_detail_batch",
            "description": "Return detailed content and example for multiple rule IDs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "rule_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of coding rule IDs, e.g., ['R001', 'R004']"
                    }
                },
                "required": ["rule_ids"]
            }
        }
    }
]


# ---------- Example COBOL source code ----------
cobol_source = """
       IDENTIFICATION DIVISION.
       PROGRAM-ID. DEMO.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 USER-ID      PIC X(10).
       PROCEDURE DIVISION.
           DISPLAY USER-ID.
           STOP RUN.
"""

# ---------- Initial conversation messages ----------
messages = [
    {
        "role": "system",
        "content": (
             "You may request multiple rule details by calling `get_rule_detail_batch` with a list of rule IDs."

             "When the rules are returned (in format like [R001] ...), always quote the rule ID like [R004] when identifying violations."
        ),
    },
    {
        "role": "user",
        "content": f"# Coding Rules Summary Table\n{summary_table}\n\n# COBOL source code\n{cobol_source}",
    },
]

client = openai.OpenAI()  # Make sure OPENAI_API_KEY is set in your environment

# ---------- Agent conversation loop ----------
while True:
    resp = client.chat.completions.create(
        model="gpt-4o-2024-05-13",  # Or "gpt-4o", "gpt-4o-mini", "gpt-4-1106-preview"
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    msg = resp.choices[0].message
    # If the model called a tool:
    if msg.tool_calls:
    messages.append(msg)  # Add assistant message with tool_calls
        for call in msg.tool_calls:
            if call.function.name == "get_rule_detail_batch":
                args = json.loads(call.function.arguments)
                rule_ids = args["rule_ids"]  # List of rule IDs
                batch_content = lookup_rules(rule_ids)
    
                tool_response = {
                    "tool_call_id": call.id,
                    "role": "tool",
                    "name": "get_rule_detail_batch",
                    "content": batch_content
                }
            messages.append(tool_response)

    else:
        # Final model response is ready
        messages.append(msg)
        break

# ---------- Print final result ----------
final_answer = messages[-1]["content"]
print(final_answer)
