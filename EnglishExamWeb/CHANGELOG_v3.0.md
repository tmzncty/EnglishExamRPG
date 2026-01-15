# English Exam RPG - v3.0 Release Notes

## 🎉 v3.0: AI Galgame Story System & Core UX Improvements

**Release Date**: 2026-01-15  
**Type**: Major Update

---

## 📋 What's New

### 🎭 AI-Powered Galgame Story System (主要特性)

完整的Galgame式剧情系统，让Mia猫娘真正陪伴你学习！

**核心功能**：
- **上下文感知剧情生成**: 基于完整题目内容（文章+选项+题型）生成剧情
- **双语支持**: 中英文双语剧情
  - 英文：VectorEngine Gemini API (`gemini-3-flash-preview`)
  - 中文：DeepSeek-V3.2 翻译，保留傲娇语气和颜文字
- **角色一致性**: Mia傲娇猫娘人设，外冷内热，关心但嘴硬
- **剧情质量**: 120-150字详细对话，包含具体题目分析
- **数据库存储**: SQLite数据库缓存预生成剧情
- **优雅降级**: 数据库缺失时自动使用静态fallback剧情

**示例剧情**：
```
哼...这种车间照明条件当然会影响工作效率啦！(｡•́︿•̀｡)  
你、你该不会连这种基础常识都不知道吧喵？
（转头小声）要是有人在这种昏暗环境里受伤的话...我才不会担心呢！(๑´ㅂ`๑)
```

**技术实现**：
- 新增文件：`js/story-service.js` - 剧情获取服务
- 新增API：`POST /api/get_story` - 服务器端点
- 数据库：`story_content.db` - SQLite存储
- 生成脚本：
  - `gen_final.py` - 使用Gemini生成英文剧情
  - `translate_stories.py` - DeepSeek翻译为中文
- 集成：修改`UIEffects.handleStoryFeedback()`使用数据库剧情

---

### 🎲 Section-Based Question Shuffling

**问题**: 之前题目按个别打乱，导致Part A/B/C被拆散

**解决方案**: 
- 修改 `loadExamData()` 逻辑
- 现在按**整个section**打乱，保持Part内部题目顺序
- 例如：Part A的所有题目保持在一起，但Part A整体可能出现在Part B之前

**代码变更** (`js/app.js`):
```javascript
// 之前：打乱individual questions
this.shuffleArray(this.allQuestions);

// 现在：打乱complete sections
const allSections = [];  // 收集完整sections
examData.sections.forEach(section => {
    allSections.push({
        year: year,
        sectionInfo: section.section_info,
        questions: [...section.questions]  // 保持内部顺序
    });
});

this.shuffleArray(allSections);  // 打乱sections
allSections.forEach(sec => {
    this.allQuestions.push(...sec.questions);  // 展开
});
```

---

### ✏️ Integrated Drawing Mode (去除模式切换)

**问题**: 之前需要按P键切换"绘图模式"和"答题模式"

**解决方案**:
- 移除切换按钮和快捷键
- Canvas始终显示
- **智能pointer-events**: 
  - 默认：`pointer-events: none` (允许点击答题选项)
  - 绘图时：`pointer-events: auto` (拦截鼠标事件)
  - 绘图结束：恢复`pointer-events: none`

**代码变更** (`js/drawing-board.js`):
```javascript
// 移除前：需要toggle()切换模式
// 移除后：绘图工具始终显示

// Canvas初始化
this.canvas.style.display = 'block';  // 之前：'none'
this.canvas.style.pointerEvents = 'none';  // 默认不拦截

// 绘图开始
const start = (e) => {
    this.canvas.style.pointerEvents = 'auto';  // 临时启用
    this.isDrawing = true;
    ...
};

// 绘图结束  
const end = () => {
    ...
    this.canvas.style.pointerEvents = 'none';  // 恢复禁用
};
```

**用户体验**: 可以边做题边画图标记，无需切换模式

---

### 🖱️ Fixed Dialog Dragging Bug

**问题**: 拖拽对话框时会自动跳到屏幕顶部

**根本原因**: 每次`mousedown`时重置`initialX/Y`，没有累积之前的偏移量

**解决方案**: 
- 新增`currentX/Y`变量存储累积偏移
- `mousedown`时计算相对于当前位置的初始值

**代码变更** (`js/ui-effects.js`):
```javascript
// 修复前
let initialX = e.clientX;  // 每次重置
let initialY = e.clientY;

// 修复后
let currentX = 0, currentY = 0;  // 累积偏移
let initialX, initialY;

handle.addEventListener('mousedown', (e) => {
    initialX = e.clientX - currentX;  // 考虑之前位置
    initialY = e.clientY - currentY;
});

document.addEventListener('mousemove', (e) => {
    currentX = e.clientX - initialX;  // 更新累积值
    currentY = e.clientY - initialY;
    overlay.style.transform = `translate(${currentX}px, ${currentY}px)`;
});
```

---

## 🔧 Technical Changes

### Modified Files

| File                  | Changes                             | Lines        |
| --------------------- | ----------------------------------- | ------------ |
| `js/app.js`           | Section shuffle logic               | ~60 modified |
| `js/drawing-board.js` | Integrated mode, removed toggle     | ~80 modified |
| `js/ui-effects.js`    | Dialog drag fix + story integration | ~40 modified |
| `js/story-service.js` | **NEW** - Story fetching service    | ~50 new      |
| `server.py`           | **NEW** API `/api/get_story`        | ~35 new      |
| `index.html`          | Script imports updated              | ~2 modified  |
| `css/theme-acg.css`   | Bug fixes (corrupted encoding)      | ~100 fixed   |

### New Dependencies

- **VectorEngine Gemini API**: `gemini-3-flash-preview` model
- **DeepSeek-V3.2**: Translation API
- **SQLite Database**: `story_content.db` for story storage

### Database Schema

```sql
CREATE TABLE stories (
    q_id INT,
    year INT,
    section_type TEXT,
    correct_cn TEXT,  -- 中文答对剧情
    wrong_cn TEXT,    -- 中文答错剧情
    correct_en TEXT,  -- 英文答对剧情
    wrong_en TEXT,    -- 英文答错剧情
    PRIMARY KEY(q_id, year)
);
```

### API Endpoints

**New**: `POST /api/get_story`

Request:
```json
{
    "q_id": 1,
    "year": 2010,
    "is_correct": true,
    "lang": "cn"
}
```

Response:
```json
{
    "success": true,
    "story": "哼...这种车间照明条件当然会影响工作效率啦！..."
}
```

---

## 🧪 Testing & Validation

### AI Story Generation
- ✅ VectorEngine Gemini API连通性测试通过
- ✅ 生成2010年题目#1的剧情（中英文）
- ✅ 剧情包含具体内容（霍桑实验、照明、生产效率）
- ✅ DeepSeek翻译保留颜文字和傲娇语气

### Frontend Integration  
- ✅ `StoryService.getStory()` 正确从数据库获取
- ✅ Fallback到静态剧情机制工作正常
- ✅ 剧情对话框显示正常

### UX Improvements
- ✅ Section shuffle保持Part完整性
- ✅ 绘图模式无需切换，体验流畅
- ✅ 对话框拖拽稳定，不再跳跃

---

## 📦 Migration Guide

### For Users

1. **更新代码**: `git pull origin main`
2. **重启服务器**: `python server.py`（会自动创建新数据库）
3. **（可选）批量生成剧情**:
   ```bash
   cd EnglishExamWeb
   python gen_final.py  # 生成所有年份的剧情
   ```

### Database

如果数据库不存在，系统会自动使用静态fallback剧情。
要使用AI生成的剧情，需运行生成脚本创建`story_content.db`。

---

## ⚠️ Breaking Changes

**None**. 所有更新向后兼容。

---

## 🐛 Bug Fixes

- Fixed CSS encoding corruption in `theme-acg.css`
- Fixed dialog dragging cumulative offset bug
- Fixed pointer events blocking answer selection in drawing mode

---

## 📊 Statistics

- **Total Commits**: 1 major update
- **Files Changed**: 7 modified, 6 new scripts
- **Lines Added**: ~350
- **Lines Modified**: ~180
- **Database Stories**: 2 questions (demo), expandable to all years

---

## 🔮 Future Roadmap

- [ ] Part completion summary stories
- [ ] Batch generate stories for all years (2010-2024)
- [ ] Language toggle in settings (CN/EN switch)
- [ ] Story caching in localStorage for offline use
- [ ] Custom story editing interface

---

## 👥 Credits

- **AI Story Generation**: VectorEngine Gemini (`gemini-3-flash-preview`)
- **Translation**: DeepSeek-V3.2
- **Character Design**: Mia the Tsundere Cat-Girl
- **Development**: tmzncty

---

**Previous Version**: v2.x (PDF parser + AI cache)  
**Current Version**: v3.0  
**Next Version**: v3.1 (planned: Part summaries)
