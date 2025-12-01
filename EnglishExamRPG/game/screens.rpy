init offset = -1

screen say(who, what):
    style_prefix "say"

    window:
        id "window"

        if who is not None:

            window:
                id "namebox"
                style "namebox"
                text who id "who"

        text what id "what"

    if not renpy.variant("small"):
        add SideImage() xalign 0.0 yalign 1.0

style window is default
style say_label is default
style say_dialogue is default
style say_thought is default
style namebox is default
style namebox_label is default

style window:
    xalign 0.5
    xfill True
    yalign 1.0
    ysize 185
    background "#00000080"

style say_label:
    color "#c8ffc8"
    xalign 0.0
    yalign 0.5

style say_dialogue:
    color "#ffffff"
    xpos 20
    xsize 1240
    ypos 20

style namebox:
    xpos 20
    ypos -40
    ysize 40

style namebox_label:
    color "#c8ffc8"

screen choice(items):
    style_prefix "choice"

    vbox:
        for i in items:
            textbutton i.caption action i.action

style choice_vbox is vbox
style choice_button is button
style choice_button_text is button_text

style choice_vbox:
    xalign 0.5
    yalign 0.5
    spacing 20

style choice_button is default:
    background "#00000080"
    xsize 800
    padding (20, 20)

style choice_button_text is default:
    color "#ffffff"
    xalign 0.5

init python:
    config.screen_width = 1280
    config.screen_height = 720

# --- EXAM UI SCREENS ---

screen exam_split_ui(article_text, question_data, q_idx, q_total):
    tag exam_ui
    modal True
    
    # Background
    add "#2c3e50" 

    hbox:
        spacing 10
        xfill True
        yfill True

        # LEFT SIDE: Article Text
        frame:
            xsize 0.6
            ysize 1.0
            background "#ecf0f1"
            padding (20, 20)
            
            viewport:
                id "article_vp"
                draggable True
                mousewheel True
                scrollbars "vertical"
                
                vbox:
                    spacing 15
                    text article_text color "#2c3e50" size 24 font "fonts/LXGWWenKaiMono-Medium.ttf"

        # RIGHT SIDE: Question & Interaction
        frame:
            xsize 0.4
            ysize 1.0
            background "#34495e"
            padding (20, 20)
            
            vbox:
                spacing 15
                xfill True
            
                # Header
                hbox:
                    xfill True
                    text "Question [q_idx]/[q_total]" size 28 color "#f1c40f" bold True font "fonts/LXGWWenKaiMono-Medium.ttf"
                    textbutton "Notepad" action Show("notepad_overlay") text_color "#ffffff"

                null height 10
                
                # Question Text Area
                frame:
                    background "#2c3e50"
                    xfill True
                    ysize 200
                    padding (15, 15)

                    viewport:
                        id "question_vp"
                        draggable True
                        mousewheel True
                        scrollbars "vertical"
                        
                        text question_data["text"] size 22 color "#ffffff" font "fonts/LXGWWenKaiMono-Medium.ttf"
                
                null height 15
                
                # Options Area
                frame:
                    background "#2c3e50"
                    xfill True
                    ysize 350
                    padding (10, 10)

                    viewport:
                        draggable True
                        mousewheel True
                        scrollbars "vertical"
                        
                        vbox:
                            spacing 12
                            xfill True
                            
                            if question_data["options"]:
                                for key, val in sorted(question_data["options"].items()):
                                    textbutton "[key]. [val]":
                                        action Return(key)
                                        xfill True
                                        text_color "#ffffff"
                                        text_hover_color "#1abc9c"
                                        text_size 20
                                        text_font "fonts/LXGWWenKaiMono-Medium.ttf"
                            else:
                                text "Please write your answer on paper or in the Notepad." color "#bdc3c7" size 20 font "fonts/LXGWWenKaiMono-Medium.ttf"
                                null height 20
                                textbutton "Show Answer" action Return("SHOW_ANSWER") text_color "#27ae60" text_size 22

# Simple Notepad Overlay
screen notepad_overlay():
    modal False
    drag:
        drag_name "notepad"
        xalign 0.9
        yalign 0.1
        
        frame:
            xsize 400
            ysize 500
            # background "#f1c40f"
            background Frame("images/notepad_bg.png", 10, 10)
            padding (20, 20)
            
            vbox:
                hbox:
                    xfill True
                    text "Scratchpad" color "#000000" bold True
                    textbutton "X" action Hide("notepad_overlay") text_color "#c0392b" xalign 1.0
                
                null height 10
                
                # Note: Ren'Py input is limited, this is a basic implementation
                # A real drawing tool requires CDDs (Creator Defined Displayables)
                text "Type notes here (Press Enter to save):" color "#555555" size 18 font "fonts/LXGWWenKaiMono-Medium.ttf"
                input value VariableInputValue("notepad_text") color "#000000" size 20 pixel_width 380 font "fonts/LXGWWenKaiMono-Medium.ttf"
