# Asset Requirements List

You can generate these assets yourself. Please ensure the filenames match exactly so the game code can find them.

## 1. Character Sprite (The "Proctor")

Since you have a specific image you want to use (the cat-ear girl), just rename it to the following:

| Filename | Description | Resolution (Approx) |
| :--- | :--- | :--- |
| `teacher_neutral.png` | The main sprite for the character. | ~1000px height (e.g., 600x1000) |

*Note: If you have variations (angry, happy), name them `teacher_angry.png`, etc., and let me know so I can add them.*

## 2. Backgrounds

These should be **1920x1080** (16:9 aspect ratio). 2K (2560x1440) is also fine, Ren'Py will scale them down, but 1080p is standard.

| Filename | Description | Prompt Idea |
| :--- | :--- | :--- |
| `bg_classroom.png` | The main classroom setting for the intro. | `anime classroom background, empty, wooden desks, sunlight, visual novel style --ar 16:9` |
| `bg_exam_hall.png` | The large hall where the exam takes place. | `anime exam hall, gymnasium, many desks, serious atmosphere, clock on wall --ar 16:9` |

## 3. UI Elements

| Filename | Description | Resolution |
| :--- | :--- | :--- |
| `notepad_bg.png` | The texture for the notepad overlay. | Square or Portrait (e.g., 500x500 or 400x500). Use the crumpled paper texture you found. |

---

## Layout Visualization (ASCII)

Here is how the Split Screen Exam UI is laid out:

```text
+--------------------------------------------------+----------------------------------+
|  LEFT SIDE (60% Width)                           |  RIGHT SIDE (40% Width)          |
|  Background: Paper Color (#ecf0f1)               |  Background: Dark Blue (#34495e) |
|                                                  |                                  |
|  +--------------------------------------------+  |  +----------------------------+  |
|  |  SCROLLABLE VIEWPORT (Article Text)        |  |  | Question 1 / 10            |  |
|  |                                            |  |  | [Notepad Button]           |  |
|  |  "The history of the English language..."  |  |  +----------------------------+  |
|  |  "dates back to the 5th century..."        |  |                                  |
|  |  "when Germanic tribes arrived..."         |  |  +----------------------------+  |
|  |  [More text...]                            |  |  | Question Text Area         |  |
|  |                                            |  |  | "What century did..."      |  |
|  |                                            |  |  +----------------------------+  |
|  |                                            |  |                                  |
|  |                                            |  |  +----------------------------+  |
|  |                                            |  |  | [ Option A ]               |  |
|  |                                            |  |  | [ Option B ]               |  |
|  |                                            |  |  | [ Option C ]               |  |
|  |                                            |  |  | [ Option D ]               |  |
|  |                                            |  |  +----------------------------+  |
|  +--------------------------------------------+  |                                  |
+--------------------------------------------------+----------------------------------+
```

**Notepad Overlay:**
When you click "Notepad", a small window pops up:
```text
+------------------------------+
| Scratchpad                 X |
| +--------------------------+ |
| | (Paper Texture Bg)       | |
| |                          | |
| | Type notes here...       | |
| |                          | |
| +--------------------------+ |
+------------------------------+
```
