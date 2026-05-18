"""
utils.py — Pure helper / formatting functions for CiteSense.
No Streamlit imports; safe to unit-test independently.
"""

def parse_url(url):
    port = url[-4:]
    slash_index = url.rfind("/")
    colon_index = url.rfind(":")
    host = url[slash_index + 1:colon_index]

    return host, port

def score_color(score: float) -> str:
    """Return a hex colour for dark-mode display based on the relevance score."""
    if score >= 0.90:
        return "#34d399"   # emerald
    elif score >= 0.75:
        return "#fbbf24"   # amber
    else:
        return "#fb7185"   # rose


def score_label(score: float) -> str:
    """Return a human-readable quality label for a relevance score."""
    if score >= 0.90:
        return "Excellent"
    elif score >= 0.75:
        return "Good"
    else:
        return "Fair"


def format_authors(authors: list[str], max_show: int = 3) -> str:
    """Truncate a long author list to the first *max_show* names."""
    if len(authors) <= max_show:
        return ", ".join(authors)
    return ", ".join(authors[:max_show]) + f" +{len(authors) - max_show} more"


def apa_citation(paper: dict) -> str:
    """Build a simple APA-style citation string for a paper dict."""
    authors_str = "; ".join(paper["authors"])
    return (
        f"{authors_str} ({paper['year']}). {paper['title']}. "
        f"*{paper['venue']}*. https://doi.org/{paper['doi']}"
    )
