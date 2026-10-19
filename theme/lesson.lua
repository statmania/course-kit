-- Renders the lesson header (kind / time chips and the learning objectives
-- box) from front matter. Only runs on pages that declare `minutes`.
local function esc(s)
  return (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"))
end

local icons = { read = "fa-book-open", code = "fa-code", quiz = "fa-circle-question", lab = "fa-flask" }
local labels = { read = "Reading", code = "Code", quiz = "Quiz", lab = "Lab" }

function Pandoc(doc)
  local m = doc.meta
  if not m.minutes then return nil end
  local kind = m.kind and pandoc.utils.stringify(m.kind) or "read"
  if not icons[kind] then kind = "read" end
  local h = {}
  h[#h + 1] = '<div class="lesson-meta">'
  h[#h + 1] = '<span class="lm-chip lm-' .. kind .. '"><i class="fa-solid ' .. icons[kind] .. '"></i> ' .. labels[kind] .. '</span>'
  h[#h + 1] = '<span class="lm-chip"><i class="fa-regular fa-clock"></i> ' .. pandoc.utils.stringify(m.minutes) .. ' min</span>'
  h[#h + 1] = '</div>'
  if m.objectives then
    h[#h + 1] = '<div class="objectives"><p class="objectives-label"><i class="fa-solid fa-bullseye"></i>By the end of this lesson you will</p><ul>'
    for _, o in ipairs(m.objectives) do
      h[#h + 1] = '<li>' .. esc(pandoc.utils.stringify(o)) .. '</li>'
    end
    h[#h + 1] = '</ul></div>'
  end
  -- Right-rail cards (moved into the margin column by theme/scripts.html)
  if m.cheatsheet then
    h[#h + 1] = '<div class="rail-card cheatsheet"><h4><i class="fa-solid fa-rectangle-list"></i>Cheat sheet</h4><dl>'
    for _, row in ipairs(m.cheatsheet) do
      h[#h + 1] = '<div><dt><code>' .. esc(pandoc.utils.stringify(row.code)) .. '</code></dt><dd>' .. esc(pandoc.utils.stringify(row.text)) .. '</dd></div>'
    end
    h[#h + 1] = '</dl></div>'
  end
  if m["rail-links"] then
    h[#h + 1] = '<div class="rail-card resources"><h4><i class="fa-solid fa-link"></i>Resources</h4><ul>'
    for _, r in ipairs(m["rail-links"]) do
      local icon = r.icon and pandoc.utils.stringify(r.icon) or "fa-arrow-up-right-from-square"
      h[#h + 1] = '<li><a href="' .. esc(pandoc.utils.stringify(r.url)) .. '"><i class="fa-solid ' .. esc(icon) .. '"></i>' .. esc(pandoc.utils.stringify(r.title)) .. '</a></li>'
    end
    h[#h + 1] = '</ul></div>'
  end
  table.insert(doc.blocks, 1, pandoc.RawBlock("html", table.concat(h, "\n")))
  return doc
end
