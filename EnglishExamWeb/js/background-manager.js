/**
 * Background Manager - 背景管理模块
 * 负责加载和切换背景图片
 */

const BackgroundManager = {
    // 配置
    config: {
        horizontalPath: 'assets/backgrounds/horizontal/',
        verticalPath: 'assets/backgrounds/vertical/',
        defaultBg: 'linear-gradient(135deg, #1a1525 0%, #251d35 100%)'
    },

    // 状态
    backgrounds: {
        horizontal: [],
        vertical: []
    },
    currentBg: null,
    isLoading: false,

    /**
     * 初始化
     */
    async init() {
        await this.loadBackgroundList();
        this.applyRandomBackground();
        this.bindResizeEvent();
        console.log('[BackgroundManager] 初始化完成');
    },

    /**
     * 加载背景列表
     */
    async loadBackgroundList() {
        // 尝试从预定义列表加载
        // 由于纯前端无法直接列出文件夹内容，我们使用预定义列表
        // 用户可以手动更新这个列表，或者使用构建工具自动生成

        try {
            const response = await fetch('assets/backgrounds/backgrounds.json');
            if (response.ok) {
                const data = await response.json();
                this.backgrounds.horizontal = data.horizontal || [];
                this.backgrounds.vertical = data.vertical || [];
                console.log(`[BackgroundManager] 加载了 ${this.backgrounds.horizontal.length} 张横版, ${this.backgrounds.vertical.length} 张竖版背景`);
            }
        } catch (e) {
            console.log('[BackgroundManager] 未找到背景配置文件，使用默认背景');
        }
    },

    /**
     * 获取当前屏幕方向适合的背景列表
     */
    getAppropriateBackgrounds() {
        const isLandscape = window.innerWidth > window.innerHeight;
        const primary = isLandscape ? this.backgrounds.horizontal : this.backgrounds.vertical;
        const fallback = isLandscape ? this.backgrounds.vertical : this.backgrounds.horizontal;
        
        // 优先使用对应方向的背景，没有则使用另一方向的
        return primary.length > 0 ? primary : fallback;
    },

    /**
     * 应用随机背景
     */
    applyRandomBackground() {
        const backgrounds = this.getAppropriateBackgrounds();
        
        if (backgrounds.length === 0) {
            // 没有自定义背景，使用默认渐变
            document.body.style.background = this.config.defaultBg;
            return;
        }

        // 随机选择一张
        const randomIndex = Math.floor(Math.random() * backgrounds.length);
        const bgPath = backgrounds[randomIndex];
        const isLandscape = window.innerWidth > window.innerHeight;
        const folder = isLandscape ? this.config.horizontalPath : this.config.verticalPath;

        this.applyBackground(folder + bgPath);
    },

    /**
     * 应用指定背景
     */
    applyBackground(path) {
        this.currentBg = path;
        document.body.style.background = `url('${path}') no-repeat center center fixed`;
        document.body.style.backgroundSize = 'cover';
        
        // 添加半透明遮罩以保证可读性
        this.ensureOverlay();
    },

    /**
     * 确保有遮罩层
     */
    ensureOverlay() {
        let overlay = document.getElementById('bg-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'bg-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(26, 21, 37, 0.7);
                pointer-events: none;
                z-index: -1;
            `;
            document.body.appendChild(overlay);
        }
    },

    /**
     * 切换到下一张背景
     */
    nextBackground() {
        const backgrounds = this.getAppropriateBackgrounds();
        if (backgrounds.length === 0) return;

        const isLandscape = window.innerWidth > window.innerHeight;
        const folder = isLandscape ? this.config.horizontalPath : this.config.verticalPath;
        
        // 找到当前背景的索引
        let currentIndex = -1;
        if (this.currentBg) {
            const currentFile = this.currentBg.split('/').pop();
            currentIndex = backgrounds.indexOf(currentFile);
        }

        // 切换到下一张
        const nextIndex = (currentIndex + 1) % backgrounds.length;
        this.applyBackground(folder + backgrounds[nextIndex]);
    },

    /**
     * 绑定窗口大小变化事件
     */
    bindResizeEvent() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                // 屏幕方向变化时重新选择合适的背景
                this.applyRandomBackground();
            }, 500);
        });
    },

    /**
     * 重置为默认背景
     */
    resetToDefault() {
        this.currentBg = null;
        document.body.style.background = this.config.defaultBg;
        const overlay = document.getElementById('bg-overlay');
        if (overlay) overlay.remove();
    }
};

// 页面加载时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => BackgroundManager.init());
} else {
    BackgroundManager.init();
}
