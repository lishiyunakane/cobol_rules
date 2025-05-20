import json, os, re, openai

# ---------- Load Coding Rules ----------
with open("rules.json", encoding="utf-8") as f:
    RULES = json.load(f)

def rule_id(idx: int) -> str:
    """Generate rule ID like R001, R002, etc."""
    return f"R{idx+1:03d}"

def lookup_rule(rule_id: str) -> dict:
    """Lookup detailed rule content locally; return empty fields if not found"""
    i = int(rule_id[1:]) - 1
    if 0 <= i < len(RULES):
        r = RULES[i]
        return {
            "rule_id": rule_id,
            "summary": r["summary"],
            "content": r["content"],
            "example": r["example"],
        }
    return {"rule_id": rule_id, "summary": "", "content": "", "example": ""}

# ---------- Build Summary Table ----------
summary_table = "\n".join(
    f"{i+1}. [{rule_id(i)}] {r['summary']}" for i, r in enumerate(RULES)
)

# ---------- Define local tool ----------
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_rule_detail",
            "description": "Return detailed rule content and example for a given rule ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "rule_id": {
                        "type": "string",
                        "description": "Coding rule ID, e.g. R001",
                    }
                },
                "required": ["rule_id"],
            },
        },
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
            "You are an enterprise COBOL code reviewer. "
            "First, scan the code using the Coding Rules Summary Table only. "
            "If you require the full text of any rule, call `get_rule_detail` with the rule_id. "
            "After all needed details are retrieved, output:\n"
            "Step 1 → issues table (line, rule_id, reason)\n"
            "Step 2 → unified diff patch\n"
            "Step 3 → final corrected COBOL code inside ```cobol ...``` block.\n"
            "Pay extreme attention to indentation requirements."
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
        for call in msg.tool_calls:
            func_name = call.function.name
            args = json.loads(call.function.arguments)
            if func_name == "get_rule_detail":
                rid = args["rule_id"]
                detail = lookup_rule(rid)
                # Return the detailed content as a tool response
                tool_message = {
                    "tool_call_id": call.id,
                    "role": "tool",
                    "name": func_name,
                    "content": (
                        f"[{detail['rule_id']}]\n"
                        f"【内容】{detail['content']}\n"
                        f"【示例】{detail['example']}"
                    ),
                }
                messages.append(msg)          # Log the model’s request
                messages.append(tool_message) # Log the tool's response
    else:
        # Final model response is ready
        messages.append(msg)
        break

# ---------- Print final result ----------
final_answer = messages[-1]["content"]
print(final_answer)
