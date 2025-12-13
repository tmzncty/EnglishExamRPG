# 🎉 VocabWeb 使用指南

## 快速开始

### 1. 启动服务器

```bash
# Windows
双击 start.bat

# 或者命令行
cd F:\sanity_check_avg\VocabWeb
python server.py
```

### 2. 访问学习界面

- **电脑**: http://localhost:8080
- **手机**: http://你的电脑IP:8080

---

## 🔧 常见问题解决

### 问题1: 页面一直显示"正在加载"

**原因**: 浏览器缓存损坏

**解决方法**:
1. 访问清除缓存页面: http://localhost:8080/clear.html
2. 点击"清除并重新加载"
3. 或者在浏览器控制台执行:
```javascript
localStorage.clear();
location.reload();
```

### 问题2: 显示"Error: file is not a database"

**原因**: 服务器数据库文件损坏

**解决方法**:
```bash
# 1. 删除损坏的数据库
cd F:\sanity_check_avg\VocabWeb
del user_vocab.db
del user_vocab.db.backup

# 2. 清除浏览器缓存
访问: http://localhost:8080/clear.html

# 3. 刷新页面，系统会自动加载预构建数据库
```

### 问题3: 手机无法访问

**检查清单**:
- ✅ 手机和电脑在同一 Wi-Fi
- ✅ 服务器正在运行（看到 `Running on http://192.168.x.x:8080`）
- ✅ 防火墙允许 8080 端口
- ✅ 使用正确的 IP 地址

**测试连接**:
```
1. 在电脑上查看 IP: ipconfig
2. 在手机浏览器输入: http://你的IP:8080/test.html
3. 如果测试页面能打开，说明连接正常
```

### 问题4: 数据没有同步

**检查步骤**:
1. 查看浏览器控制台是否有错误
2. 确认服务器正在运行
3. 访问 http://localhost:8080/api/status 查看服务器状态
4. 手动触发同步:
```javascript
// 在浏览器控制台执行
db.saveToServer();
```

### 问题5: 配置丢失了

**原因**: 配置保存在 localStorage，清除缓存会丢失

**预防方法**:
1. 记录你的配置
2. 或者在控制台查看当前配置:
```javascript
['dailyGoal', 'sleepTime', 'notificationEnabled', 'notificationTime'].forEach(key => {
    console.log(key, localStorage.getItem(`vocab_setting_${key}`));
});
```

---

## 📊 数据同步说明

### 会同步的数据
- ✅ 学习记录
- ✅ 词汇数据
- ✅ 例句
- ✅ AI讲解缓存
- ✅ 错题本

### 不会同步的数据
- ⚙️ 每日学习目标
- ⚙️ 通知设置
- ⚙️ API Key

详见: [DATA_SYNC.md](DATA_SYNC.md)

---

## 🎯 使用技巧

### 1. 多设备学习流程

```
电脑 (每日目标50个)
  → 学习30个单词
  → 自动同步到服务器 ✅

手机 (每日目标20个)
  → 打开页面，加载服务器数据
  → 看到已学习30个，今日已完成 ✅
  → 可以继续超额学习
```

### 2. 推荐配置

**电脑端**:
- 每日目标: 50 个
- 通知时间: 20:00（晚上学习）

**手机端**:
- 每日目标: 20 个
- 通知时间: 12:00（午休复习）

### 3. 离线使用

```
1. 有网络时：数据自动同步
2. 断网后：使用本地缓存继续学习
3. 联网后：自动同步到服务器
```

### 4. 备份数据

**定期备份服务器数据库**:
```bash
# 备份
copy F:\sanity_check_avg\VocabWeb\user_vocab.db D:\backup\vocab_备份日期.db

# 恢复
copy D:\backup\vocab_备份日期.db F:\sanity_check_avg\VocabWeb\user_vocab.db
```

---

## 🔍 调试工具

### 查看数据库状态
http://localhost:8080/test.html

### 清除缓存
http://localhost:8080/clear.html

### 浏览器控制台命令

```javascript
// 查看数据库大小
console.log('数据库缓存:', (localStorage.getItem('vocabDB')?.length / 1024).toFixed(2), 'KB');

// 查看配置
['dailyGoal', 'sleepTime', 'notificationEnabled', 'notificationTime'].forEach(key => {
    console.log(key, localStorage.getItem(`vocab_setting_${key}`));
});

// 手动保存到服务器
db.saveToServer();

// 手动从服务器加载
location.reload();

// 查看今日统计
db.getTodayStats();

// 查看错题数量
db.getMistakeCount();
```

---

## 📱 手机访问设置

### Android

1. 连接与电脑相同的 Wi-Fi
2. 打开浏览器（推荐 Chrome）
3. 输入地址: `http://192.168.x.x:8080`
4. 添加到主屏幕：
   - Chrome: 菜单 → 添加到主屏幕
   - 像原生应用一样使用

### iOS

1. 连接与电脑相同的 Wi-Fi
2. 打开 Safari
3. 输入地址: `http://192.168.x.x:8080`
4. 添加到主屏幕：
   - 点击分享按钮
   - 添加到主屏幕
   - 全屏显示，更像应用

---

## ⚠️ 注意事项

1. **服务器必须运行**
   - 关闭服务器后，其他设备无法同步
   - 但可以继续使用本地缓存

2. **不要同时在多设备答题**
   - 可能导致数据冲突
   - 建议一个设备学习完再换另一个

3. **定期备份**
   - 虽然有自动保存，但建议定期备份
   - 数据文件: `user_vocab.db`

4. **API Key设置**
   - 每个设备单独设置
   - 建议使用相同的Key共享缓存

---

## 📚 相关文档

- [README.md](README.md) - 项目总览
- [DATA_SYNC.md](DATA_SYNC.md) - 数据同步详解
- [CONFIG.md](CONFIG.md) - 配置说明

---

## 💡 最佳实践

1. **首次使用**
   - 在电脑上打开，系统会加载预构建数据库
   - 配置好学习目标
   - 手机打开时会自动同步

2. **日常学习**
   - 在任何设备打开都能继续上次进度
   - 不用担心数据丢失
   - 随时随地学习

3. **清除缓存前**
   - 确保已同步到服务器
   - 或者保存好配置信息
   - 学习数据在服务器上是安全的

---

## 🎊 享受学习吧！

现在你可以：
- 🏠 在家用电脑深度学习
- 📱 在路上用手机碎片复习
- 💻 在任何地方继续进度
- 🔄 所有数据实时同步

**祝你早日攻克考研英语！喵~ 🐱**
