# -*- coding: utf-8 -*-

__author__ = "Nicholas Murray"

import klibs
from klibs import P
from klibs.KLGraphics import KLDraw as kld # To draw shapes
from klibs.KLUserInterface import any_key, mouse_pos, smart_sleep # So participants can press any key to continue; convert mouse presses to mouse position coordinates
from klibs.KLGraphics import fill, blit, flip # To actually make drawn shapes appear on the screen
from klibs.KLUtilities import deg_to_px # Convert stimulus sizes according to degrees of visual angle
from klibs.KLResponseCollectors import KeyPressResponse # To take in key presses as a response to a trial
from klibs.KLResponseListeners import KeypressListener, BaseResponseListener # To record key press responses at the end of a trial
from klibs.KLConstants import TK_MS, RECT_BOUNDARY # to specify milliseconds as the unit of time to measure response times in, and the rectangle boundary for the line motion rating scale
from klibs.KLEventInterface import TrialEventTicket as ET # to define the events of a trial according to stimulus timings
from klibs.KLKeyMap import KeyMap # To map keys to responses and have them recorded in the database
import sdl2 # To generate keyboard button names upon pressing them as a response
from klibs.KLCommunication import message # To write messages on the screen to participants
from klibs.KLBoundary import RectangleBoundary, BoundaryInspector # To create a boundary within which participants can rate line motion
from klibs.KLEventQueue import pump, flush # Everything below recommended by Austin for drawing rating scale
from klibs.KLBoundary import RectangleBoundary

# Defining some useful constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (45, 45, 45)

class gaze_ilm(klibs.Experiment):

    def setup(self):

        if P.run_practice_blocks:
            self.insert_practice_block(1, trial_counts = P.trials_per_practice_block)

        # Block and trial start messages
        self.practice_block_message = message("Press space to begin the practice trials", "default", blit_txt = False)
        self.block_start_message = message("Press space to begin the experiment", "default", blit_txt = False)
        block_start_message_vertical_offset = deg_to_px(3)
        self.block_start_message_position = (P.screen_c[0], P.screen_c[1]-block_start_message_vertical_offset)
        self.next_block_message = message("You have completed a block of trials! Press space to start the next block", "default", blit_txt = False)
        self.next_trial_message = message("Press space to continue", "default", blit_txt = False)
        next_trial_message_vertical_offset = deg_to_px(3)
        self.next_trial_message_posiition = (P.screen_c[0], P.screen_c[1]-next_trial_message_vertical_offset)

        # Fixation Cross
        crosslinesize = deg_to_px(.57)
        self.horizontal_cross = kld.Line(length = crosslinesize, color = WHITE, thickness = 3)
        self.vertical_cross = kld.Line(length = crosslinesize, color = WHITE, thickness = 3, rotation = 90)

        # X which replaces the fixation cross on exogenous cuing trials
        self.x_cross1 = kld.Line(length = crosslinesize, color = WHITE, thickness = 3, rotation = 45)
        self.x_cross2 = kld.Line(length = crosslinesize, color = WHITE, thickness = 3, rotation = -45)

        # Probe stimuli
        probecirclesize = deg_to_px(.57)
        innercirclesize = deg_to_px(.4)
        probestroke = [1, (0,0,0)]
        probe_horizontal_offset = deg_to_px(2.5)
        probe_vertical_offset = deg_to_px(1.1)
        self.probecircle = kld.Circle(diameter = probecirclesize, stroke = probestroke, fill = WHITE)
        self.innercircle = kld.Circle(diameter = innercirclesize, stroke = probestroke, fill = GREY)
        self.left_probe_position = (P.screen_c[0]-probe_horizontal_offset, P.screen_c[1]-probe_vertical_offset)
        self.right_probe_position = (P.screen_c[0]+probe_horizontal_offset, P.screen_c[1]-probe_vertical_offset)
        
        # Exogenous cue stimuli
        cue_stroke_thickness = 2
        self.cue = kld.Circle(diameter = probecirclesize, stroke = [cue_stroke_thickness, WHITE], fill = WHITE)

        # Gaze cue stimuli
        facecirclesize = deg_to_px(1.14) # Double the size of the fixation cross 
        eyecirclesize = deg_to_px(.29)
        pupilcirclesize = deg_to_px(.07)
        noselength = deg_to_px(.09)
        mouthwidth = deg_to_px(.18)
        self.facecircle = kld.Circle(diameter = facecirclesize, stroke = [1, (0,0,0)], fill = WHITE)
        self.eyecircle = kld.Circle(diameter = eyecirclesize, stroke = [1, (0,0,0)], fill = WHITE)
        self.pupilcircle = kld.Circle(diameter = pupilcirclesize, stroke = [1, (0,0,0)], fill = BLACK)
        self.nose = kld.Line(length = noselength, color = BLACK, thickness = 3)
        self.mouth = kld.Line(length = mouthwidth, color = BLACK, thickness = 3, rotation = 90)
        eye_offset = deg_to_px(.23)
        self.left_eye_position = (P.screen_c[0]-eye_offset, P.screen_c[1]-eye_offset)
        self.right_eye_position = (P.screen_c[0]+eye_offset, P.screen_c[1]-eye_offset)
        mouth_offset = deg_to_px(.26)
        self.mouth_position = (P.screen_c[0], P.screen_c[1]+mouth_offset)
        pupilcue_offset = deg_to_px(.14)
        self.lefteye_left_pupilcue_position = (self.left_eye_position[0]-pupilcue_offset, self.left_eye_position[1])
        self.lefteye_right_pupilcue_position = (self.left_eye_position[0]+pupilcue_offset, self.left_eye_position[1])
        self.righteye_left_pupilcue_position = (self.right_eye_position[0]-pupilcue_offset, self.right_eye_position[1])
        self.righteye_right_pupilcue_position = (self.right_eye_position[0]+pupilcue_offset, self.right_eye_position[1])

        # Detection target stimuli
        targetsize = deg_to_px(.23)
        targetstroke = [1, (0,0,0)]
        self.target = kld.Circle(diameter = targetsize, stroke = targetstroke, fill = WHITE)

        # Static line stimuli
        linelength = deg_to_px(4.43)
        linewidth = deg_to_px(.57)
        self.static_line = kld.Line(length = linelength, color = WHITE, thickness = 3, rotation = 90)
        self.static_line_position = (P.screen_c[0], P.screen_c[1]-probe_vertical_offset)

        # Real line motion stimuli
        linelength_shorterline = deg_to_px(.56) # Length for 260 Hz monitor
        linelength_longerline = deg_to_px(.59)
        linelength = deg_to_px(1.1075) # Length for 120 Hz monitor
        lineoffset_shorterlines = deg_to_px(2.485)
        self.shorter_moving_line = kld.Line(length = linelength_shorterline, color = WHITE, thickness = 3, rotation = 90)
        self.longer_moving_line = kld.Line(length = linelength_longerline, color = WHITE, thickness = 3, rotation = 90)
        self.real_line_1_position = (P.screen_c[0]-deg_to_px(1.94), P.screen_c[1]-probe_vertical_offset)
        self.real_line_2_position = (P.screen_c[0]-deg_to_px(1.39), P.screen_c[1]-probe_vertical_offset)
        self.real_line_3_position = (P.screen_c[0]-deg_to_px(.84), P.screen_c[1]-probe_vertical_offset)
        self.real_line_4_position = (P.screen_c[0]-deg_to_px(.29), P.screen_c[1]-probe_vertical_offset)
        self.real_line_5_position = (P.screen_c[0]+deg_to_px(.26), P.screen_c[1]-probe_vertical_offset)
        self.real_line_6_position = (P.screen_c[0]+deg_to_px(.81), P.screen_c[1]-probe_vertical_offset)
        self.real_line_7_position = (P.screen_c[0]+deg_to_px(1.36), P.screen_c[1]-probe_vertical_offset)
        self.real_line_8_position = (P.screen_c[0]+deg_to_px(1.91), P.screen_c[1]-probe_vertical_offset)

        self.moving_line = kld.Line(length = linelength, color = WHITE, thickness = 3, rotation = 90)
        self.moving_line_1_position = (P.screen_c[0]-deg_to_px(1.66125), P.screen_c[1]-probe_vertical_offset)
        self.moving_line_2_position = (P.screen_c[0]-deg_to_px(.55375), P.screen_c[1]-probe_vertical_offset)
        self.moving_line_3_position = (P.screen_c[0]+deg_to_px(.55375), P.screen_c[1]-probe_vertical_offset)
        self.moving_line_4_position = (P.screen_c[0]+deg_to_px(1.66125), P.screen_c[1]-probe_vertical_offset)

        # Line motion rating scale stimuli
        scale_vertical_offset = deg_to_px(1.1)
        scale_w = deg_to_px(4.30)
        scale_h = deg_to_px(1)
        scale_stroke = [int(scale_h * 0.1), WHITE, klibs.STROKE_INNER]
        self.scale_loc = (P.screen_c[0], P.screen_c[1] + scale_vertical_offset)
        self.scale = kld.Rectangle(scale_w, scale_h, stroke=scale_stroke)
        self.scale_mark = kld.Rectangle(int(scale_h * 0.1), scale_h, fill=BLACK)
        self.scale_bounds = bounds_from_blit(self.scale, self.scale_loc)

        left_right_motion_rating_message_horizontal_offset = deg_to_px(3)
        left_right_motion_rating_message_vertical_offset = deg_to_px(1.1)
        no_motion_rating_message_vertical_offset = deg_to_px(2.2)
        self.motion_rating_message = message("Rate the how much and what direction the line may have moved:")
        self.motion_rating_message_position = (P.screen_c[0], P.screen_c[1])
        self.left_motion_rating_message = message("Left")
        self.left_motion_rating_message_position = (P.screen_c[0]-left_right_motion_rating_message_horizontal_offset, P.screen_c[1]+left_right_motion_rating_message_vertical_offset)
        self.right_motion_rating_message = message("Right")
        self.right_motion_rating_message_position = (P.screen_c[0]+left_right_motion_rating_message_horizontal_offset, P.screen_c[1]+left_right_motion_rating_message_vertical_offset)
        self.no_motion_rating_message = message("No motion")
        self.no_motion_rating_message_position = (P.screen_c[0], P.screen_c[1]+no_motion_rating_message_vertical_offset)
        no_motion_line_length = deg_to_px(1)
        self.no_motion_rating_line = kld.Line(length = no_motion_line_length, color = WHITE, thickness = 3)
        self.scale_listener = ScaleListener(
            self.scale_bounds, loop_callback=self.scale_callback

        )

        self.task_demo()

    def task_demo(self):
        #def show_demo_text(msg, stim_set = []):
         #   msg_x = int(P.screen_x / 2)
          #  msg_y = int(P.screen_y * .5)
           # text = message(msg, "default", blit_txt = False)

           # fill()
            #blit(text, registration = 5, location = (msg_x, msg_y))
            #stim_set
            #flip()

        def show_demo_text(msg):
            message_vertical_offset = deg_to_px(6)
            self.message_position = (P.screen_c[0], P.screen_c[1]-message_vertical_offset)
            text = message(msg, "default", blit_txt = False, align = "center")

            #fill()
            blit(text, registration = 5, location = self.message_position)
            #stim_set
            #flip()

        def generate_stimuli(stimuli_type):
            
            # Valid exo trial
                # Start by fixating
            if stimuli_type == "fixation": 
                # Fixation cross
                blit(self.horizontal_cross, registration = 5, location = P.screen_c)
                blit(self.vertical_cross, registration = 5, location = P.screen_c)

                # Probes
                blit(self.probecircle, registration = 5, location = self.left_probe_position)
                blit(self.probecircle, registration = 5, location = self.right_probe_position)
                blit(self.innercircle, registration = 5, location = self.left_probe_position)
                blit(self.innercircle, registration = 5, location = self.right_probe_position)
                
                # Go to an x-cross 
            if stimuli_type == "x-cross":
                # Fixation cross
                blit(self.x_cross1, registration = 5, location = P.screen_c)
                blit(self.x_cross2, registration = 5, location = P.screen_c)

                # Probes
                blit(self.probecircle, registration = 5, location = self.left_probe_position)
                blit(self.probecircle, registration = 5, location = self.right_probe_position)
                blit(self.innercircle, registration = 5, location = self.left_probe_position)
                blit(self.innercircle, registration = 5, location = self.right_probe_position)

            # Go to a no-pupil gaze face
            if stimuli_type == "no_pupil_gaze_face":
                blit(self.facecircle, registration = 5, location = P.screen_c)
                blit(self.eyecircle, registration = 5, location = self.left_eye_position)
                blit(self.eyecircle, registration = 5, location = self.right_eye_position)
                blit(self.nose, registration = 5, location = P.screen_c)
                blit(self.mouth, registration = 5, location = self.mouth_position)

                # Probes
                blit(self.probecircle, registration = 5, location = self.left_probe_position)
                blit(self.probecircle, registration = 5, location = self.right_probe_position)
                blit(self.innercircle, registration = 5, location = self.left_probe_position)
                blit(self.innercircle, registration = 5, location = self.right_probe_position)

            # Go to a leftwards exogenous cue
            if stimuli_type == "left_exogenous_cue":
                blit(self.x_cross1, registration = 5, location = P.screen_c)
                blit(self.x_cross2, registration = 5, location = P.screen_c)
                blit(self.probecircle, registration = 5, location = self.left_probe_position)
                blit(self.probecircle, registration = 5, location = self.right_probe_position)
                blit(self.innercircle, registration = 5, location = self.left_probe_position)
                blit(self.innercircle, registration = 5, location = self.right_probe_position)

                blit(self.cue, registration = 5, location = self.left_probe_position)

            # Go to a right detection target
            if stimuli_type == "right_detection_target":
                blit(self.x_cross1, registration = 5, location = P.screen_c)
                blit(self.x_cross2, registration = 5, location = P.screen_c)
                blit(self.probecircle, registration = 5, location = self.left_probe_position)
                blit(self.probecircle, registration = 5, location = self.right_probe_position)
                blit(self.innercircle, registration = 5, location = self.left_probe_position)
                blit(self.innercircle, registration = 5, location = self.right_probe_position)

                blit(self.target, registration = 5, location = self.right_probe_position)

            # Go to a right looking gaze face
            if stimuli_type == "right_gaze_face":
                blit(self.facecircle, registration = 5, location = P.screen_c)
                blit(self.eyecircle, registration = 5, location = self.left_eye_position)
                blit(self.eyecircle, registration = 5, location = self.right_eye_position)
                blit(self.pupilcircle, registration = 5, location = self.lefteye_right_pupilcue_position)
                blit(self.pupilcircle, registration = 5, location = self.righteye_right_pupilcue_position)
                blit(self.nose, registration = 5, location = P.screen_c)
                blit(self.mouth, registration = 5, location = self.mouth_position)
                blit(self.probecircle, registration = 5, location = self.left_probe_position)
                blit(self.probecircle, registration = 5, location = self.right_probe_position)
                blit(self.innercircle, registration = 5, location = self.left_probe_position)
                blit(self.innercircle, registration = 5, location = self.right_probe_position)

            # Go to left invalid gaze target
            if stimuli_type == "left_gaze_target":
                blit(self.facecircle, registration = 5, location = P.screen_c)
                blit(self.eyecircle, registration = 5, location = self.left_eye_position)
                blit(self.eyecircle, registration = 5, location = self.right_eye_position)
                blit(self.pupilcircle, registration = 5, location = self.lefteye_right_pupilcue_position)
                blit(self.pupilcircle, registration = 5, location = self.righteye_right_pupilcue_position)
                blit(self.nose, registration = 5, location = P.screen_c)
                blit(self.mouth, registration = 5, location = self.mouth_position)
                blit(self.probecircle, registration = 5, location = self.left_probe_position)
                blit(self.probecircle, registration = 5, location = self.right_probe_position)
                blit(self.innercircle, registration = 5, location = self.left_probe_position)
                blit(self.innercircle, registration = 5, location = self.right_probe_position)

                blit(self.target, registration = 5, location = self.left_probe_position)

            # Go to a right valid gaze target
            if stimuli_type == "right_gaze_target":
                blit(self.facecircle, registration = 5, location = P.screen_c)
                blit(self.eyecircle, registration = 5, location = self.left_eye_position)
                blit(self.eyecircle, registration = 5, location = self.right_eye_position)
                blit(self.pupilcircle, registration = 5, location = self.lefteye_right_pupilcue_position)
                blit(self.pupilcircle, registration = 5, location = self.righteye_right_pupilcue_position)
                blit(self.nose, registration = 5, location = P.screen_c)
                blit(self.mouth, registration = 5, location = self.mouth_position)
                blit(self.probecircle, registration = 5, location = self.left_probe_position)
                blit(self.probecircle, registration = 5, location = self.right_probe_position)
                blit(self.innercircle, registration = 5, location = self.left_probe_position)
                blit(self.innercircle, registration = 5, location = self.right_probe_position)

                blit(self.target, registration = 5, location = self.right_probe_position)

            # Go to a neutral looking gaze face
            if stimuli_type == "neutral_gaze_face":
                blit(self.facecircle, registration = 5, location = P.screen_c)
                blit(self.eyecircle, registration = 5, location = self.left_eye_position)
                blit(self.eyecircle, registration = 5, location = self.right_eye_position)
                blit(self.pupilcircle, registration = 5, location = self.left_eye_position)
                blit(self.pupilcircle, registration = 5, location = self.right_eye_position)
                blit(self.nose, registration = 5, location = P.screen_c)
                blit(self.mouth, registration = 5, location = self.mouth_position)
                blit(self.probecircle, registration = 5, location = self.left_probe_position)
                blit(self.probecircle, registration = 5, location = self.right_probe_position)
                blit(self.innercircle, registration = 5, location = self.left_probe_position)
                blit(self.innercircle, registration = 5, location = self.right_probe_position)

            # Draw a line for an exo trial
            if stimuli_type == "exo_line_draw":
                blit(self.x_cross1, registration = 5, location = P.screen_c)
                blit(self.x_cross2, registration = 5, location = P.screen_c)

                # Probes
                blit(self.probecircle, registration = 5, location = self.left_probe_position)
                blit(self.probecircle, registration = 5, location = self.right_probe_position)
                blit(self.innercircle, registration = 5, location = self.left_probe_position)
                blit(self.innercircle, registration = 5, location = self.right_probe_position)
                
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
                blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)

            # Draw a line for a gaze trial
            if stimuli_type == "right_gaze_line_draw":
                blit(self.facecircle, registration = 5, location = P.screen_c)
                blit(self.eyecircle, registration = 5, location = self.left_eye_position)
                blit(self.eyecircle, registration = 5, location = self.right_eye_position)
                blit(self.pupilcircle, registration = 5, location = self.lefteye_right_pupilcue_position)
                blit(self.pupilcircle, registration = 5, location = self.righteye_right_pupilcue_position)
                blit(self.nose, registration = 5, location = P.screen_c)
                blit(self.mouth, registration = 5, location = self.mouth_position)
                blit(self.probecircle, registration = 5, location = self.left_probe_position)
                blit(self.probecircle, registration = 5, location = self.right_probe_position)
                blit(self.innercircle, registration = 5, location = self.left_probe_position)
                blit(self.innercircle, registration = 5, location = self.right_probe_position)
                
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
                blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
                blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)

            # Draw line rating scale
            if stimuli_type == "line_rating_scale":
                blit(self.motion_rating_message, registration = 5, location = self.motion_rating_message_position)
                blit(self.left_motion_rating_message, registration = 5, location = self.left_motion_rating_message_position)
                blit(self.right_motion_rating_message, registration = 5, location = self.right_motion_rating_message_position)
                blit(self.no_motion_rating_message, registration = 5, location = self.no_motion_rating_message_position)
                blit(self.no_motion_rating_line, registration = 5, location = self.scale_loc)
                blit(self.scale, 5, self.scale_loc)
                # Draw the cue
            # if x_cross == "x-cross" and cue_type == "exogenous" and cue_loc == "left":
            #     # X-cross
            #     fill()
            #     blit(self.x_cross1, registration = 5, location = P.screen_c)
            #     blit(self.x_cross2, registration = 5, location = P.screen_c)

            #     # Probes
            #     blit(self.probecircle, registration = 5, location = self.left_probe_position)
            #     blit(self.probecircle, registration = 5, location = self.right_probe_position)
            #     blit(self.innercircle, registration = 5, location = self.left_probe_position)
            #     blit(self.innercircle, registration = 5, location = self.right_probe_position)
                
            #     # Left exogenous cues
            #     blit(self.cue, registration = 5, location = self.left_probe_position)                
            #     flip()

            #     # Draw the valid target
            # if x_cross == "x-cross" and cue_type == "exogenous" and cue_loc == None and target_loc == "left":
            #     # X-cross
            #     fill()
            #     blit(self.x_cross1, registration = 5, location = P.screen_c)
            #     blit(self.x_cross2, registration = 5, location = P.screen_c)

            #     # Probes
            #     blit(self.probecircle, registration = 5, location = self.left_probe_position)
            #     blit(self.probecircle, registration = 5, location = self.right_probe_position)
            #     blit(self.innercircle, registration = 5, location = self.left_probe_position)
            #     blit(self.innercircle, registration = 5, location = self.right_probe_position)
                
            #      # Right detection target
            #     blit(self.target, registration = 5, location = self.left_probe_position)
            #     flip()
            #     # Subtract the valid target for response
            # if x_cross == "x-cross" and cue_type == "exogenous" and cue_loc == None and target_loc == None:
            #     # X-cross
            #     fill()
            #     blit(self.x_cross1, registration = 5, location = P.screen_c)
            #     blit(self.x_cross2, registration = 5, location = P.screen_c)

            #     # Probes
            #     blit(self.probecircle, registration = 5, location = self.left_probe_position)
            #     blit(self.probecircle, registration = 5, location = self.right_probe_position)
            #     blit(self.innercircle, registration = 5, location = self.left_probe_position)
            #     blit(self.innercircle, registration = 5, location = self.right_probe_position)
            #     flip()

        def demo_message_stimuli(message = "", stimuli_condition = []):
            fill()
            show_demo_text(message)
            generate_stimuli(stimuli_condition)
            flip()
            any_key()

        # Creating the actual demo    
        demo_message_stimuli("Welcome to the experiment! This tutorial will help explain the task. \n (Press space to continue)",
                             "fixation"
                             )
        
        demo_message_stimuli("Every trial begins with what you see below: \n a fixation cross, and two circles. \n (Press space to continue)",
                             "fixation"
                             )
        
        demo_message_stimuli("To begin trials, \n we ask that you fixate your eyes on that central cross, \n and keep fixated there during the entire trial. \n (Press space to continue)",
                             "fixation"
                             )
        
        demo_message_stimuli("With your eyes fixated at centre, \n you will be prompted to press space to start the trial. \n That means you can take a quick break \n between trials if you would like! \n (Press space to continue)",
                             "fixation"
                             )
        
        demo_message_stimuli("Once you press space to start a trial, \n one of two things will happen: \n (Press space to continue)",
                             "fixation"
                             )
        
        demo_message_stimuli("You'll either see an x-appear at the centre, like this: \n (Press space to continue)",
                              "x-cross"
                             )

        demo_message_stimuli("Or a face without pupils, like this: \n (Press space to continue)",
                              "no_pupil_gaze_face"
                             )
        
        demo_message_stimuli("For now, we'll focus on trials where an x appears: \n (Press space to continue)",
                              "x-cross"
                             )

        demo_message_stimuli("After the x, a flash will appear in one or both of the circles: \n (Press space to continue)",
                              "left_exogenous_cue"
                             )
        
        demo_message_stimuli("Then, the flash will disappear, \n and a dot will appear in one of the two circles: \n (Press space to continue)",
                              "right_detection_target"
                             )
        
        demo_message_stimuli("This is where your task comes in: \n If the dot appears on the left, press the 'z' key with your left index finger. \n If the dot appears on the right, press the '/' key with your right index finger. \n (Press space to continue)",
                              "right_detection_target"
                             )

        demo_message_stimuli("During the experiment respond by pressing 'z' or '/' \n as fast as you can after seeing the dot. \n Don't worry, you'll get to practice after this demo! \n (Press space to continue)",
                              "right_detection_target"
                             )
        
        demo_message_stimuli("After each trial, you'll be brought back to this screen, \n and you'll be asked to press space to start new trial. \n (Press space to continue)",
                             "fixation"
                             )

        demo_message_stimuli("Now let's try this with the face. \n Remember, you'll see a face with no pupils appear: \n (Press space to continue)",
                             "no_pupil_gaze_face"
                             )
        
        demo_message_stimuli("Then pupils will appear, \n looking either left, right, or straight ahead: \n (Press space to continue)",
                             "right_gaze_face"
                             )
        
        demo_message_stimuli("Then, the dot will appear on one side. \n As usual, you have to respond as fast as you can \n by pressing 'z' for left, or '/' for right. \n (Press space to continue)",
                             "left_gaze_target"
                             )
        
        demo_message_stimuli("You will have noticed that sometimes the eyes (or the flash) \n can appear on the side opposite the target dot. \n That means the direction of the eyes and \n the location of the flash are not useful for guessing where the target dot will appear. \n (Press space to continue)",
                             "right_gaze_target"
                             )
        
        demo_message_stimuli("So, you just have to respond to wherever the dot appears, \n while keeping your eyes fixated on the centre \n (whether that be the x or the face). \n (Press space to continue)",
                             "neutral_gaze_face"
                             )
        
        demo_message_stimuli("Now, sometimes instead of a dot appearing in one of the circles, \n a line will appear connecting the two dots: \n (Press space to continue)",
                             "exo_line_draw"
                             )
        
        demo_message_stimuli("In these cases, you won't be responding to a dot that appears \n after the flash or the pupils moving. \n (Press space to continue)",
                             "right_gaze_line_draw"
                             )
        
        demo_message_stimuli("Instead, you'll be asked to rate the quality of the line motion: \n (Press space to continue)",
                             "line_rating_scale"
                             )        
        
        demo_message_stimuli("If the line seemed like it was moving when it appeared, \n then you'd click in the rectangle which direction it moved in: left or right? \n (Press space to continue)",
                             "line_rating_scale"
                             )       

        demo_message_stimuli("We ask if the line seemed to move, please respond not just with the direction: \n Depending on how intensely the line seemed to move, \n you can click further left (for stronger leftward motion) \n or further right (for stronger rightward motion) within the rectangle. \n (Press space to continue)",
                             "line_rating_scale"
                             )       
        
        demo_message_stimuli("Of course, if the line seemed to appear all at once (instead of moving), \n you can click the middle of the rectangle to specify 'No motion'. \n (Press space to continue)",
                             "line_rating_scale"
                             )

        demo_message_stimuli("This line rating task will happen less often than the dot target task. \n So, you can assume each trial is probably a dot target task. \n (Press space to continue)",
                             "line_rating_scale"
                             )    
        
        demo_message_stimuli("That's it! \n Remember: for the dot-target task, \n press 'z' if the dot appears on the left, and '/' if it appears on the right. \n For the line rating task, report whether the line moved, \n and if it moved, what direction and how strongly it seemed to move. \n So, you can assume each trial is probably a dot target task. \n (Press space to continue)",
                             )   

        demo_message_stimuli("Next, you will get to practice a bit before doing the experiment. \n If you have any questions, please ask them now. \n And if you have any more questions later, you can stop and ask them at any time. \n (Press space to continue to practice trials)",
                             )     #######################################################################################
        # FUNCTIONS DEFINING THE EXOGENOUS CUING TASK STIMULI
    #######################################################################################

    def trial_start_stimuli(self):
        # Fixation cross
        fill()
        blit(self.horizontal_cross, registration = 5, location = P.screen_c)
        blit(self.vertical_cross, registration = 5, location = P.screen_c)

        # Probes
        blit(self.probecircle, registration = 5, location = self.left_probe_position)
        blit(self.probecircle, registration = 5, location = self.right_probe_position)
        blit(self.innercircle, registration = 5, location = self.left_probe_position)
        blit(self.innercircle, registration = 5, location = self.right_probe_position)
        flip()

    def exo_trial_pre_cue_stimuli(self):

        if self.task_requirement == "detection":
            # X-cross
            fill()
            blit(self.x_cross1, registration = 5, location = P.screen_c)
            blit(self.x_cross2, registration = 5, location = P.screen_c)

            # Probes
            blit(self.probecircle, registration = 5, location = self.left_probe_position)
            blit(self.probecircle, registration = 5, location = self.right_probe_position)
            blit(self.innercircle, registration = 5, location = self.left_probe_position)
            blit(self.innercircle, registration = 5, location = self.right_probe_position)
            flip()
        else:
            # X-cross
            fill()
            blit(self.x_cross1, registration = 5, location = P.screen_c)
            blit(self.x_cross2, registration = 5, location = P.screen_c)

            # Probes
            blit(self.probecircle, registration = 5, location = self.left_probe_position)
            blit(self.probecircle, registration = 5, location = self.right_probe_position)
            blit(self.innercircle, registration = 5, location = self.left_probe_position)
            blit(self.innercircle, registration = 5, location = self.right_probe_position)
            flip()

    def exo_trial_left_cue_stimuli(self):
        # X-cross
        fill()
        blit(self.x_cross1, registration = 5, location = P.screen_c)
        blit(self.x_cross2, registration = 5, location = P.screen_c)

        # Probes
        blit(self.probecircle, registration = 5, location = self.right_probe_position)
        blit(self.innercircle, registration = 5, location = self.left_probe_position)
        blit(self.innercircle, registration = 5, location = self.right_probe_position)

        # Left exogenous cues
        blit(self.cue, registration = 5, location = self.left_probe_position)

        flip()

    def exo_trial_right_cue_stimuli(self):
        # X-cross
        fill()
        blit(self.x_cross1, registration = 5, location = P.screen_c)
        blit(self.x_cross2, registration = 5, location = P.screen_c)

        # Probes
        blit(self.probecircle, registration = 5, location = self.left_probe_position)
        blit(self.innercircle, registration = 5, location = self.left_probe_position)
        blit(self.innercircle, registration = 5, location = self.right_probe_position)

        # Right exogenous cues
        blit(self.cue, registration = 5, location = self.right_probe_position)

        flip()

    def exo_trial_neutral_cue_stimuli(self):
        # X-cross
        fill()
        blit(self.x_cross1, registration = 5, location = P.screen_c)
        blit(self.x_cross2, registration = 5, location = P.screen_c)

        # Probes
        blit(self.innercircle, registration = 5, location = self.left_probe_position)
        blit(self.innercircle, registration = 5, location = self.right_probe_position)

        # Left and right exogenous cue simultaneously (i.e., neutral exogenous cue)
        blit(self.cue, registration = 5, location = self.left_probe_position)
        blit(self.cue, registration = 5, location = self.right_probe_position)

        flip()

    def exo_trial_left_target_stimuli(self):
        # X-cross
        fill()
        blit(self.x_cross1, registration = 5, location = P.screen_c)
        blit(self.x_cross2, registration = 5, location = P.screen_c)

        # Probes
        blit(self.probecircle, registration = 5, location = self.left_probe_position)
        blit(self.probecircle, registration = 5, location = self.right_probe_position)
        blit(self.innercircle, registration = 5, location = self.left_probe_position)
        blit(self.innercircle, registration = 5, location = self.right_probe_position)

        # Left detection target
        blit(self.target, registration = 5, location = self.left_probe_position)
        flip()

    def exo_trial_right_target_stimuli(self):
        # X-cross
        fill()
        blit(self.x_cross1, registration = 5, location = P.screen_c)
        blit(self.x_cross2, registration = 5, location = P.screen_c)

        # Probes
        blit(self.probecircle, registration = 5, location = self.left_probe_position)
        blit(self.probecircle, registration = 5, location = self.right_probe_position)
        blit(self.innercircle, registration = 5, location = self.left_probe_position)
        blit(self.innercircle, registration = 5, location = self.right_probe_position)

        # Right detection target
        blit(self.target, registration = 5, location = self.right_probe_position)
        flip()

    def exo_cuing_task(self):
        while self.evm.before("x_cross_on"):
            self.trial_start_stimuli()
        
        while self.evm.between("x_cross_on", "cue_onset"):
            self.exo_trial_pre_cue_stimuli()

        while self.evm.between("cue_onset", "cue_offset"):
            if self.cue_location == "left":
                self.exo_trial_left_cue_stimuli()
            else:
                if self.cue_location == "right":
                    self.exo_trial_right_cue_stimuli()
                else:
                    self.exo_trial_neutral_cue_stimuli()
        
        while self.evm.between("cue_offset", "target_onset"):
            self.exo_trial_pre_cue_stimuli()

        while self.evm.between("target_onset", "target_offset"):
            if self.target_location == "left" and self.task_requirement == "detection":
                self.exo_trial_left_target_stimuli()
            else:
                if self.target_location == "right" and self.task_requirement == "detection":
                    self.exo_trial_right_target_stimuli()
                else:
                    if self.task_requirement == "illusory line motion rating":
                        self.draw_static_line()
                    else: 
                        if self.task_requirement == "rightward real line motion rating":
                            self.draw_right_line()
                        else:
                            if self.task_requirement == "leftward real line motion rating":
                                self.draw_left_line()

    #######################################################################################
    # FUNCTIONS DEFINING GAZE-CUING STIMULI
    #######################################################################################

    def gaze_trial_pre_cue_stimuli(self):
        # Face without pupils
        fill()
        blit(self.facecircle, registration = 5, location = P.screen_c)
        blit(self.eyecircle, registration = 5, location = self.left_eye_position)
        blit(self.eyecircle, registration = 5, location = self.right_eye_position)
        blit(self.nose, registration = 5, location = P.screen_c)
        blit(self.mouth, registration = 5, location = self.mouth_position)

        # Probes
        blit(self.probecircle, registration = 5, location = self.left_probe_position)
        blit(self.probecircle, registration = 5, location = self.right_probe_position)
        blit(self.innercircle, registration = 5, location = self.left_probe_position)
        blit(self.innercircle, registration = 5, location = self.right_probe_position)
        flip()

    def gaze_trial_left_cue_stimuli(self):
        fill()
        blit(self.facecircle, registration = 5, location = P.screen_c)
        blit(self.eyecircle, registration = 5, location = self.left_eye_position)
        blit(self.eyecircle, registration = 5, location = self.right_eye_position)
        blit(self.pupilcircle, registration = 5, location = self.lefteye_left_pupilcue_position)
        blit(self.pupilcircle, registration = 5, location = self.righteye_left_pupilcue_position)
        blit(self.nose, registration = 5, location = P.screen_c)
        blit(self.mouth, registration = 5, location = self.mouth_position)
        
        # Probes
        blit(self.probecircle, registration = 5, location = self.left_probe_position)
        blit(self.probecircle, registration = 5, location = self.right_probe_position)
        blit(self.innercircle, registration = 5, location = self.left_probe_position)
        blit(self.innercircle, registration = 5, location = self.right_probe_position)
        flip()

    def gaze_trial_right_cue_stimuli(self):
        fill()
        blit(self.facecircle, registration = 5, location = P.screen_c)
        blit(self.eyecircle, registration = 5, location = self.left_eye_position)
        blit(self.eyecircle, registration = 5, location = self.right_eye_position)
        blit(self.pupilcircle, registration = 5, location = self.lefteye_right_pupilcue_position)
        blit(self.pupilcircle, registration = 5, location = self.righteye_right_pupilcue_position)
        blit(self.nose, registration = 5, location = P.screen_c)
        blit(self.mouth, registration = 5, location = self.mouth_position)
        
        # Probes
        blit(self.probecircle, registration = 5, location = self.left_probe_position)
        blit(self.probecircle, registration = 5, location = self.right_probe_position)
        blit(self.innercircle, registration = 5, location = self.left_probe_position)
        blit(self.innercircle, registration = 5, location = self.right_probe_position)
        flip()

    def gaze_trial_neutral_cue_stimuli(self):
        fill()
        blit(self.facecircle, registration = 5, location = P.screen_c)
        blit(self.eyecircle, registration = 5, location = self.left_eye_position)
        blit(self.eyecircle, registration = 5, location = self.right_eye_position)
        blit(self.pupilcircle, registration = 5, location = self.left_eye_position)
        blit(self.pupilcircle, registration = 5, location = self.right_eye_position)
        blit(self.nose, registration = 5, location = P.screen_c)
        blit(self.mouth, registration = 5, location = self.mouth_position)
        
        # Probes
        blit(self.probecircle, registration = 5, location = self.left_probe_position)
        blit(self.probecircle, registration = 5, location = self.right_probe_position)
        blit(self.innercircle, registration = 5, location = self.left_probe_position)
        blit(self.innercircle, registration = 5, location = self.right_probe_position)
        flip()

    def gaze_cuing_task(self):
        while self.evm.before("x_cross_on"):
            self.trial_start_stimuli()
        
        while self.evm.between("x_cross_on", "cue_onset"):
            self.gaze_trial_pre_cue_stimuli()

        while self.evm.between("cue_onset", "cue_offset"):
            if self.cue_location == "left":
                self.gaze_trial_left_cue_stimuli()
            else:
                if self.cue_location == "right":
                    self.gaze_trial_right_cue_stimuli()
                else:
                    self.gaze_trial_neutral_cue_stimuli()

        while self.evm.between("cue_offset", "target_onset"):
            self.gaze_trial_pre_cue_stimuli()

        while self.evm.between("target_onset", "target_offset"):
            if self.target_location == "left" and self.task_requirement == "detection":
                self.exo_trial_left_target_stimuli()
            else:
                if self.target_location == "right" and self.task_requirement == "detection":
                    self.exo_trial_right_target_stimuli()
                else:
                    if self.task_requirement == "illusory line motion rating":
                        self.draw_static_line()
                    else:
                        if self.task_requirement == "rightward real line motion rating":
                            self.draw_right_line()
                        else:
                            if self.task_requirement == "leftward real line motion rating":
                                self.draw_left_line()

    #######################################################################################
        # DRAWING THE LINES: NO MOTION, REAL LEFTWARD MOTION, AND REAL RIGHTWARD MOTION
    #######################################################################################
                
    def draw_static_line(self):

        def static_line():
            # Static line composed of small lines; 260 Hz Monitor
            #blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
            #blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
            #blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
            #blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
            #blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
            #blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
            #blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
            #blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)

            # Static line composed of small lines; 120 Hz monitor
            blit(self.moving_line, registration = 5, location = self.moving_line_1_position)
            blit(self.moving_line, registration = 5, location = self.moving_line_2_position)
            blit(self.moving_line, registration = 5, location = self.moving_line_3_position)
            blit(self.moving_line, registration = 5, location = self.moving_line_4_position)


        if self.cuing_task_type == "gaze":
            # Face without pupils
            fill()
            blit(self.facecircle, registration = 5, location = P.screen_c)
            blit(self.eyecircle, registration = 5, location = self.left_eye_position)
            blit(self.eyecircle, registration = 5, location = self.right_eye_position)
            blit(self.nose, registration = 5, location = P.screen_c)
            blit(self.mouth, registration = 5, location = self.mouth_position)

            # Probes
            blit(self.probecircle, registration = 5, location = self.left_probe_position)
            blit(self.probecircle, registration = 5, location = self.right_probe_position)
            blit(self.innercircle, registration = 5, location = self.left_probe_position)
            blit(self.innercircle, registration = 5, location = self.right_probe_position)

            # Static line
            #blit(self.static_line, registration = 5, location = self.static_line_position)
            static_line()
            flip()
        else:
            if self.cuing_task_type == "exogenous":
                # X-cross
                fill()
                blit(self.x_cross1, registration = 5, location = P.screen_c)
                blit(self.x_cross2, registration = 5, location = P.screen_c)

                # Probes
                blit(self.probecircle, registration = 5, location = self.left_probe_position)
                blit(self.probecircle, registration = 5, location = self.right_probe_position)
                blit(self.innercircle, registration = 5, location = self.left_probe_position)
                blit(self.innercircle, registration = 5, location = self.right_probe_position)
                
                # Static line
                #blit(self.static_line, registration = 5, location = self.static_line_position)

                # Static line composed of small lines
                static_line()

                flip()

    def draw_right_line(self):            

        def gaze_line_stimuli():
            # Face without pupils
            blit(self.facecircle, registration = 5, location = P.screen_c)
            blit(self.eyecircle, registration = 5, location = self.left_eye_position)
            blit(self.eyecircle, registration = 5, location = self.right_eye_position)
            blit(self.nose, registration = 5, location = P.screen_c)
            blit(self.mouth, registration = 5, location = self.mouth_position)

            # Probes
            blit(self.probecircle, registration = 5, location = self.left_probe_position)
            blit(self.probecircle, registration = 5, location = self.right_probe_position)
            blit(self.innercircle, registration = 5, location = self.left_probe_position)
            blit(self.innercircle, registration = 5, location = self.right_probe_position)

        def exo_line_stimuli():
            # X-cross
            blit(self.x_cross1, registration = 5, location = P.screen_c)
            blit(self.x_cross2, registration = 5, location = P.screen_c)

            # Probes
            blit(self.probecircle, registration = 5, location = self.left_probe_position)
            blit(self.probecircle, registration = 5, location = self.right_probe_position)
            blit(self.innercircle, registration = 5, location = self.left_probe_position)
            blit(self.innercircle, registration = 5, location = self.right_probe_position)
                    

        # if self.task_requirement == "rightward real line motion rating":
        #     while self.evm.between("target_onset", "line1"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #                 flip()

        #     while self.evm.between("line1", "line2"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #                 flip()

        #     while self.evm.between("line2", "line3"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #                 flip()

        #     while self.evm.between("line3", "line4"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #                 flip()

        #     while self.evm.between("line4", "line5"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #                 flip()

        #     while self.evm.between("line5", "line6"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #                 flip()

        #     while self.evm.between("line6", "line7"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #                 flip()

        #     while self.evm.between("line7", "target_offset"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #             blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_1_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #                 blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #                 flip()
            
            # 120 Hz monitor 
            
        if self.task_requirement == "rightward real line motion rating":
            while self.evm.between("target_onset", "line1"):
                if self.cuing_task_type == "gaze":
                    fill()
                    gaze_line_stimuli()
                    blit(self.moving_line, registration = 5, location = self.moving_line_1_position)
                    flip()
                else:
                    if self.cuing_task_type == "exogenous":
                        fill()
                        exo_line_stimuli()
                        blit(self.moving_line, registration = 5, location = self.moving_line_1_position)
                        flip()

            while self.evm.between("line1", "line2"):
                if self.cuing_task_type == "gaze":
                    fill()
                    gaze_line_stimuli()
                    blit(self.moving_line, registration = 5, location = self.moving_line_1_position)
                    blit(self.moving_line, registration = 5, location = self.moving_line_2_position)
                    flip()
                else:
                    if self.cuing_task_type == "exogenous":
                        fill()
                        exo_line_stimuli()
                        blit(self.moving_line, registration = 5, location = self.moving_line_1_position)
                        blit(self.moving_line, registration = 5, location = self.moving_line_2_position)
                        flip()

            while self.evm.between("line2", "line3"):
                if self.cuing_task_type == "gaze":
                    fill()
                    gaze_line_stimuli()
                    blit(self.moving_line, registration = 5, location = self.moving_line_1_position)
                    blit(self.moving_line, registration = 5, location = self.moving_line_2_position)
                    blit(self.moving_line, registration = 5, location = self.moving_line_3_position)
                    flip()
                else:
                    if self.cuing_task_type == "exogenous":
                        fill()
                        exo_line_stimuli()
                        blit(self.moving_line, registration = 5, location = self.moving_line_1_position)
                        blit(self.moving_line, registration = 5, location = self.moving_line_2_position)
                        blit(self.moving_line, registration = 5, location = self.moving_line_3_position)
                        flip()

            while self.evm.between("line4", "target_offset"):
                if self.cuing_task_type == "gaze":
                    fill()
                    gaze_line_stimuli()
                    blit(self.moving_line, registration = 5, location = self.moving_line_1_position)
                    blit(self.moving_line, registration = 5, location = self.moving_line_2_position)
                    blit(self.moving_line, registration = 5, location = self.moving_line_3_position)
                    blit(self.moving_line, registration = 5, location = self.moving_line_4_position)
                    flip()
                else:
                    if self.cuing_task_type == "exogenous":
                        fill()
                        exo_line_stimuli()
                        blit(self.moving_line, registration = 5, location = self.moving_line_1_position)
                        blit(self.moving_line, registration = 5, location = self.moving_line_2_position)
                        blit(self.moving_line, registration = 5, location = self.moving_line_3_position)
                        blit(self.moving_line, registration = 5, location = self.moving_line_4_position)
                        flip()

    def draw_left_line(self):            

        def gaze_line_stimuli():
            # Face without pupils
            blit(self.facecircle, registration = 5, location = P.screen_c)
            blit(self.eyecircle, registration = 5, location = self.left_eye_position)
            blit(self.eyecircle, registration = 5, location = self.right_eye_position)
            blit(self.nose, registration = 5, location = P.screen_c)
            blit(self.mouth, registration = 5, location = self.mouth_position)

            # Probes
            blit(self.probecircle, registration = 5, location = self.left_probe_position)
            blit(self.probecircle, registration = 5, location = self.right_probe_position)
            blit(self.innercircle, registration = 5, location = self.left_probe_position)
            blit(self.innercircle, registration = 5, location = self.right_probe_position)

        def exo_line_stimuli():
            # X-cross
            blit(self.x_cross1, registration = 5, location = P.screen_c)
            blit(self.x_cross2, registration = 5, location = P.screen_c)

            # Probes
            blit(self.probecircle, registration = 5, location = self.left_probe_position)
            blit(self.probecircle, registration = 5, location = self.right_probe_position)
            blit(self.innercircle, registration = 5, location = self.left_probe_position)
            blit(self.innercircle, registration = 5, location = self.right_probe_position)
                    

        # if self.task_requirement == "leftward real line motion rating":
        #     while self.evm.between("target_onset", "line1"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #                 flip()

        #     while self.evm.between("line1", "line2"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #                 flip()

        #     while self.evm.between("line2", "line3"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #                 flip()

        #     while self.evm.between("line3", "line4"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #                 flip()

        #     while self.evm.between("line4", "line5"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #                 flip()

        #     while self.evm.between("line5", "line6"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #                 flip()

        #     while self.evm.between("line6", "line7"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #                 flip()

        #     while self.evm.between("line7", "target_offset"):
        #         if self.cuing_task_type == "gaze":
        #             fill()
        #             gaze_line_stimuli()
        #             blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #             blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #             blit(self.longer_moving_line, registration = 5, location = self.real_line_1_position)
        #             flip()
        #         else:
        #             if self.cuing_task_type == "exogenous":
        #                 fill()
        #                 exo_line_stimuli()
        #                 blit(self.longer_moving_line, registration = 5, location = self.real_line_8_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_7_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_6_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_5_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_4_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_3_position)
        #                 blit(self.shorter_moving_line, registration = 5, location = self.real_line_2_position)
        #                 blit(self.longer_moving_line, registration = 5, location = self.real_line_1_position)
        #                 flip()
            
        if self.task_requirement == "leftward real line motion rating":
            while self.evm.between("target_onset", "line1"):
                if self.cuing_task_type == "gaze":
                    fill()
                    gaze_line_stimuli()
                    blit(self.moving_line, registration = 5, location = self.moving_line_4_position)
                    flip()
                else:
                    if self.cuing_task_type == "exogenous":
                        fill()
                        exo_line_stimuli()
                        blit(self.moving_line, registration = 5, location = self.moving_line_4_position)
                        flip()

            while self.evm.between("line1", "line2"):
                if self.cuing_task_type == "gaze":
                    fill()
                    gaze_line_stimuli()
                    blit(self.moving_line, registration = 5, location = self.moving_line_4_position)
                    blit(self.moving_line, registration = 5, location = self.moving_line_3_position)
                    flip()
                else:
                    if self.cuing_task_type == "exogenous":
                        fill()
                        exo_line_stimuli()
                        blit(self.moving_line, registration = 5, location = self.moving_line_4_position)
                        blit(self.moving_line, registration = 5, location = self.moving_line_3_position)
                        flip()

            while self.evm.between("line2", "line3"):
                if self.cuing_task_type == "gaze":
                    fill()
                    gaze_line_stimuli()
                    blit(self.moving_line, registration = 5, location = self.moving_line_4_position)
                    blit(self.moving_line, registration = 5, location = self.moving_line_3_position)
                    blit(self.moving_line, registration = 5, location = self.moving_line_2_position)
                    flip()
                else:
                    if self.cuing_task_type == "exogenous":
                        fill()
                        exo_line_stimuli()
                        blit(self.moving_line, registration = 5, location = self.moving_line_4_position)
                        blit(self.moving_line, registration = 5, location = self.moving_line_3_position)
                        blit(self.moving_line, registration = 5, location = self.moving_line_2_position)
                        flip()

            while self.evm.between("line4", "target_offset"):
                if self.cuing_task_type == "gaze":
                    fill()
                    gaze_line_stimuli()
                    blit(self.moving_line, registration = 5, location = self.moving_line_4_position)
                    blit(self.moving_line, registration = 5, location = self.moving_line_3_position)
                    blit(self.moving_line, registration = 5, location = self.moving_line_2_position)
                    blit(self.moving_line, registration = 5, location = self.moving_line_1_position)
                    flip()
                else:
                    if self.cuing_task_type == "exogenous":
                        fill()
                        exo_line_stimuli()
                        blit(self.moving_line, registration = 5, location = self.moving_line_4_position)
                        blit(self.moving_line, registration = 5, location = self.moving_line_3_position)
                        blit(self.moving_line, registration = 5, location = self.moving_line_2_position)
                        blit(self.moving_line, registration = 5, location = self.moving_line_1_position)
                        flip()

    #######################################################################################
    # FINALIZING THE BASIC CUING DETECTION TASK
    #######################################################################################
    
    def detection_cuing_task(self):
        if self.cuing_task_type == "gaze":
            self.gaze_cuing_task()
            self.gaze_trial_pre_cue_stimuli()
            flip()
        else:
            if self.cuing_task_type == "exogenous":
                self.exo_cuing_task()
                self.exo_trial_pre_cue_stimuli()
                flip()

    #######################################################################################

    def block(self):
        pass

    def setup_response_collector(self):
        self.rc.uses(KeyPressResponse) # Specify to record key presses
        self.rc.terminate_after = [1700, TK_MS] # End the collection loop after 1700 ms
        #self.rc.display_callback = self.resp_callback # Run the self.resp.callback method every loop
        self.rc.flip = True # draw the screen at the end of every loop
        self.rc.keypress_listener.key_map = KeyMap('response', ['z', '/', 'b'], ['left', 'right', 'no motion'], [sdl2.SDLK_z, sdl2.SDLK_SLASH, sdl2.SDLK_b]) # Interpret Z-key presses as "left", /-key presses as "right"
        self.rc.keypress_listener.interrupts = True # end the collection loop if a valid key is pressed

    def trial_prep(self):

        # Define stimulus event timings
        if self.task_requirement == "detection":
            events = []
            events.append([100, "x_cross_on"]) # Add in the x-cross after fixation
            events.append([events[-1][0] + 400, "cue_onset"]) # Add in the cue
            events.append([events[-1][0] + 50, "cue_offset"]) # Remove the cue
            events.append([events[-1][0] + 50, "target_onset"]) # Add in the target
            events.append([events[-1][0] + 50, "target_offset"]) # Remove the target
        else:
            if self.task_requirement == "illusory line motion rating":
                events = []
                events.append([100, "x_cross_on"]) # Add in the x-cross after fixation
                events.append([events[-1][0] + 400, "cue_onset"]) # Add in the cue
                events.append([events[-1][0] + 50, "cue_offset"]) # Remove the cue
                events.append([events[-1][0] + 50, "target_onset"]) # Add in the target
                events.append([events[-1][0] + 1000, "target_offset"]) # Remove the line in line motion trials
            else:
                events = []
                events.append([100, "x_cross_on"]) # Add in the x-cross after fixation
                events.append([events[-1][0] + 400, "cue_onset"]) # Add in the cue
                events.append([events[-1][0] + 50, "cue_offset"]) # Remove the cue
                events.append([events[-1][0] + 50, "target_onset"]) # Add in the target
                # events.append([events[-1][0] + 4, "line1"]) # Line segments for 260 Hz monitor
                # events.append([events[-1][0] + 4, "line2"])
                # events.append([events[-1][0] + 4, "line3"])
                # events.append([events[-1][0] + 4, "line4"])
                # events.append([events[-1][0] + 4, "line5"])
                # events.append([events[-1][0] + 4, "line6"])
                # events.append([events[-1][0] + 4, "line7"])
                events.append([events[-1][0] + 8.33, "line1"]) # Line segments for 120 Hz monitor
                events.append([events[-1][0] + 8.33, "line2"])
                events.append([events[-1][0] + 8.33, "line3"])
                events.append([events[-1][0] + 8.33, "line4"])

                events.append([events[-1][0] + 1004, "target_offset"]) # Remove the line in line motion trials
                
        for e in events:
            self.evm.register_ticket(ET(e[1], e[0]))

        # If the first trial of the block, display message to start.
        if P.run_practice_blocks and P.block_number == 1 and P.trial_number == 1:
            self.trial_start_stimuli()
            flip()
            blit(self.practice_block_message, registration = 5, location = self.block_start_message_position)
            flip()
            any_key()
        
        if P.block_number == 2 and P.trial_number == 1:
            self.trial_start_stimuli()
            flip()
            blit(self.block_start_message, registration = 5, location = self.block_start_message_position)
            flip()
            any_key()

        if P.block_number > 2 and P.trial_number == 1:
            self.trial_start_stimuli()
            flip()
            blit(self.next_block_message, registration = 5, location = self.block_start_message_position)
            flip()
            any_key()

        if P.trial_number > 1:
            self.trial_start_stimuli()
            flip()
            blit(self.next_trial_message, registration = 5, location = self.next_trial_message_posiition)
            flip()
            any_key()

    def trial(self):
        self.detection_cuing_task()
        
        if self.task_requirement == "detection":
            flip()
            self.rc.collect()
            rt = self.rc.keypress_listener.response(False, True)
            response = self.rc.keypress_listener.response(True, False)
        else:
            fill()
            blit(self.scale, 5, self.scale_loc)
            blit(self.motion_rating_message, registration = 5, location = self.motion_rating_message_position)
            flip()
            response, rt = self.scale_listener.collect()
            print(response, rt)

        return {
            "practice": P.practicing,
            "cue_type": self.cuing_task_type,
            "task_requirement": self.task_requirement,
            "cue_location": self.cue_location,
            "target_location": self.target_location,
            "response": response,
            "block_num": P.block_number,
            "trial_num": P.trial_number * P.block_number,
            "reaction_time": rt
        }

    def trial_clean_up(self):
        pass

    def clean_up(self):
        pass

    def scale_callback(self):
        mouse_x, mouse_y = mouse_pos()
        scale_mid_y = self.scale_bounds.center[1]
        fill()
        blit(self.motion_rating_message, registration = 5, location = self.motion_rating_message_position)
        blit(self.left_motion_rating_message, registration = 5, location = self.left_motion_rating_message_position)
        blit(self.right_motion_rating_message, registration = 5, location = self.right_motion_rating_message_position)
        blit(self.no_motion_rating_message, registration = 5, location = self.no_motion_rating_message_position)
        blit(self.no_motion_rating_line, registration = 5, location = self.scale_loc)
        blit(self.scale, 5, self.scale_loc)
        if (mouse_x, mouse_y) in self.scale_bounds:
            blit(self.scale_mark, 5, (mouse_x, scale_mid_y))
        flip()


REGISTRATION_MAP = {
    1: (0, -1.0),
    2: (-0.5, -1.0),
    3: (-1.0, -1.0),
    4: (0, -0.5),
    5: (-0.5, -0.5),
    6: (-1.0, -0.5),
    7: (0, 0),
    8: (-0.5, 0),
    9: (-1.0, 0),
}
        
def bounds_from_blit(rect, location, registration=5):
    x_offset, y_offset = REGISTRATION_MAP[registration]
    width, height = rect.dimensions
    x1 = location[0] + int(width * x_offset)
    y1 = location[1] + int(height * y_offset)
    x2 = x1 + width
    y2 = y1 + height
    return RectangleBoundary('', (x1, y1), (x2, y2))


class ScaleListener(BaseResponseListener):
    """A convenience class for collecting continuous scale responses.

    This class requires that the response scale has already been drawn to the
    screen prior to response collection.

    Args:
        bounds (:obj:`~klibs.KLBoundary.RectangleBoundary`): A rectangle boundary
            defining the size and location of the response scale.
        start_pos (tuple, optional): The position to place the mouse cursor at the
            start of the scale collection loop (in (x, y) pixel coordinates).
            Defaults to the center of the screen if not specified.
        timeout (float, optional): The maximum duration (in seconds) to wait for a
            color response. Defaults to None (no timeout).
        loop_callback (callable, optional): An optional function or method to be
            called every time the collection loop checks for new input.

    """
    def __init__(self, bounds, start_pos=None, timeout=None, loop_callback=None):
        super(ScaleListener, self).__init__(timeout, loop_callback)
        self.default_response = (None, -1)
        self._cursor_was_hidden = False
        self._start_pos = start_pos if start_pos else P.screen_c
        if not isinstance(bounds, RectangleBoundary):
            raise TypeError("Scale bounds must be a RectangleBoundary object.")
        self._bounds = bounds

    def _timestamp(self):
        return sdl2.SDL_GetTicks()
        
    def _get_scale_pos(self, cursor_pos):
        if not pos in self._bounds:
            return None
        x1 = self._bounds.p1[0]
        return (pos[0] - x1) / self._bounds.width

    def init(self):
        """Initializes the listener for response collection.

        This method shows the mouse cursor and warps it to the start position.

        Only needs to be called manually if using :meth:`listen` directly in a
        custom collection loop.

        """
        # Start with cursor shown in start position
        self._cursor_was_hidden = sdl2.ext.cursor_hidden()
        sdl2.ext.show_cursor()
        mouse_pos(position=self._start_pos)
        # Clear any existing events in the queue and set the response start time
        flush()
        self._loop_start = self._timestamp()

    def listen(self, q):
        """Checks a queue of input events for continuous scale responses.

        Along with :meth:`init` and :meth:`cleanup`, this method can be used to
        create custom response collection loops in cases where :meth:`collect`
        doesn't offer enough flexibility.

        Args:
            q (list): A list of input events to check for scale responses.

        Returns:
            tuple or None: A ``(response, rt)`` tuple if the scale has been
            clicked, otherwise None.

        """
        for e in q:
            if e.type == sdl2.SDL_MOUSEBUTTONUP:
                # First, ensure mouse click was within the scale boundary
                pos = (e.button.x * P.screen_scale_x, e.button.y * P.screen_scale_y)
                if not pos in self._bounds:
                    continue
                # Next, calculate where the click was relative to the scale
                x1 = self._bounds.p1[0]
                resp = (pos[0] - x1) / self._bounds.width
                rt = e.button.timestamp - self._loop_start
                return (resp, rt)
        return None

    def cleanup(self):
        """Performs any necessary cleanup after response collection.

        For the scale listener, this method hides the mouse cursor if it wasn't
        visible already when :meth:`init` was called, and resets the response
        timer.

        Only needs to be called manually if using :meth:`listen` directly in a
        custom collection loop.

        """
        self._loop_start = None
        if self._cursor_was_hidden:
            sdl2.ext.hide_cursor()