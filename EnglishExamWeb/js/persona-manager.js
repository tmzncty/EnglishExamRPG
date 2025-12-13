/**
 * Persona Manager - AI 人格切换管理器
 * 管理三种不同的 AI 人格
 */

const PersonaManager = {
    // 后端 API 地址
    API_BASE: 'http://localhost:8000/api',
    
    // 当前人格
    currentPersona: 'normal',
    
    // 人格配置
    personas: {
        normal: {
            id: 'normal',
            name: '学习助手',
            emoji: '📚',
            color: '#3498db',
            description: '专业友善的学习伙伴'
        },
        neko: {
            id: 'neko',
            name: '猫娘学姐',
            emoji: '🐱',
            color: '#e91e63',
            description: '温柔可爱，句尾带"喵～"'
        },
        mesugaki: {
            id: 'mesugaki',
            name: '雌小鬼',
            emoji: '😏',
            color: '#9c27b0',
            description: '高傲毒舌，实力强大'
        }
    },
    
    /**
     * 初始化人格管理器
     */
    async init() {
        console.log('[PersonaManager] 初始化...');
        
        // 获取当前人格
        await this.loadCurrentPersona();
        
        // 创建人格切换UI
        this.createPersonaSwitcher();
        
        // 应用人格主题
        this.applyPersonaTheme();
    },
    
    /**
     * 加载当前人格
     */
    async loadCurrentPersona() {
        try {
            const response = await fetch(`${this.API_BASE}/persona/current`);
            const data = await response.json();
            
            this.currentPersona = data.persona;
            
            console.log(`[PersonaManager] 当前人格: ${data.name} ${data.emoji}`);
            
            return data;
        } catch (error) {
            console.error('[PersonaManager] 加载人格失败:', error);
            return null;
        }
    },
    
    /**
     * 切换人格
     */
    async switchPersona(personaId) {
        if (!this.personas[personaId]) {
            console.error('[PersonaManager] 无效的人格ID:', personaId);
            return false;
        }
        
        try {
            const response = await fetch(`${this.API_BASE}/persona/switch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    key: 'persona',
                    value: personaId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentPersona = personaId;
                
                // 应用新主题
                this.applyPersonaTheme();
                
                // 显示切换消息
                UIEffects.showToast(data.message, 'success');
                
                console.log(`[PersonaManager] 已切换到: ${personaId}`);
                
                return true;
            }
        } catch (error) {
            console.error('[PersonaManager] 切换人格失败:', error);
            UIEffects.showToast('切换失败，请检查后端服务', 'error');
            return false;
        }
    },
    
    /**
     * 创建人格切换UI
     */
    createPersonaSwitcher() {
        // 检查是否已存在
        if (document.getElementById('persona-switcher')) {
            return;
        }
        
        // 创建切换器容器
        const switcher = document.createElement('div');
        switcher.id = 'persona-switcher';
        switcher.className = 'persona-switcher';
        
        switcher.innerHTML = `
            <button class="persona-toggle" title="切换 AI 人格">
                <span class="persona-emoji">${this.personas[this.currentPersona].emoji}</span>
            </button>
            <div class="persona-menu" style="display: none;">
                <div class="persona-menu-header">
                    <h3>选择 AI 人格</h3>
                </div>
                <div class="persona-options">
                    ${this.generatePersonaOptions()}
                </div>
            </div>
        `;
        
        document.body.appendChild(switcher);
        
        // 绑定事件
        const toggle = switcher.querySelector('.persona-toggle');
        const menu = switcher.querySelector('.persona-menu');
        
        toggle.addEventListener('click', () => {
            const isVisible = menu.style.display === 'block';
            menu.style.display = isVisible ? 'none' : 'block';
        });
        
        // 点击外部关闭菜单
        document.addEventListener('click', (e) => {
            if (!switcher.contains(e.target)) {
                menu.style.display = 'none';
            }
        });
        
        // 绑定人格选项点击事件
        const options = switcher.querySelectorAll('.persona-option');
        options.forEach(option => {
            option.addEventListener('click', async () => {
                const personaId = option.dataset.persona;
                const success = await this.switchPersona(personaId);
                
                if (success) {
                    // 更新UI
                    this.updateSwitcherUI();
                    menu.style.display = 'none';
                }
            });
        });
    },
    
    /**
     * 生成人格选项HTML
     */
    generatePersonaOptions() {
        return Object.values(this.personas).map(persona => `
            <div class="persona-option ${persona.id === this.currentPersona ? 'active' : ''}" 
                 data-persona="${persona.id}">
                <span class="persona-emoji">${persona.emoji}</span>
                <div class="persona-info">
                    <strong>${persona.name}</strong>
                    <small>${persona.description}</small>
                </div>
                ${persona.id === this.currentPersona ? '<i class="ph-duotone ph-check"></i>' : ''}
            </div>
        `).join('');
    },
    
    /**
     * 更新切换器UI
     */
    updateSwitcherUI() {
        const switcher = document.getElementById('persona-switcher');
        if (!switcher) return;
        
        // 更新按钮图标
        const toggle = switcher.querySelector('.persona-toggle .persona-emoji');
        if (toggle) {
            toggle.textContent = this.personas[this.currentPersona].emoji;
        }
        
        // 更新选项状态
        const menu = switcher.querySelector('.persona-menu');
        if (menu) {
            menu.innerHTML = `
                <div class="persona-menu-header">
                    <h3>选择 AI 人格</h3>
                </div>
                <div class="persona-options">
                    ${this.generatePersonaOptions()}
                </div>
            `;
            
            // 重新绑定事件
            const options = menu.querySelectorAll('.persona-option');
            options.forEach(option => {
                option.addEventListener('click', async () => {
                    const personaId = option.dataset.persona;
                    const success = await this.switchPersona(personaId);
                    
                    if (success) {
                        this.updateSwitcherUI();
                        menu.style.display = 'none';
                    }
                });
            });
        }
    },
    
    /**
     * 应用人格主题
     */
    applyPersonaTheme() {
        const persona = this.personas[this.currentPersona];
        const root = document.documentElement;
        
        // 设置主题色
        root.style.setProperty('--persona-color', persona.color);
        
        // 更新页面标题（可选）
        const titleElements = document.querySelectorAll('.persona-title');
        titleElements.forEach(el => {
            el.textContent = persona.name;
        });
        
        // 添加人格类名到body
        document.body.classList.remove('persona-normal', 'persona-neko', 'persona-mesugaki');
        document.body.classList.add(`persona-${this.currentPersona}`);
        
        console.log(`[PersonaManager] 已应用 ${persona.name} 主题`);
    },
    
    /**
     * 获取当前人格配置
     */
    getCurrentPersona() {
        return this.personas[this.currentPersona];
    },
    
    /**
     * 获取人格欢迎语
     */
    async getGreeting() {
        try {
            const response = await fetch(`${this.API_BASE}/persona/current`);
            const data = await response.json();
            return data.greeting;
        } catch (error) {
            console.error('[PersonaManager] 获取欢迎语失败:', error);
            return '欢迎回来！';
        }
    },
    
    /**
     * 显示人格介绍
     */
    showPersonaIntro() {
        const persona = this.getCurrentPersona();
        
        const modal = document.createElement('div');
        modal.className = 'modal persona-intro-modal';
        modal.style.display = 'flex';
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${persona.emoji} ${persona.name}</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <p>${persona.description}</p>
                    <div class="persona-preview">
                        <h4>预览风格:</h4>
                        <div class="persona-sample">
                            ${this.getPersonaSample(persona.id)}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 绑定关闭事件
        const closeBtn = modal.querySelector('.modal-close');
        closeBtn.addEventListener('click', () => {
            modal.remove();
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    },
    
    /**
     * 获取人格示例文本
     */
    getPersonaSample(personaId) {
        const samples = {
            normal: `
                <p><strong>正确示例:</strong> "这道题做得很好，继续保持！"</p>
                <p><strong>错误示例:</strong> "这道题有点问题，我们一起看看。"</p>
            `,
            neko: `
                <p><strong>正确示例:</strong> "主人好厉害喵～！(๑˃ᴗ˂)ﻭ"</p>
                <p><strong>错误示例:</strong> "主人别难过喵～ *摸摸头* (っ´ω\`c)"</p>
            `,
            mesugaki: `
                <p><strong>正确示例:</strong> "哼，勉强合格吧...才不是夸你呢！😏"</p>
                <p><strong>错误示例:</strong> "噗哈哈哈！就知道你不行～这么简单都答错了！😂"</p>
            `
        };
        
        return samples[personaId] || samples.normal;
    }
};

// 导出到全局
window.PersonaManager = PersonaManager;
