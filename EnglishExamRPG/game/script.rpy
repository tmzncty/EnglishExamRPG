# Define characters
define t = Character("Proctor", color="#c8ffc8")
define narrator = Character(None)

# Define Images
image bg classroom:
    "images/bg_classroom.png"
    size (1920, 1080)

image bg exam_hall:
    "images/bg_exam_hall.png"
    size (1920, 1080)

image teacher neutral:
    "images/teacher_neutral.png"
    zoom 0.7
    yalign 1.0

default notepad_text = ""

# Python block for data loading and logic
init python:
    import json
    import os
    
    # Set the default font for the entire game to the one you provided
    # This ensures Chinese characters show up everywhere (Questions, Options, Notepad)
    style.default.font = "fonts/LXGWWenKaiMono-Medium.ttf"
    style.default.size = 24

    def load_exam_data():
        # Ren'Py file handling
        # renpy.loader.transfn gets the absolute path to a file in the game dir
        file_path = renpy.loader.transfn("exam_data.json")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Load data at initialization
    exam_data = load_exam_data()
    current_year = exam_data["meta"]["year"]
    sections = exam_data["sections"]

# Game Entry Point
label start:
    scene bg classroom
    show teacher neutral at center

    t "Welcome to the [current_year] English Exam RPG!"
    t "I am your instructor today. Don't expect me to go easy on you just because you're cute."
    t "We have {b}[len(sections)]{/b} sections to get through. Let's begin!"

    $ section_index = 0
    
    while section_index < len(sections):
        $ current_section = sections[section_index]
        call process_section(current_section)
        $ section_index += 1

    t "That's it! You survived the exam. Now go review your mistakes!"
    return

# Label to process a single section
label process_section(section):
    $ sec_type = section["section_info"]["type"]
    $ sec_name = section["section_info"]["name"]
    
    t "Next up: [sec_name] ([sec_type])."
    
    # Prepare article text
    $ article_text = ""
    if "article" in section and "paragraphs" in section["article"]:
        $ article_text = "\n\n".join(section["article"]["paragraphs"])

    # Loop through questions
    $ questions = section["questions"]
    $ q_index = 0
    $ total_q = len(questions)
    
    while q_index < len(questions):
        $ q = questions[q_index]
        # Pass article text to the question label
        call ask_question_split(q, article_text, q_index + 1, total_q)
        $ q_index += 1
        
    return

# Label to ask a single question using Split Screen
label ask_question_split(q, article_text, q_idx, q_total):
    $ q_text = q["text"]
    $ q_id = q["id"]
    $ correct_ans = q["correct_answer"]
    $ explanation = q["ai_persona_prompt"]
    $ raw_analysis = q["analysis_raw"]
    
    # Call the split screen
    call screen exam_split_ui(article_text, q, q_idx, q_total)
    $ user_answer = _return
    
    # Hide the exam UI temporarily to show dialogue (or keep it shown if we modify screens)
    # For now, let's hide it to show the teacher sprite/dialogue clearly
    
    if user_answer == "SHOW_ANSWER":
        # For writing/translation
        t "Here is the model answer/translation:"
        "[correct_ans]"
    elif user_answer == correct_ans:
        t "Correct! Not bad."
    else:
        t "Wrong! The correct answer is [correct_ans]."
        
    # Show explanation
    if explanation:
        t "[explanation]"
    elif raw_analysis:
        t "[raw_analysis]"
            
    return

# Screen for multiple choice
screen multiple_choice_question(question_text, options):
    style_prefix "choice"
    
    frame:
        xalign 0.5
        yalign 0.5
        padding (30, 30)
        background "#000000cc" # Darker background for the question box
        
        vbox:
            spacing 20
            
            # Question text
            text question_text:
                size 24 
                xmaximum 800 
                color "#ffffff"
                xalign 0.5
                text_align 0.5
            
            null height 20
            
            # Iterate over options (A, B, C, D)
            for key, value in sorted(options.items()):
                textbutton "[key]. [value]":
                    action Return(key) 
                    xfill True
                    text_xalign 0.0 # Left align text inside button
