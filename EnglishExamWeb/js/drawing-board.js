/**
 * Drawing Board - 屏幕涂鸦/笔记板
 * 允许用户在界面上进行标注 - Supports Vector Storage & Cloud Sync
 */

const DrawingBoard = {
    canvas: null,
    ctx: null,
    isDrawing: false,
    isVisible: false,

    // 配置
    config: {
        color: '#ff4757', // 默认红色
        lineWidth: 3,
        eraserMode: false,
        eraserSize: 20
    },

    strokes: [], // 存储所有笔画 {points: [], color, size, mode}
    currentStroke: null,
    currentPaperId: 'default', // 当前试卷ID

    lastToggleTime: 0,

    /**
     * 初始化
     */
    init() {
        if (this.canvas) return;

        // 创建 Canvas - 始终可见，不阻挡答题点击
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'drawing-canvas';
        this.canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 999;
            pointer-events: none;
            background: transparent;
            display: block;
        `;
        document.body.appendChild(this.canvas);

        this.ctx = this.canvas.getContext('2d');
        this.resize();
        window.addEventListener('resize', () => this.resize());

        this.bindEvents();
        this.createToolbar();

        // 加载云端笔记
        this.loadFromBackend();

        this.isVisible = true; // Drawing always active

        console.log('[DrawingBoard] 初始化完成 - 绘图模式始终可用');
    },

    /**
     * 创建工具栏
     */
    createToolbar() {
        const toolbar = document.createElement('div');
        toolbar.id = 'drawing-toolbar';
        toolbar.className = 'glass-panel';
        toolbar.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            padding: 10px;
            display: flex;
            gap: 10px;
            border-radius: 12px;
            background: rgba(30, 30, 40, 0.85);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
        `;

        toolbar.innerHTML = `
            <div id="draw-tools" style="display: flex; gap: 8px; align-items: center;">
                <span style="color: #fff; font-size: 0.85rem; opacity: 0.7;">✏️ 绘图</span>
                <input type="color" id="draw-color" value="${this.config.color}" style="width: 30px; height: 30px; border: none; background: none; cursor: pointer;">
                <input type="range" id="draw-size" min="1" max="10" value="${this.config.lineWidth}" style="width: 60px;">
                <button id="draw-eraser" class="btn-icon" title="橡皮擦"><i class="ph-duotone ph-eraser"></i></button>
                <button id="draw-clear" class="btn-icon" title="清空"><i class="ph-duotone ph-trash"></i></button>
            </div>
        `;

        document.body.appendChild(toolbar);

        // 绑定工具栏事件
        document.getElementById('draw-color')?.addEventListener('input', (e) => {
            this.config.color = e.target.value;
            this.config.eraserMode = false;
            this.updateCursor();
        });
        document.getElementById('draw-size')?.addEventListener('input', (e) => {
            this.config.lineWidth = e.target.value;
        });
        document.getElementById('draw-eraser')?.addEventListener('click', () => {
            this.config.eraserMode = !this.config.eraserMode;
            document.getElementById('draw-eraser').classList.toggle('active', this.config.eraserMode);
            this.updateCursor();
        });
        document.getElementById('draw-clear')?.addEventListener('click', () => {
            if (confirm('确定要清空所有笔记吗？')) this.clear();
        });
    },

    // Removed toggle function - drawing is always available
    /**
     * 切换绘画模式 (已移除 - 绘图始终可用)
     */

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.redraw(); // 重绘
    },

    redraw() {
        if (!this.ctx) return;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.strokes.forEach(stroke => {
            this.drawStroke(stroke);
        });
    },

    drawStroke(stroke) {
        if (stroke.points.length < 2) return;

        this.ctx.beginPath();
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        if (stroke.mode === 'eraser') {
            this.ctx.globalCompositeOperation = 'destination-out';
            this.ctx.lineWidth = stroke.size;
        } else {
            this.ctx.globalCompositeOperation = 'source-over';
            this.ctx.strokeStyle = stroke.color;
            this.ctx.lineWidth = stroke.size;
        }

        this.ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
        for (let i = 1; i < stroke.points.length; i++) {
            this.ctx.lineTo(stroke.points[i].x, stroke.points[i].y);
        }
        this.ctx.stroke();
    },

    bindEvents() {
        const start = (e) => {
            // Always allow drawing, temporarily enable pointer events
            this.canvas.style.pointerEvents = 'auto';
            this.isDrawing = true;
            const { x, y } = this.getPos(e);

            // 开始新笔画
            this.currentStroke = {
                points: [{ x, y }],
                color: this.config.color,
                size: this.config.lineWidth,
                mode: this.config.eraserMode ? 'eraser' : 'draw'
            };

            // 实时绘制
            this.ctx.beginPath();
            this.ctx.moveTo(x, y);
            e.preventDefault();
        };

        const move = (e) => {
            if (!this.isDrawing) return;
            const { x, y } = this.getPos(e);

            // 记录点
            this.currentStroke.points.push({ x, y });

            // 实时绘制
            this.ctx.lineCap = 'round';
            this.ctx.lineJoin = 'round';
            if (this.config.eraserMode) {
                this.ctx.globalCompositeOperation = 'destination-out';
                this.ctx.lineWidth = this.config.eraserSize;
            } else {
                this.ctx.globalCompositeOperation = 'source-over';
                this.ctx.strokeStyle = this.config.color;
                this.ctx.lineWidth = this.config.lineWidth;
            }
            this.ctx.lineTo(x, y);
            this.ctx.stroke();
            e.preventDefault();
        };

        const end = () => {
            if (this.isDrawing && this.currentStroke) {
                this.isDrawing = false;
                this.strokes.push(this.currentStroke);
                this.currentStroke = null;
                this.saveToBackend(); // 自动保存

                // Disable pointer events after drawing to allow clicking
                this.canvas.style.pointerEvents = 'none';
            }
        };

        this.canvas.addEventListener('mousedown', start);
        this.canvas.addEventListener('mousemove', move);
        this.canvas.addEventListener('mouseup', end);
        this.canvas.addEventListener('mouseout', end);
        this.canvas.addEventListener('touchstart', start, { passive: false });
        this.canvas.addEventListener('touchmove', move, { passive: false });
        this.canvas.addEventListener('touchend', end);
    },

    getPos(e) {
        if (e.touches && e.touches.length > 0) {
            return { x: e.touches[0].clientX, y: e.touches[0].clientY };
        }
        return { x: e.clientX, y: e.clientY };
    },

    clear() {
        this.strokes = [];
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.saveToBackend();
    },

    updateCursor() {
        const canvas = this.canvas;
        if (!canvas) return;
        if (this.config.eraserMode) {
            canvas.style.cursor = 'crosshair';
        } else {
            canvas.style.cursor = 'default';
        }
    },

    async saveToBackend() {
        try {
            await fetch('/api/save_drawing', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    paper_id: this.currentPaperId,
                    strokes: this.strokes
                })
            });
        } catch (e) {
            console.error('Failed to save drawing:', e);
        }
    },

    async loadFromBackend() {
        try {
            const res = await fetch('/api/get_drawing', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ paper_id: this.currentPaperId })
            });
            const data = await res.json();
            if (data.success && data.strokes) {
                this.strokes = data.strokes;
                this.redraw();
            }
        } catch (e) {
            console.error('Failed to load drawing:', e);
        }
    }
};

window.DrawingBoard = DrawingBoard;
