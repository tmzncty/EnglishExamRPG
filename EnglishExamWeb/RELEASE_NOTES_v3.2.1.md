# Release Notes v3.2.1

**Release Date**: 2026-01-17  
**Type**: Bug Fix Release

## 🐛 Bug Fixes

### Drawing Canvas Issues
- **Fixed**: Drawing canvas not clearing when switching between questions
  - Canvas now properly clears before loading each question's saved drawings
  - Added pre-clear logic in `loadDrawingForQuestion()` to prevent old strokes from persisting
  - Improved `loadFromBackend()` to always initialize strokes array (even if empty)
  
- **Fixed**: Drawing canvas visible on home screen
  - Canvas now automatically hides when navigating away from exam screen
  - Added visibility control in `showScreen()` function
  - Drawing mode automatically disabled when leaving exam screen

### Galgame Dialog Box Enhancements
- **Enhanced**: Dialog box resize functionality
  - Removed `!important` flags from width/height CSS properties to enable native resize
  - Changed `overflow` from `hidden` to `auto` to properly support resize handles
  - Increased max-height from 400px to 600px for better flexibility
  - Users can now freely resize Mia's dialog box by dragging the bottom-right corner

- **Improved**: Dialog box initial state
  - Removed default placeholder text for cleaner appearance
  - Removed unnecessary next indicator arrow
  - Dialog box now starts empty and only shows content when story appears

## 📝 Technical Details

### Modified Files
- `js/drawing-board.js` - Drawing canvas management fixes
- `js/app.js` - Screen switching and canvas visibility control
- `css/theme-acg.css` - Dialog box resize CSS fixes
- `index.html` - Dialog box HTML cleanup
- `js/ui-effects.js` - Removed references to deleted DOM elements

### Testing
All fixes have been tested and confirmed working:
- ✅ Drawing canvas clears correctly when switching questions
- ✅ Canvas hidden on home/vocab screens
- ✅ Dialog box resizable via drag handle
- ✅ No JavaScript console errors

## 🙏 Acknowledgments

Thank you to all users who reported these issues!

---

**Full Changelog**: v3.2...v3.2.1
