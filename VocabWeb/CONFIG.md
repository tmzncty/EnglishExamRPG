# VocabWeb 配置文件示例

本系统的配置文件保存在浏览器的 LocalStorage 中，**不会同步到服务器**。

## 为什么配置不同步？

- ✅ **个性化设置**：每个设备可以有不同的学习目标和提醒时间
- ✅ **避免冲突**：手机和电脑的通知设置可能不同
- ✅ **更灵活**：不同设备可以根据使用场景调整配置

## 同步说明

### 📊 会同步到服务器的数据
- ✅ 词汇学习记录
- ✅ 学习进度（复习间隔、重复次数等）
- ✅ 错题本
- ✅ AI 讲解缓存
- ✅ 例句数据

### 🔧 不会同步的数据（仅本地）
- ⚙️ 每日学习目标（`dailyGoal`）
- ⚙️ 睡眠时间（`sleepTime`）
- ⚙️ 通知开关（`notificationEnabled`）
- ⚙️ 通知时间（`notificationTime`）
- ⚙️ Gemini API Key

## 默认配置

```json
{
  "dailyGoal": "20",           // 每日新词数量 (5-100)
  "sleepTime": "23:00",        // 一天结束时间
  "notificationEnabled": "false",  // 是否启用通知
  "notificationTime": "20:00",     // 每日提醒时间
  "geminiApiKey": ""           // AI 讲解 API Key（可选）
}
```

## 如何设置

1. **通过界面设置**（推荐）
   - 点击右上角"⚙️ 设置"按钮
   - 修改配置后自动保存到当前设备

2. **浏览器控制台设置**
   ```javascript
   // 设置每日目标为 50 个单词
   localStorage.setItem('vocab_setting_dailyGoal', '50');
   
   // 设置通知时间为早上 8 点
   localStorage.setItem('vocab_setting_notificationTime', '08:00');
   ```

3. **清除所有配置**
   ```javascript
   // 仅清除配置（保留学习数据）
   ['dailyGoal', 'sleepTime', 'notificationEnabled', 'notificationTime', 'geminiApiKey'].forEach(key => {
       localStorage.removeItem(`vocab_setting_${key}`);
   });
   ```

## 跨设备使用建议

### 电脑配置
```json
{
  "dailyGoal": "50",           // 电脑学习时间长，可以多学
  "notificationEnabled": "true",
  "notificationTime": "20:00"  // 晚上学习
}
```

### 手机配置
```json
{
  "dailyGoal": "20",           // 碎片时间学习
  "notificationEnabled": "true",
  "notificationTime": "12:00"  // 午休时间
}
```

## 数据同步流程

```
电脑学习 50 个单词
   ↓
学习记录保存到服务器
   ↓
手机打开，从服务器加载学习记录
   ↓
手机使用自己的配置（每日 20 个）
   ↓
手机继续学习，进度同步回服务器
   ↓
✨ 学习数据完全同步，但配置各自独立！
```

## 注意事项

1. **Gemini API Key**
   - 每个设备需要单独设置
   - 建议使用相同的 API Key（方便共享缓存）

2. **首次使用**
   - 每个设备首次打开会使用默认配置
   - 建议根据设备类型调整配置

3. **配置丢失**
   - 清除浏览器缓存会丢失配置
   - 但学习数据在服务器上，不会丢失

## 常见问题

**Q: 为什么换了设备配置变了？**  
A: 配置是设备本地的，这是设计如此。学习数据是同步的，配置是独立的。

**Q: 我想在所有设备使用相同配置怎么办？**  
A: 在每个设备上手动设置一次相同的值即可。

**Q: 配置会影响学习进度同步吗？**  
A: 不会！配置只影响当前设备的行为，学习进度完全独立同步。
