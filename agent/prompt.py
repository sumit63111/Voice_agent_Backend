from pathlib import Path
from datetime import date

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8")


def get_system_prompt() -> str:
    template = _load("system_prompt.txt")
    return template.replace("{current_date}", date.today().strftime("%A, %B %d, %Y"))


SYSTEM_PROMPT = get_system_prompt()
