# Font Setup Instructions

To fix the Chinese character display issue in the Notepad, you need to provide a font file that supports Chinese characters.

1.  **Find a Font:**
    *   On Windows, go to `C:\Windows\Fonts`.
    *   Find "Microsoft YaHei" (msyh.ttc) or "SimHei" (simhei.ttf).
    *   Copy the file to your desktop.

2.  **Rename and Move:**
    *   Rename the file to `text_font.ttf` (even if it was .ttc, Ren'Py can often handle it, but .ttf is safer. If it's .ttc, rename to `text_font.ttc` and let me know).
    *   Move this file into the `game/fonts` folder. (I have created this folder for you).

3.  **Restart:**
    *   Restart the game. The notepad should now display Chinese characters correctly.
