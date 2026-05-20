def parse_url(url):
    port = url[-4:]
    slash_index = url.rfind("/")
    colon_index = url.rfind(":")
    host = url[slash_index + 1:colon_index]

    return host, port

def score_color(score: float) -> str:
    """Return a hex colour for dark-mode display based on the relevance score."""
    if score >= 90:
        return "#34d399"
    elif score >= 75:
        return "#fbbf24"
    else:
        return "#fb7185"


def score_label(score: float) -> str:
    """Return a human-readable quality label for a relevance score."""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    else:
        return "Fair"


def format_authors(authors: list[str], max_show: int = 3) -> str:
    """Truncate a long author list to the first *max_show* names."""
    if len(authors) <= max_show:
        return ", ".join(authors)
    return ", ".join(authors[:max_show]) + f" + {len(authors) - max_show} more"