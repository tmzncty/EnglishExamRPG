/**
 * 通知管理模块
 */

export class NotificationManager {
    constructor() {
        this.permission = Notification.permission;
    }

    /**
     * 请求通知权限
     */
    async requestPermission() {
        if (!('Notification' in window)) {
            console.warn('浏览器不支持通知功能');
            return false;
        }

        if (this.permission === 'granted') {
            return true;
        }

        const permission = await Notification.requestPermission();
        this.permission = permission;
        return permission === 'granted';
    }

    /**
     * 发送通知
     */
    sendNotification(title, options = {}) {
        if (this.permission !== 'granted') {
            console.warn('没有通知权限');
            return;
        }

        const defaultOptions = {
            icon: '📚',
            badge: '📖',
            vibrate: [200, 100, 200],
            requireInteraction: false,
            ...options
        };

        const notification = new Notification(title, defaultOptions);

        notification.onclick = () => {
            window.focus();
            notification.close();
        };

        return notification;
    }

    /**
     * 发送学习提醒
     */
    sendLearningReminder(dueWords) {
        const title = '📚 该学习啦！';
        const body = dueWords > 0 
            ? `你有 ${dueWords} 个单词等待复习哦~`
            : '今天还没有学习新单词呢！';

        this.sendNotification(title, {
            body,
            tag: 'learning-reminder',
            requireInteraction: true
        });
    }

    /**
     * 发送学习完成通知
     */
    sendCompletionNotification(stats) {
        const title = '🎉 今日学习完成！';
        const body = `学习了 ${stats.learnedToday} 个新词，复习了 ${stats.reviewedToday} 个单词。正确率：${stats.accuracy}%！`;

        this.sendNotification(title, {
            body,
            tag: 'completion',
            requireInteraction: false
        });
    }

    /**
     * 发送鼓励通知
     */
    sendEncouragementNotification() {
        const messages = [
            '加油！每天进步一点点 💪',
            '坚持就是胜利！你真棒 ✨',
            '学习使我快乐！继续努力 🌟',
            '词汇量+1！你越来越强了 🚀',
            '太棒了！保持这个节奏 🎯'
        ];

        const randomMessage = messages[Math.floor(Math.random() * messages.length)];

        this.sendNotification('💝 加油鼓励', {
            body: randomMessage,
            tag: 'encouragement'
        });
    }

    /**
     * 设置定时提醒
     */
    scheduleReminder(time, dueWords) {
        const [hours, minutes] = time.split(':').map(Number);
        const now = new Date();
        const scheduledTime = new Date();
        scheduledTime.setHours(hours, minutes, 0, 0);

        // 如果时间已过，设置为明天
        if (scheduledTime <= now) {
            scheduledTime.setDate(scheduledTime.getDate() + 1);
        }

        const delay = scheduledTime.getTime() - now.getTime();

        setTimeout(() => {
            this.sendLearningReminder(dueWords);
            // 设置下一天的提醒
            this.scheduleReminder(time, dueWords);
        }, delay);
    }

    /**
     * 检查并发送每日提醒
     */
    checkDailyReminder(settings, dueWords) {
        const enabled = settings.notificationEnabled === 'true';
        if (!enabled) return;

        const notificationTime = settings.notificationTime || '20:00';
        this.scheduleReminder(notificationTime, dueWords);
    }
}

export const notificationManager = new NotificationManager();
