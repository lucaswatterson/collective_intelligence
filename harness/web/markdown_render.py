import markdown as _md


_MD = _md.Markdown(
    extensions=["fenced_code", "tables", "sane_lists"],
    output_format="html5",
)


def render_markdown(text: str) -> str:
    _MD.reset()
    return _MD.convert(text)
