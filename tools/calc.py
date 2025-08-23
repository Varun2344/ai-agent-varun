
def calculator(expr: str) -> str:
    allowed = "0123456789+-*/(). "
    if any(ch not in allowed for ch in expr or ""):
        return "Only basic arithmetic allowed."
    try:
        return str(eval(expr, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"[error] {e}"
