path = '/opt/project-mia/frontend/src/style.css'
with open(path, 'r') as f:
    content = f.read()

# Add viewport-adaptive rules at the end
css_addition = """

/* ── [Adaptive Viewport] 确保内容不被浏览器工具栏裁掉 ── */
html {
  height: -webkit-fill-available;
}
body {
  min-height: 100vh;
  min-height: -webkit-fill-available;
  min-height: 100dvh; /* 动态视口高度，自动扣除浏览器 chrome */
  overflow-x: hidden;
}

/* 页面底部安全间距（用于底部固定导航） */
.page-bottom-safe {
  padding-bottom: calc(4rem + env(safe-area-inset-bottom, 0px));
}

/* 平板浏览器地址栏高度补偿 */
@media (min-width: 2000px) {
  body {
    /* 平板浏览器 chrome 占用约 80~120px，提前预留 */
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }
}
"""

if 'min-height: 100dvh' not in content:
    content = content + css_addition
    with open(path, 'w') as f:
        f.write(content)
    print('style.css FIXED - added viewport adaptive rules')
else:
    print('style.css already has viewport adaptive rules')
