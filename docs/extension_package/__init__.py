from pathlib import Path

def get_templates_path() -> Path:
    return Path(__file__).parent / "templates"
