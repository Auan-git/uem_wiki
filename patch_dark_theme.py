# -*- coding: utf-8 -*-
"""给未启用暗色主题的页面注入主题变量、切换按钮与脚本。"""
from pathlib import Path
import re

ROOT = Path(__file__).parent

FOUC = """  <script>
    (function () {
      try {
        var saved = localStorage.getItem('uem-theme');
        var dark = saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (dark) document.documentElement.setAttribute('data-theme', 'dark');
      } catch (e) {}
    })();
  </script>
"""

DARK_KIT = r"""
<style id="uem-dark-kit">
:root { color-scheme: light; }
html[data-theme="dark"] { color-scheme: dark; }
html[data-theme="dark"] body {
  background: #12141a !important;
  color: #e8eaef !important;
}
html[data-theme="dark"] .app-nav,
html[data-theme="dark"] .top-bar {
  background: #1a1d26 !important;
  border-bottom-color: #2c313c !important;
  box-shadow: 0 1px 4px rgba(0,0,0,.45) !important;
  color: #e8eaef !important;
}
html[data-theme="dark"] .app-nav .nav-brand,
html[data-theme="dark"] .top-bar .logo-text,
html[data-theme="dark"] .app-nav a,
html[data-theme="dark"] .top-bar .logo-text {
  color: #e8eaef !important;
}
html[data-theme="dark"] .app-nav a { color: #9aa1b0 !important; }
html[data-theme="dark"] .app-nav a:hover,
html[data-theme="dark"] .app-nav a.active { color: #e8eaef !important; }
html[data-theme="dark"] .nav-search,
html[data-theme="dark"] .top-bar .search,
html[data-theme="dark"] input[type="text"],
html[data-theme="dark"] input[type="search"] {
  background: #12141a !important;
  color: #e8eaef !important;
  border-color: #2c313c !important;
}
html[data-theme="dark"] .search-results {
  background: #1c1f28 !important;
  border-color: #2c313c !important;
  box-shadow: 0 4px 12px rgba(0,0,0,.45) !important;
}
html[data-theme="dark"] .search-result-item {
  color: #e8eaef !important;
  border-bottom-color: #2c313c !important;
}
html[data-theme="dark"] .search-result-item:hover,
html[data-theme="dark"] .search-no-result {
  background: #1a1d26 !important;
  color: #9aa1b0 !important;
}
html[data-theme="dark"] .search-result-desc,
html[data-theme="dark"] .search-result-title { color: inherit !important; }
html[data-theme="dark"] .search-result-desc { color: #9aa1b0 !important; }
html[data-theme="dark"] .markdown-section,
html[data-theme="dark"] .wiki-main,
html[data-theme="dark"] .content {
  background: #12141a !important;
  color: #e8eaef !important;
}
html[data-theme="dark"] .markdown-section h1,
html[data-theme="dark"] .markdown-section h2,
html[data-theme="dark"] .markdown-section h3,
html[data-theme="dark"] .markdown-section h4,
html[data-theme="dark"] .markdown-section p,
html[data-theme="dark"] .markdown-section li,
html[data-theme="dark"] .markdown-section td,
html[data-theme="dark"] .markdown-section th,
html[data-theme="dark"] .markdown-section strong {
  color: #e8eaef !important;
}
html[data-theme="dark"] .markdown-section h3,
html[data-theme="dark"] .markdown-section h4,
html[data-theme="dark"] .markdown-section em { color: #c2c7d1 !important; }
html[data-theme="dark"] .markdown-section a { color: #d4a574 !important; }
html[data-theme="dark"] .markdown-section a:hover { color: #e25a3c !important; }
html[data-theme="dark"] .markdown-section blockquote {
  background: #1a2233 !important;
  border-left-color: #9aa1b0 !important;
  color: #c2c7d1 !important;
}
html[data-theme="dark"] .markdown-section table,
html[data-theme="dark"] .markdown-section thead th,
html[data-theme="dark"] .markdown-section tbody td {
  background: #12141a !important;
  color: #e8eaef !important;
  border-color: #2c313c !important;
}
html[data-theme="dark"] .markdown-section thead th { background: #1a1d26 !important; }
html[data-theme="dark"] .markdown-section tbody tr:hover { background: #1a1d26 !important; }
html[data-theme="dark"] .markdown-section code,
html[data-theme="dark"] .markdown-section pre,
html[data-theme="dark"] .markdown-section kbd {
  background: #1a1d26 !important;
  color: #e8eaef !important;
  border-color: #2c313c !important;
}
html[data-theme="dark"] .markdown-section hr { background: #2c313c !important; }
html[data-theme="dark"] .toc-sidebar { background: transparent !important; }
html[data-theme="dark"] .toc-title { color: #e8eaef !important; border-bottom-color: #2c313c !important; }
html[data-theme="dark"] .toc-list a { color: #9aa1b0 !important; }
html[data-theme="dark"] .toc-list a:hover { color: #e8eaef !important; }
html[data-theme="dark"] .toc-list a.active { color: #e25a3c !important; }
html[data-theme="dark"] .twikoo-title { color: #e8eaef !important; }
html[data-theme="dark"] #twikoo-comment { border-top-color: #e8eaef !important; }
html[data-theme="dark"] footer {
  border-top-color: #2c313c !important;
  color: #9aa1b0 !important;
  background: transparent !important;
}
html[data-theme="dark"] .doc-links a {
  background: #1a1d26 !important;
  color: #e8eaef !important;
  border-color: #2c313c !important;
}
html[data-theme="dark"] .doc-links a:hover {
  background: #e8eaef !important;
  color: #12141a !important;
}
/* 首页专用（若存在） */
html[data-theme="dark"] .hero h1,
html[data-theme="dark"] .hero h3,
html[data-theme="dark"] .hero p { color: inherit !important; }
html[data-theme="dark"] .hero h3 { color: #9aa1b0 !important; }
html[data-theme="dark"] .hero p { color: #c2c7d1 !important; }
html[data-theme="dark"] .section-card {
  background: linear-gradient(145deg, #1c1f28 0%, #181b23 100%) !important;
  border-color: #2c313c !important;
  color: #e8eaef !important;
}
html[data-theme="dark"] .section-card:hover {
  border-color: #4a5160 !important;
  box-shadow: 0 8px 24px rgba(0,0,0,.45) !important;
}
html[data-theme="dark"] .section-card h3 { color: #e8eaef !important; }
html[data-theme="dark"] .section-card p { color: #9aa1b0 !important; }
html[data-theme="dark"] .hero-links .primary {
  background: #e25a3c !important;
  color: #fff !important;
}
html[data-theme="dark"] .hero-links .secondary {
  border-color: #2c313c !important;
  color: #c2c7d1 !important;
}
/* 常用链接卡片页可能用到的浅底 */
html[data-theme="dark"] .card,
html[data-theme="dark"] .flip-card,
html[data-theme="dark"] .org-card {
  background: #1c1f28 !important;
  color: #e8eaef !important;
}
html[data-theme="dark"] .wiki-sidebar,
html[data-theme="dark"] .sidebar-toggle,
html[data-theme="dark"] .toc-toggle,
html[data-theme="dark"] .back-to-top {
  background: #0a1f4d !important;
}
.theme-toggle {
  flex-shrink: 0;
  width: 34px; height: 34px; margin-left: 10px;
  border: 1px solid #d4c9b8; border-radius: 999px;
  background: #fff; color: #2c2416;
  cursor: pointer; font-size: 15px; line-height: 1;
  display: inline-flex; align-items: center; justify-content: center;
  vertical-align: middle;
}
html[data-theme="dark"] .theme-toggle {
  background: #12141a; color: #e8eaef; border-color: #2c313c;
}
.theme-toggle:hover { transform: scale(1.05); }
@media print { .theme-toggle { display: none !important; } }
</style>
"""

THEME_JS = r"""
<script>
(function () {
  var root = document.documentElement;
  function isDark() { return root.getAttribute('data-theme') === 'dark'; }
  function apply(theme, save) {
    if (theme === 'dark') root.setAttribute('data-theme', 'dark');
    else root.removeAttribute('data-theme');
    var btn = document.getElementById('themeToggle');
    if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
    if (save) { try { localStorage.setItem('uem-theme', theme); } catch (e) {} }
  }
  function ensureBtn() {
    var btn = document.getElementById('themeToggle');
    if (btn) { btn.onclick = function () { apply(isDark() ? 'light' : 'dark', true); }; return; }
    btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'themeToggle';
    btn.className = 'theme-toggle';
    btn.title = '切换深浅色';
    btn.setAttribute('aria-label', '切换深浅色');
    btn.textContent = isDark() ? '☀️' : '🌙';
    btn.onclick = function () { apply(isDark() ? 'light' : 'dark', true); };
    var nav = document.querySelector('.app-nav') || document.querySelector('.top-bar');
    if (nav) nav.appendChild(btn);
    else if (document.body) document.body.insertBefore(btn, document.body.firstChild);
  }
  apply(isDark() ? 'dark' : 'light', false);
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensureBtn);
  } else {
    ensureBtn();
  }
})();
</script>
"""


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "uem-theme" in text or "themeToggle" in text and "data-theme" in text:
        return False
    if "<html" not in text.lower():
        return False

    # FOUC：插到 </head> 前
    if "</head>" in text:
        text = text.replace("</head>", FOUC + DARK_KIT + "</head>", 1)
    elif "<style" in text:
        text = text.replace("<style", FOUC + DARK_KIT + "<style", 1)
    else:
        text = text.replace("<head>", "<head>" + FOUC + DARK_KIT, 1)

    # JS：插到 </body> 前
    if "</body>" in text:
        text = text.replace("</body>", THEME_JS + "</body>", 1)
    else:
        text += THEME_JS

    path.write_text(text, encoding="utf-8")
    return True


def main():
    skip_parts = {"node_modules", "qa_slides", "ppt_assets", "__pycache__", ".git"}
    patched = []
    for f in ROOT.rglob("*.html"):
        if any(p in f.parts for p in skip_parts):
            continue
        if f.name.startswith("deepseek"):
            continue
        if patch_file(f):
            patched.append(str(f.relative_to(ROOT)))
    print(f"patched {len(patched)} files")
    for p in patched[:20]:
        print(" -", p)
    if len(patched) > 20:
        print(f" ... and {len(patched)-20} more")


if __name__ == "__main__":
    main()
