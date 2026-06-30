def format_duration(seconds: int) -> str:
    if not seconds or seconds <= 0:
        return "0:00"
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}:{secs:02d}"


def progress_bar(percent: float, length: int = 10) -> str:
    filled = int(length * percent / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"
