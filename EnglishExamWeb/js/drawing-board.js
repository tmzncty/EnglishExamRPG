/**
 * Drawing Board - 屏幕涂鸦/笔记板
 * 允许用户在界面上进行标注 - Supports Vector Storage & Cloud Sync
 */

const DrawingBoard = {
    canvas: null,
    ctx: null,
    isDrawing: false,
    isVisible: false,
    drawModeActive: false, // Whether drawing is currently enabled

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
        window.addEventListener('scroll', () => this.redraw()); // Redraw on scroll to adjust positions


        this.bindEvents();
        this.bindToolbarEvents();

        // 加载云端笔记
        this.loadFromBackend();

        this.isVisible = true; // Drawing always active

        console.log('[DrawingBoard] 初始化完成 - 绘图模式始终可用');
    },

    /**
     * 绑定工具栏事件
     */
    bindToolbarEvents() {
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

        // Toggle draw mode
        document.getElementById('draw-toggle')?.addEventListener('click', () => {
            this.toggleDrawMode();
        });
    },



    // Toggle drawing mode on/off
    toggleDrawMode() {
        this.drawModeActive = !this.drawModeActive;
        const toggleBtn = document.getElementById('draw-toggle');

        if (this.drawModeActive) {
            this.canvas.style.pointerEvents = 'auto';
            this.canvas.style.cursor = 'crosshair';
            if (toggleBtn) {
                toggleBtn.classList.add('active');
            }
            console.log('[DrawingBoard] 绘图模式已开启');
        } else {
            this.canvas.style.pointerEvents = 'none';
            this.canvas.style.cursor = 'default';
            if (toggleBtn) {
                toggleBtn.classList.remove('active');
            }
            console.log('[DrawingBoard] 绘图模式已关闭');
        }
    },
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

        // Apply scroll offset transformation
        // Strokes are stored in absolute document coordinates
        // Translate back to viewport coordinates for rendering
        this.ctx.save();
        this.ctx.translate(-window.scrollX, -window.scrollY);

        this.strokes.forEach(stroke => {
            this.drawStroke(stroke);
        });

        this.ctx.restore();
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
            // Only draw if draw mode is active
            if (!this.drawModeActive) return;
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

                // Don't disable pointer events here, let toggleDrawMode handle it
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
        // Get viewport coordinates
        const clientX = e.touches && e.touches.length > 0 ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches && e.touches.length > 0 ? e.touches[0].clientY : e.clientY;

        // Convert to absolute document coordinates by adding scroll offset
        return {
            x: clientX + window.scrollX,
            y: clientY + window.scrollY
        };
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
            if (data.success) {
                // Always set strokes, even if it's an empty array
                this.strokes = data.strokes || [];
                this.redraw();
            }
        } catch (e) {
            console.error('Failed to load drawing:', e);
            // Ensure strokes is at least an empty array on error
            this.strokes = [];
        }
    },

    /**
     *  Load drawing for a specific question
     */
    async loadDrawingForQuestion(questionId) {
        // Save current drawing before switching
        if (this.currentPaperId && this.strokes.length > 0) {
            await this.saveToBackend();
        }

        // Update paper ID to question-specific
        this.currentPaperId = `q_${questionId}`;

        // CRITICAL FIX: Clear current strokes first to prevent old drawings from persisting
        this.strokes = [];
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Load drawing for this question (if any exists)
        await this.loadFromBackend();

        console.log(`[DrawingBoard] Loaded drawing for question ${questionId}`);
    }
};

window.DrawingBoard = DrawingBoard;
