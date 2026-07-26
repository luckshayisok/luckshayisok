import os
from pathlib import Path

def _repo_root() -> Path:
    # resolve repo root as the directory containing this script
    return Path(__file__).parent.resolve()

def _resolve_candidate(path: str) -> Path:
    p = Path(path)
    # absolute paths are used as-is
    if p.is_absolute():
        return p
    # first try relative to script directory (robust to CWD)
    candidate = _repo_root().joinpath(p)
    if candidate.exists():
        return candidate
    # try siblings: .github/templates, assets/templates, templates/
    alt_paths = [
        _repo_root().joinpath("templates").joinpath(p.name),
        _repo_root().joinpath(".github").joinpath("templates").joinpath(p.name),
        _repo_root().joinpath("assets").joinpath("templates").joinpath(p.name),
        _repo_root().joinpath(p.name),
    ]
    for alt in alt_paths:
        if alt.exists():
            return alt
    # finally, try a repo-wide name search for files with the same basename (not expensive for CI)
    matches = list(_repo_root().rglob(p.name))
    if matches:
        return matches[0]
    # not found; return the first candidate checked for clear error messages
    return candidate

def render_svg(template_path, output_path, values):
    tpl = _resolve_candidate(template_path)
    if not tpl.exists():
        # helpful diagnostic listing nearby files
        parent = tpl.parent
        try:
            files = [f.name for f in parent.iterdir()]
        except FileNotFoundError:
            files = []
        # also show any svg files found anywhere (limit to 50)
        all_svgs = [str(p.relative_to(_repo_root())) for p in _repo_root().rglob("*.svg")]
        raise FileNotFoundError(
            f"Template not found at: {tpl}\n"
            f"Checked locations: {template_path} -> {tpl}\n"
            f"Files in {parent}: {files}\n"
            f"SVGs found in repo (up to 50): {all_svgs[:50]}"
        )

    svg = tpl.read_text(encoding="utf-8")
    for key, val in values.items():
        svg = svg.replace("{{" + key + "}}", str(val))

    out = _repo_root().joinpath(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
