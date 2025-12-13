# 预构建数据库使用说明

## 概述
为了解决浏览器端导入大量数据时的"Maximum call stack size exceeded"错误，我们现在使用预构建的数据库。

## 文件说明

- `prebuild_database.py` - 预构建数据库的 Python 脚本
- `vocab_prebuilt.db` - SQLite 数据库文件（1.19 MB）
- `data/vocab_prebuilt.txt` - Base64 编码的数据库（1.58 MB）

## 工作流程

1. **构建数据库**（当词汇数据更新时）
   ```bash
   cd VocabWeb
   python prebuild_database.py
   ```

2. **自动加载** - 用户首次访问时：
   - 检查 localStorage 是否有数据库
   - 如果没有，自动从 `data/vocab_prebuilt.txt` 加载
   - 保存到 localStorage 供后续使用

3. **后续访问**：
   - 直接从 localStorage 加载
   - 无需重新下载

## 数据统计

- 总词汇数：6131 个
- 总例句数：1882 条
- 数据库大小：1.19 MB
- Base64 大小：1.58 MB

## 优势

✅ 用户无需手动导入
✅ 首次加载后保存在本地
✅ 避免了大数据导入的栈溢出问题
✅ 更好的用户体验

## 更新词汇数据

如果 `exam_vocabulary.json` 更新了：

1. 运行 `python prebuild_database.py`
2. 提交新的 `data/vocab_prebuilt.txt`
3. 用户清除浏览器缓存后会自动获取新版本

## 技术细节

### 分块编码
为了避免栈溢出，Base64 编码使用 32KB 分块：

```javascript
const chunkSize = 0x8000; // 32KB chunks
const chunks = [];

for (let i = 0; i < data.length; i += chunkSize) {
    const chunk = data.subarray(i, i + chunkSize);
    chunks.push(String.fromCharCode.apply(null, chunk));
}

const binary = chunks.join('');
const base64 = window.btoa(binary);
```

这样可以安全处理大型数据库而不会导致栈溢出。
