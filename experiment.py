# -*- coding: utf-8 -*-

__author__ = "Nicholas Murray"

import klibs
from klibs import P
from klibs.KLGraphics import KLDraw as kld # To draw shapes
from klibs.KLUserInterface import any_key # So participants can press any key to continue
from klibs.KLGraphics import fill, blit, flip # To actually make drawn shapes appear on the screen
from klibs.KLUtilities import deg_to_px # Convert stimulus sizes according to degrees of visual angle

# Defining some useful constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (45, 45, 45)

class gaze_ilm(klibs.Experiment):

    def setup(self):
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
        probe_horizontal_offset = deg_to_px(5)
        probe_vertical_offset = deg_to_px(1.1)
        self.probecircle = kld.Circle(diameter = probecirclesize, stroke = probestroke, fill = WHITE)
        self.innercircle = kld.Circle(diameter = innercirclesize, stroke = probestroke, fill = GREY)
        self.left_probe_position = (P.screen_c[0]-probe_horizontal_offset, P.screen_c[1]-probe_vertical_offset)
        self.right_probe_position = (P.screen_c[0]+probe_horizontal_offset, P.screen_c[1]-probe_vertical_offset)
        
        # Exogenous cue stimuli
        cue_stroke_thickness = 2
        self.cue = kld.Circle(diameter = probecirclesize, stroke = [cue_stroke_thickness, WHITE], fill = WHITE)

        # Detection target stimuli
        targetsize = deg_to_px(.23)
        targetstroke = [1, (0,0,0)]
        self.target = kld.Circle(diameter = targetsize, stroke = targetstroke, fill = WHITE)


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

    def block(self):
        pass

    def trial_prep(self):
        pass

    def trial(self):

        return {
            "block_num": P.block_number,
            "trial_num": P.trial_number
        }

    def trial_clean_up(self):
        pass

    def clean_up(self):
        pass
