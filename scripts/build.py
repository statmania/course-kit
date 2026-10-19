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
        (len(modules), "modules"),
        (len(lessons), "lessons"),
        (hours, "of content"),
        (quizzes, "quiz questions"),
    ]
    stats_html = "".join(f'<div class="stat"><b>{e(n)}</b><span>{e(l)}</span></div>' for n, l in stats)

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


def main():
    GEN.mkdir(exist_ok=True)
    cfg, modules = load_structure()
    build_module_pages(modules)
    build_home(cfg, modules)
    print(f"build.py: {len(modules)} modules, {sum(len(m['lessons']) for m in modules)} lessons", file=sys.stderr)


if __name__ == "__main__":
    main()
