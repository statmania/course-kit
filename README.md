# Stat Mania Course Kit

A Quarto template for building a course: a home page, modules, lessons, quizzes, saved progress
and a three-column layout (course tree, lesson, right-hand helpers). The kit is itself a short
course about how to use it, so render it and read it first.

## 1. What you need
- [Quarto](https://quarto.org/docs/get-started/) 1.4 or newer
- Python 3 with PyYAML (`pip install pyyaml`)

## 2. Try it
```bash
quarto preview     # opens the course in your browser and reloads when you save
```
Stop with `Ctrl+C`. To build the finished site into this folder: `quarto render`.

## 3. Start your own course
1. Copy this folder and name it after your course, for example `../my-course`.
2. Delete the built files in the copy (the old site): all `*.html`, `site_libs/`, `.quarto/`, `search.json`, `sitemap.xml`, `robots.txt`.
3. Open `index.qmd` and change the title, description and the `course:` block
   (level, outcomes, requirements, instructor).
4. Open `_quarto.yml`. The `sidebar:` list is your table of contents. Rename modules, add or
   remove lessons, and reorder lines to reorder the course.
5. Write your lessons in `modules/<module>/<lesson>.qmd`. Copy an existing lesson as a start.
6. Run `python3 scripts/build.py`, then `quarto preview`.
   (Step 6 is only needed the first time. After that, preview and render do it for you.)

## 4. Write a lesson
Every lesson starts with a few lines of front matter. The header, objectives and the
right-hand cards are generated from it:

```yaml
---
title: "My lesson"
description: "One sentence for the home page."
minutes: 8                  # required: turns on the lesson header
kind: read                  # read | code | quiz | lab
objectives:
  - "What the learner will be able to do"
cheatsheet:                 # optional quick-reference card (plain text only)
  - { code: "x", text: "What it means" }
rail-links:                 # optional link card
  - { title: "Docs", url: "https://example.com", icon: "fa-book" }
---
```

Useful blocks inside a lesson:

| Want | Write |
|---|---|
| Summary box (goes in the right column) | `::: {.takeaways}` with a bullet list, closed by `:::` |
| Glossary or aside (goes in the right column) | `::: {.column-margin}` ... `:::` |
| Callout | `::: {.callout-tip}` ... `:::` (note, tip, important, warning, caution) |
| Tabs | `::: {.panel-tabset}` with a `## Heading` per tab |
| Quiz | copy the `sm-quiz` HTML from the "Components" lesson |

The "Writing Lessons" module in the course shows each of these working.

## 5. Make it yours
- **Logo:** replace `img/statmania_logo.svg`, or change `navbar.logo` in `_quarto.yml`.
- **Colours:** edit the `$sm-*` variables at the top of `theme/course.scss`.
- **Footer links and social icons:** edit `theme/footer.html` (social links are `#` placeholders).
- **Site title and link:** `website.title` and `site-url` in `_quarto.yml`.

## 6. Things to know
- Never edit the built `.html` files; edit the `.qmd` sources and re-render.
- Never edit `_generated/`. It is rewritten on every render from `_quarto.yml` and the lessons.
- Do not name a front matter key `resources`; Quarto reserves it (this kit uses `rail-links`).
- Progress, checkmarks and notes are saved in the learner's browser only (no account, no server).
- For live R code, add the quarto-webr extension. The "Code blocks" lesson lists the steps.

## 7. Publish (GitHub Pages)
The built site is committed to the repo, so GitHub Pages can serve it straight from the branch.

1. Set your address in `_quarto.yml`, for example
   `site-url: "https://www.statmania.info/my-course/"`.
2. Build and push:
   ```bash
   quarto render
   git add -A && git commit -m "Update course" && git push
   ```
3. One-time, in the GitHub repo: Settings, Pages, Source: **Deploy from a branch**,
   branch `main`, folder `/ (root)`.

Always run `quarto render` before committing. The site shows what was last rendered, not
what is in the `.qmd` files. The empty `.nojekyll` file must stay: it stops GitHub from
ignoring folders that start with an underscore.
