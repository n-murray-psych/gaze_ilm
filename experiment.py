# -*- coding: utf-8 -*-

__author__ = "Nicholas Murray"

import klibs
from klibs import P
from klibs.KLGraphics import KLDraw as kld # To draw shapes
from klibs.KLUserInterface import any_key, mouse_pos # So participants can press any key to continue; convert mouse presses to mouse position coordinates
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
from klibs.KLUserInterface import mouse_pos
from klibs.KLBoundary import RectangleBoundary

# Defining some useful constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (45, 45, 45)

class gaze_ilm(klibs.Experiment):

    def setup(self):
        # Block and trial start messages
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

        # Motion rating scale stimuli
        ratingscalebaselength = deg_to_px(4.30)
        ratingscalebaseheight = deg_to_px(.5)
        ratingscalebaseverticaloffset = deg_to_px(3.75)
        self.rating_scale_base_position = (P.screen_c[0], P.screen_c[1]+ratingscalebaseverticaloffset)
        self.rating_scale_base = kld.Rectangle(width = ratingscalebaselength, height = ratingscalebaseheight, stroke = [1, (0,0,0)], fill = WHITE)
        ratingscalemidpoint = deg_to_px(.5)
        self.rating_scale_midpoint = kld.Line(length = ratingscalemidpoint, color = BLACK, thickness = 3)
        #self.rating_scale_base = kld.Line(ratingscalebaselength, color = WHITE, thickness = 3, rotation = 90)

        ratingscaleheight = deg_to_px(1)
        ratingscaleheightverticaloffset = deg_to_px(3)
        ratingscaleheighthorizontaloffset = deg_to_px(2.15)
        self.rating_scale_left_height_position = (P.screen_c[0]-ratingscaleheighthorizontaloffset, P.screen_c[1]+ratingscaleheightverticaloffset)
        self.rating_scale_right_height_position = (P.screen_c[0]+ratingscaleheighthorizontaloffset, P.screen_c[1]+ratingscaleheightverticaloffset)
        self.rating_scale_height = kld.Line(ratingscaleheight, color = WHITE, thickness = 3)

        ratingscalehypotenuse = deg_to_px(2.37)
        ratingscalehypotenuseverticaloffset = deg_to_px(3)
        ratingscalehypotenusehorizontaloffset = deg_to_px(1.075)
        self.rating_scale_left_hypotenuse_position = (P.screen_c[0]-ratingscalehypotenusehorizontaloffset, P.screen_c[1]+ratingscalehypotenuseverticaloffset)
        self.rating_scale_left_hypotenuse = kld.Line(ratingscalehypotenuse, color = WHITE, thickness = 3, rotation = -65.056)
        self.rating_scale_right_hypotenuse_position = (P.screen_c[0]+ratingscalehypotenusehorizontaloffset, P.screen_c[1]+ratingscalehypotenuseverticaloffset)
        self.rating_scale_right_hypotenuse = kld.Line(ratingscalehypotenuse, color = WHITE, thickness = 3, rotation = 65.056)

        ratingscalebasex1 = self.rating_scale_base_position[0]-(.5*ratingscalebaselength)
        ratingscalebasex2 = self.rating_scale_base_position[0]+(.5*ratingscalebaselength)
        ratingscalebasey1 = self.rating_scale_base_position[1]+(.5*ratingscalebaseheight)
        ratingscalebasey2 = self.rating_scale_base_position[1]-(.5*ratingscalebaseheight)
        ratingscalebounds = RectangleBoundary(mouse_pos(), (ratingscalebasex1, ratingscalebasey1), (ratingscalebasex2, ratingscalebasey2))
        
        # Response scale from Austin
        scale_w = int(P.screen_x * 0.8)
        scale_h = int(scale_w * 0.2)
        scale_stroke = [int(scale_h * 0.1), BLACK, klibs.STROKE_INNER]
        self.scale_loc = (P.screen_c[0], int(P.screen_y * 0.7))
        
        self.scale = kld.Rectangle(scale_w, scale_h, stroke=scale_stroke)
        self.scale_mark = kld.Rectangle(int(scale_h * 0.1), scale_h, fill=BLACK)
        self.scale_bounds = bounds_from_blit(self.scale, self.scale_loc)

        self.scale_listener = ScaleListener(
            self.scale_bounds, loop_callback=self.scale_callback
        )

    #######################################################################################
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
                    if self.task_requirement == "line motion rating":
                        self.draw_static_line()

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
                    if self.task_requirement == "line motion rating":
                        self.draw_static_line()

    #######################################################################################
        # DRAWING THE LINES: NO MOTION, REAL LEFTWARD MOTION, AND REAL RIGHTWARD MOTION
    #######################################################################################
                
    def draw_static_line(self):
        fill()
        blit(self.static_line, registration = 5, location = self.static_line_position)
        flip()

    #######################################################################################
        # DRAWING THE MOTION RATING SCALE
    #######################################################################################
    
    def draw_rating_scale(self):
        fill()
        blit(self.rating_scale_base, registration = 5, location = self.rating_scale_base_position)
        blit(self.rating_scale_midpoint, registration = 5, location = self.rating_scale_base_position)
        blit(self.rating_scale_height, registration = 5, location = self.rating_scale_left_height_position)
        blit(self.rating_scale_height, registration = 5, location = self.rating_scale_right_height_position)
        blit(self.rating_scale_left_hypotenuse, registration = 5, location = self.rating_scale_left_hypotenuse_position)
        blit(self.rating_scale_right_hypotenuse, registration = 5, location = self.rating_scale_right_hypotenuse_position)
        flip()

    #######################################################################################
    # FINALIZING THE BASIC CUING DETECTION TASK
    #######################################################################################
    
    def detection_cuing_task(self):
        if self.cuing_task_type == "gaze":
            self.gaze_cuing_task()
            self.gaze_trial_pre_cue_stimuli()
        else:
            if self.cuing_task_type == "exogenous":
                self.exo_cuing_task()
                self.exo_trial_pre_cue_stimuli()

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
        events = []
        events.append([100, "x_cross_on"]) # Add in the x-cross after fixation
        events.append([events[-1][0] + 400, "cue_onset"]) # Add in the cue
        events.append([events[-1][0] + 50, "cue_offset"]) # Remove the cue
        events.append([events[-1][0] + 50, "target_onset"]) # Add in the target
        events.append([events[-1][0] + 50, "target_offset"]) # Remove the target

        for e in events:
            self.evm.register_ticket(ET(e[1], e[0]))

        # If the first trial of the block, display message to start.
        if P.block_number == 1 and P.trial_number == 1:
            self.trial_start_stimuli()
            flip()
            self.draw_rating_scale()
            flip()
            blit(self.block_start_message, registration = 5, location = self.block_start_message_position)
            flip()
            any_key()

        if P.block_number > 1 and P.trial_number == 1:
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
            flip()
            resp, rt = self.scale_listener.collect()
            print(resp, rt)

        return {
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