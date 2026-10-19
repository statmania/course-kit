# Course template

A self-explanatory Quarto course template (the course *is* the documentation).
Render it and read it from the home page.

```bash
quarto preview     # live preview (runs scripts/build.py first)
quarto render      # build the site into this folder
```

## Start a new course
1. Copy this folder to `../<slug>`; delete `index.html`, `modules/**/*.html`, `site_libs/`, `.quarto/`.
2. Edit the `index.qmd` front matter (title, description, `course:` block).
3. Edit the sidebar in `_quarto.yml`: it defines modules and lesson order.
4. Replace the lessons under `modules/`. Each needs `title`, `description`, `minutes`, `kind`.
5. Run `python3 scripts/build.py` once (Quarto reads `_generated/` before the pre-render
   step on a brand-new course), then `quarto render`.

Requires Quarto 1.4+ and Python 3 with PyYAML. For live R, see the "Code blocks" lesson.

## Logo
The navbar logo is `img/statmania_logo.svg`. Replace it, or change `website.navbar.logo` /
`logo-href` in `_quarto.yml`. Full instructions are in the "Theming" lesson.
