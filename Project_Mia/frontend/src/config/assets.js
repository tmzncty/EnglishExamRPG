// src/config/assets.js — 统一资源管理入口 (Phase 4.9)

import miaNormal from '../assets/images/mia/normal.jpeg';
import miaHappy from '../assets/images/mia/happy.jpeg';
import miaFocused from '../assets/images/mia/focused.jpeg';
import miaWorried from '../assets/images/mia/worried.jpeg';
import miaExhausted from '../assets/images/mia/exhausted.jpeg';
import miaAvatar from '../assets/images/mia/avatar.jpeg';

export const ASSETS = {
    background: null,   // 白纸模式：不使用背景图
    mia: {
        default: miaNormal,
        happy: miaHappy,
        focused: miaFocused,
        worried: miaWorried,
        exhausted: miaExhausted,
        avatar: miaAvatar,
    }
};
