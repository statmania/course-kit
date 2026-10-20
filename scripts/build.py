#!/usr/bin/env python3
"""Pre-render step: build the course home page and module overview pages.

Reads
  - _quarto.yml       -> sidebar order (modules and lessons)
  - index.qmd         -> `course:` block (level, outcomes, instructor, ...)
  - each .qmd's front matter -> title, description, minutes, kind

Writes (all under _generated/, included by index.qmd and module index.qmd)
  - home.md           course home page (raw HTML in a fenced block)
  - <module>.md       lesson list for a module overview page
"""
import html
import os
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "_generated"
KIND_ICON = {"read": "fa-book-open", "code": "fa-code", "quiz": "fa-circle-question", "lab": "fa-flask"}
KIND_LABEL = {"read": "Reading", "code": "Code", "quiz": "Quiz", "lab": "Lab"}


def e(s):
    return html.escape(str(s), quote=True)


def front_matter(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta = yaml.safe_load(m.group(1)) if m else {}
    return meta or {}, text


def page(href):
    meta, text = front_matter(href)
    return {
        "href": href,
        "url": re.sub(r"\.qmd$", ".html", href),
        "title": meta.get("title", Path(href).stem),
        "description": meta.get("description", ""),
        "minutes": int(meta.get("minutes", 0) or 0),
        "kind": meta.get("kind", "read"),
        "quizzes": len(re.findall(r'data-quiz="', text)),
        "meta": meta,
    }


def load_structure():
    cfg = yaml.safe_load((ROOT / "_quarto.yml").read_text(encoding="utf-8"))
    modules = []
    for item in cfg["website"]["sidebar"]["contents"]:
        if isinstance(item, dict) and "section" in item:
            mod = page(item["href"])
            mod["title"] = item["section"]
            mod["slug"] = Path(item["href"]).parent.name
            mod["lessons"] = [page(h if isinstance(h, str) else h["href"]) for h in item["contents"]]
            modules.append(mod)
    return cfg, modules


def rel(target_url, from_dir):
    return os.path.relpath(target_url, from_dir).replace(os.sep, "/")


def lesson_row(lesson, base_dir, num):
    k = lesson["kind"] if lesson["kind"] in KIND_ICON else "read"
    mins = f'{lesson["minutes"]} min' if lesson["minutes"] else ""
    desc = f'<span class="lr-desc">{e(lesson["description"])}</span>' if lesson["description"] else ""
    lid = re.sub(r"\.html$", "", lesson["url"])
    return (
        f'<a class="lesson-row" href="{e(rel(lesson["url"], base_dir))}" data-lesson="{e(lid)}">'
        f'<span class="lr-icon lr-{k}"><i class="fa-solid {KIND_ICON[k]}"></i></span>'
        f'<span class="lr-body"><span class="lr-title"><span class="lr-num">{num}</span>{e(lesson["title"])}</span>{desc}</span>'
        f'<span class="lr-meta"><span class="lr-kind">{KIND_LABEL[k]}</span>{e(mins)}</span>'
        f'<span class="lr-check" aria-hidden="true"><i class="fa-solid fa-circle-check"></i></span>'
        f"</a>"
    )


def fenced(markup):
    return "```{=html}\n" + markup + "\n```\n"


def build_module_pages(modules):
    for mi, mod in enumerate(modules, 1):
        rows = "".join(lesson_row(l, f"modules/{mod['slug']}", f"{mi}.{li}") for li, l in enumerate(mod["lessons"], 1))
        (GEN / f"{mod['slug']}.md").write_text(fenced(f'<div class="lesson-list">{rows}</div>'), encoding="utf-8")


def build_home(cfg, modules):
    meta, _ = front_matter("index.qmd")
    c = meta.get("course", {})
    inst = c.get("instructor", {})
    lessons = [l for m in modules for l in m["lessons"]]
    total_min = sum(l["minutes"] for l in lessons)
    hours = f"{total_min / 60:.1f}".rstrip("0").rstrip(".") if total_min >= 60 else f"{total_min} min"
    hours = f"{hours} hours" if total_min >= 60 else hours
    quizzes = sum(l["quizzes"] for l in lessons)
    first = lessons[0]["url"] if lessons else "#"

    chips = "".join(f'<span class="chip chip-{i}">{e(lv)}</span>' for i, lv in enumerate(c.get("levels", [])))
    sep = '<i class="fa-solid fa-angle-right"></i>'
    crumbs = sep.join(['<a href="../index.html">All courses</a>'] + [f"<span>{e(x)}</span>" for x in c.get("category", [])])
    outcomes = "".join(f'<li><i class="fa-solid fa-check"></i><span>{e(o)}</span></li>' for o in c.get("outcomes", []))
    reqs = "".join(f"<li>{e(r)}</li>" for r in c.get("requirements", []))
    includes = "".join(f'<li><i class="fa-solid {e(i["icon"])}"></i>{e(i["text"])}</li>' for i in c.get("includes", []))
    stats = [
        (len(modules), "modules", "fa-layer-group"),
        (len(lessons), "lessons", "fa-book-open"),
        (hours, "of content", "fa-clock"),
        (quizzes, "quiz questions", "fa-circle-question"),
    ]
    stats_html = "".join(
        f'<div class="stat"><i class="fa-solid {ic}"></i><div><b>{e(n)}</b><span>{e(l)}</span></div></div>'
        for n, l, ic in stats
    )

    acc = []
    for mi, mod in enumerate(modules, 1):
        mins = sum(l["minutes"] for l in mod["lessons"])
        rows = "".join(lesson_row(l, ".", f"{mi}.{li}") for li, l in enumerate(mod["lessons"], 1))
        desc = f'<p class="mod-desc">{e(mod["description"])}</p>' if mod["description"] else ""
        acc.append(
            f'<details class="module" open data-module="{e(mod["slug"])}">'
            f'<summary><span class="mod-num">Module {mi}</span>'
            f'<span class="mod-title">{e(mod["title"])}</span>'
            f'<span class="mod-meta"><span class="mod-count" data-total="{len(mod["lessons"])}">{len(mod["lessons"])} lessons</span> · {mins} min</span>'
            f'<i class="fa-solid fa-chevron-down mod-chev"></i></summary>{desc}'
            f'<div class="lesson-list">{rows}</div></details>'
        )

    why = c.get("why")
    why_html = ""
    if why:
        cards_html = "".join(
            f'<div class="why-card"><i class="fa-solid {e(i["icon"])}"></i><h3>{e(i["title"])}</h3><p>{e(i["text"])}</p></div>'
            for i in why.get("items", [])
        )
        repro = "".join(f"<div>{e(line)}</div>" for line in why.get("repro", []))
        why_html = (
            f'<h2 class="ch-h"><span class="ch-emoji">🔁</span> {e(why.get("title", ""))}</h2>'
            f'<p class="why-intro">{e(why.get("intro", ""))}</p>'
            f'<div class="why-grid">{cards_html}</div>'
            + (f'<div class="why-repro"><span>Rebuild it yourself</span><code>{repro}</code></div>' if repro else "")
            + (f'<p class="why-note"><i class="fa-solid fa-circle-info"></i> {e(why["cms_note"])}</p>' if why.get("cms_note") else "")
        )

    initials = "".join(w[0] for w in inst.get("name", "?").split()[:2]).upper()
    home = f"""
<div class="ch" data-total="{len(lessons)}" data-first="{e(first)}">
<nav class="ch-crumbs">{crumbs}</nav>
<section class="ch-hero">
  <div class="ch-hero-main">
    <div class="ch-chips">{chips}</div>
    <h1 class="ch-title">{e(meta.get("title", ""))}</h1>
    <p class="ch-desc">{e(meta.get("description", ""))}</p>
    <div class="ch-byline">
      <span class="ch-avatar">{e(initials)}</span>
      <span class="ch-by">Created by<br><b>{e(inst.get("name", ""))}</b>{", " + e(inst.get("role", "")) if inst.get("role") else ""}</span>
      <span class="ch-updated"><i class="fa-solid fa-pen"></i> Last updated {e(c.get("updated", ""))}</span>
    </div>
  </div>
</section>

<div class="ch-tabs" role="tablist">
  <button role="tab" data-tab="overview" class="active"><i class="fa-solid fa-table-cells-large"></i> Overview</button>
  <button role="tab" data-tab="content"><i class="fa-solid fa-list-check"></i> Course content</button>
  <button role="tab" data-tab="instructor"><i class="fa-solid fa-chalkboard-user"></i> Instructor</button>
</div>

<section class="ch-panel active" id="tab-overview">
  <h2 class="ch-h"><span class="ch-emoji">📚</span> What you'll learn</h2>
  <ul class="outcomes">{outcomes}</ul>
  <div class="stats">{stats_html}</div>
  {why_html}
  <h2 class="ch-h"><span class="ch-emoji">🧰</span> Requirements</h2>
  <ul class="reqs">{reqs}</ul>
</section>

<section class="ch-panel" id="tab-content">
  <div class="content-head"><h2 class="ch-h">Course content</h2><button type="button" class="btn-ghost" id="toggle-all">Collapse all</button></div>
  {''.join(acc)}
</section>

<section class="ch-panel" id="tab-instructor">
  <div class="inst">
    <span class="ch-avatar ch-avatar-lg">{e(initials)}</span>
    <div><h2 class="ch-h" style="margin-top:0">{e(inst.get("name", ""))}</h2>
    <p class="inst-role">{e(inst.get("role", ""))}</p><p>{e(inst.get("bio", ""))}</p></div>
  </div>
</section>
</div>
"""
    rail = f"""
  <div class="ch-card">
    <div class="ring-row">
      <svg class="ring" viewBox="0 0 64 64" aria-hidden="true"><circle class="ring-bg" cx="32" cy="32" r="26"/><circle class="ring-fg" cx="32" cy="32" r="26"/></svg>
      <div><div class="ring-pct">0%</div><div class="ring-sub"><span class="ring-done">0</span> of {len(lessons)} lessons</div></div>
    </div>
    <a class="btn-go" href="{e(first)}"><span class="btn-go-label">Start course</span> <i class="fa-solid fa-arrow-right"></i></a>
    <button class="btn-reset" type="button" hidden>Reset progress</button>
    <ul class="ch-includes">{includes}</ul>
  </div>
"""
    (GEN / "home.md").write_text(fenced(home), encoding="utf-8")
    (GEN / "home-rail.md").write_text(fenced(rail), encoding="utf-8")


def build_catalog(modules):
    cfg = yaml.safe_load((ROOT / "courses.yml").read_text(encoding="utf-8"))
    lessons = [l for m in modules for l in m["lessons"]]
    mins = sum(l["minutes"] for l in lessons)
    courses = cfg["courses"]
    for c in courses:
        if c.get("self"):
            c["lessons"] = len(lessons)
            c["hours"] = round(mins / 60, 1)
    by_slug = {c["slug"]: c for c in courses}

    def facet(key):
        counts = {}
        for c in courses:
            counts[c[key]] = counts.get(c[key], 0) + 1
        return counts

    def facet_html(title, key):
        rows = "".join(
            f'<label><input type="checkbox" data-facet="{key}" value="{e(v)}"> <span>{e(v)}</span><b>{n}</b></label>'
            for v, n in sorted(facet(key).items())
        )
        return f'<div class="cat-group"><h4>{e(title)}</h4>{rows}</div>'

    status_label = {"live": "Available", "soon": "Coming soon"}
    status_rows = "".join(
        f'<label><input type="checkbox" data-facet="status" value="{k}"> <span>{status_label[k]}</span><b>{sum(1 for c in courses if c["status"] == k)}</b></label>'
        for k in ("live", "soon")
        if any(c["status"] == k for c in courses)
    )

    cards = []
    for i, c in enumerate(courses):
        soon = c["status"] == "soon"
        meta = []
        if c.get("lessons"):
            meta.append(f'<span><i class="fa-solid fa-book-open"></i> {c["lessons"]} lessons</span>')
        if c.get("hours"):
            meta.append(f'<span><i class="fa-regular fa-clock"></i> {c["hours"]} h</span>')
        if c.get("updated"):
            meta.append(f'<span><i class="fa-solid fa-pen"></i> {e(c["updated"])}</span>')
        action = (
            '<span class="cc-btn cc-soon">Coming soon</span>'
            if soon
            else f'<a class="cc-btn" href="{e(c["url"])}"><span class="cc-btn-label">Start course</span> <i class="fa-solid fa-arrow-right"></i></a>'
        )
        cards.append(
            f'<div class="cc{" is-soon" if soon else ""}" data-slug="{e(c["slug"])}" data-root="{e(c["url"])}" data-total="{c.get("lessons", 0)}" '
            f'data-level="{e(c["level"])}" data-category="{e(c["category"])}" data-status="{e(c["status"])}" '
            f'data-updated="{e(c.get("updated", ""))}" data-featured="{1 if c.get("featured") else 0}" data-order="{i}" data-title="{e(c["title"]).lower()}" '
            f'data-text="{e(c["title"] + " " + c["description"] + " " + c["category"]).lower()}">'
            f'<div class="cc-thumb"><i class="fa-solid {e(c["icon"])}"></i></div>'
            f'<div class="cc-body"><div class="cc-chips"><span class="chip chip-1">{e(c["level"])}</span><span class="chip chip-2">{e(c["category"])}</span></div>'
            f'<h3><a href="{e(c["url"]) if not soon else "#"}">{e(c["title"])}</a></h3><p>{e(c["description"])}</p>'
            f'<div class="cc-meta">{"".join(meta)}</div>'
            f'<div class="cc-prog" hidden><div class="cc-prog-bar"><i></i></div><span></span></div>'
            f'<div class="cc-foot">{action}</div></div></div>'
        )

    path = "".join(
        f'<li class="{"is-soon" if by_slug[sl]["status"] == "soon" else ""}"><a href="{e(by_slug[sl]["url"])}">{e(by_slug[sl]["title"])}</a></li>'
        for sl in cfg.get("path", []) if sl in by_slug
    )
    newest = sorted([c for c in courses if c.get("updated")], key=lambda c: c["updated"], reverse=True)[:3]
    new_html = "".join(f'<li><a href="{e(c["url"])}">{e(c["title"])}</a><span>{e(c["updated"])}</span></li>' for c in newest)
    help_html = "".join(f'<a href="{e(h["url"])}"><i class="fa-solid {e(h["icon"])}"></i>{e(h["text"])}</a>' for h in cfg.get("help", []))

    html_out = f"""
<div class="cat">
  <div class="cat-filters">
    <div class="cat-search"><i class="fa-solid fa-magnifying-glass"></i><input type="search" id="cat-q" placeholder="Search courses" aria-label="Search courses"></div>
    {facet_html("Level", "level")}
    {facet_html("Category", "category")}
    <div class="cat-group"><h4>Status</h4>{status_rows}</div>
    <button type="button" class="btn-ghost" id="cat-clear">Clear filters</button>
  </div>
  <div class="cat-main">
    <h1 class="cat-title">All Courses</h1>
    <p class="cat-intro">{e(cfg.get("intro", "")).strip()}</p>
    <div class="cat-bar"><span id="cat-count"></span>
      <label>Sort by <select id="cat-sort"><option value="featured">Featured</option><option value="newest">Newest</option><option value="az">A to Z</option></select></label></div>
    <div class="cat-grid">{"".join(cards)}</div>
    <p class="cat-empty" id="cat-empty" hidden>No courses match your filters.</p>
  </div>
  <div class="cat-rail">
    <div class="rail-card" id="cat-continue" hidden><h4><i class="fa-solid fa-play"></i>Continue learning</h4><ul class="cat-list"></ul></div>
    <div class="rail-card"><h4><i class="fa-solid fa-route"></i>Suggested path</h4><ol class="cat-path">{path}</ol></div>
    <div class="rail-card"><h4><i class="fa-solid fa-star"></i>New &amp; updated</h4><ul class="cat-list">{new_html}</ul></div>
    <div class="rail-card cat-help"><h4><i class="fa-solid fa-life-ring"></i>Help</h4>{help_html}</div>
  </div>
</div>
"""
    (GEN / "catalog.md").write_text(fenced(html_out), encoding="utf-8")


STARFIELD = """<!-- Starfield background (option `starfield: true` in _quarto.yml). Generated; do not edit. -->
<script>document.documentElement.classList.add('sm-starfield');</script>
<canvas class="sm-canvas" aria-hidden="true"></canvas>
<script src="https://www.statmania.info/starfield.js" async></script>
"""


def build_starfield(cfg):
    """Always write the include so _quarto.yml can reference it; it is empty when the option is off."""
    on = bool(cfg.get("starfield", False))
    (GEN / "starfield.html").write_text(STARFIELD if on else "<!-- starfield off -->\n", encoding="utf-8")


def main():
    GEN.mkdir(exist_ok=True)
    cfg, modules = load_structure()
    build_starfield(cfg)
    build_module_pages(modules)
    build_home(cfg, modules)
    build_catalog(modules)
    print(f"build.py: {len(modules)} modules, {sum(len(m['lessons']) for m in modules)} lessons", file=sys.stderr)


if __name__ == "__main__":
    main()
