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
  table.insert(doc.blocks, 1, pandoc.RawBlock("html", table.concat(h, "\n")))
  return doc
end
