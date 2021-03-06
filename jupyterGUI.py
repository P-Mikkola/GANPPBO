import sys
import os

PROJECTDIR = os.getcwd()
GAN_DIR = os.path.join(PROJECTDIR, "ganspace")
sys.path.insert(0, GAN_DIR)

import numpy as np
import pandas as pd

import ipywidgets as widgets

from jupGUI_utils.utils import verbose_info, widget_image_to_bytes

VERBOSE = False
VERBOSE_ENDL = "\t   "


class GUIses(object):
    def __init__(self,
                 ganpreffinder):
        """
        :param ganpreffinder: GANPrefFinder class instance
        """
        self.optimize_Theta = False

        self.GANpf = ganpreffinder

        WIDGET_CONTINIOUS_UPDATE = self.GANpf.USING_CUDA
        WIDGET_WIDTH = 300

        self.strength = 0
        self.w = self.GANpf.get_init_W()
        init_img = self.GANpf.get_init_img()

        self.X, self.Xi = self.GANpf.get_next_query()

        self.widget_image = widgets.Image(format='png', width=WIDGET_WIDTH,
                                          value=self.to_bytes(init_img))

        self.widget_pref_image = widgets.Image(format='png', width=WIDGET_WIDTH,
                                               value=self.to_bytes(init_img))

        self.widget_image_init = widgets.Image(format='png', width=WIDGET_WIDTH,
                                               value=self.to_bytes(init_img))

        self.widget_strength_slider = widgets.IntSlider(min=self.GANpf.left_bound,
                                                        max=self.GANpf.right_bound,
                                                        value=self.strength,
                                                        continuous_update=WIDGET_CONTINIOUS_UPDATE,
                                                        description='strength:')

        self.widget_strength_text = widgets.IntText(description="strength:",
                                                    continuous_update=WIDGET_CONTINIOUS_UPDATE)

        self.widget_button_incs = widgets.Button(description="slider +10 (both sides)",
                                                 buttin_style="info",
                                                 layout=widgets.Layout(width="150px"))

        self.widget_button_decs = widgets.Button(description="slider -10 (both sides)",
                                                 buttin_style="info",
                                                 layout=widgets.Layout(width="150px"))

        self.widget_button_nq = widgets.Button(description="next query",
                                               buttin_style="info",
                                               layout=widgets.Layout(width="300px"))

        self.widget_chb_adaptive_init = widgets.Checkbox(
            value=self.GANpf.ADAPTIVE_INITIALIZATION,
            description='adaptive initialization', disabled=False, indent=False)


    def run(self):
        self.widget_strength_text.observe(self.change_strength, 'value')
        self.widget_button_nq.on_click(self.next_query)
        self.widget_button_incs.on_click(self.increase_slider_range)
        self.widget_button_decs.on_click(self.decrease_slider_range)
        self.widget_chb_adaptive_init.observe(self.switch_adaptive_init)
        # self.widget_chb_choose_comp.observe(self.switch_Xi_strategy)
        # self.widget_comp_slider.observe(self.change_component)

        widgets.link((self.widget_strength_slider, 'value'), (self.widget_strength_text, 'value'))

        manage_panel = widgets.VBox([
            widgets.Label(value='Control Panel:'),
            #widgets.HBox([self.widget_button_decs, self.widget_button_incs]),
            self.widget_strength_slider,
            self.widget_strength_text,
            self.widget_chb_adaptive_init,
            self.widget_button_nq
        ])

        image_panel = widgets.VBox([widgets.Label(value='Image:'), self.widget_image])

        pref_image_panel = widgets.VBox([widgets.Label(value='Preferred Image:'), self.widget_pref_image])

        init_image_panel = widgets.VBox([widgets.Label(value='Initial Image:'), self.widget_image_init])

        run_wid = widgets.VBox([
            widgets.HBox([image_panel, pref_image_panel, init_image_panel]),
            manage_panel
        ])

        return run_wid

    # === easy switching components ===

    def switch_adaptive_init(self, _):
        self.GANpf.switch_adaptive_initialization()
        if not self.GANpf.ADAPTIVE_INITIALIZATION:
            self.optimize_Theta = True

    def increase_slider_range(self, _):
        self.widget_strength_slider.min -= 10
        self.widget_strength_slider.max += 10

    def decrease_slider_range(self, _):
        self.widget_strength_slider.min += 10
        self.widget_strength_slider.max -= 10

    # === main functions ===

    def change_strength(self, strength):
        self._update_strength_value(strength.new)
        self._update_image()

    def next_query(self, _):
        self._updateGP()
        self._update_pref_image()
        # if self.optimize_Theta:
        #     print("+++ OPTIMIZING Theta for GP")
        #     self.ganpfinder.optimizeGP()
        #     self.optimize_Theta = False
        #     print("+++ FINISHED Theta OPTIMIZATION")
        self._update_X()
        self._next_query()
        self._update_strength_value(0)
        self._update_image()
        self._update_strength_slider_value()

    # === help functions ===

    @verbose_info(verbose=VERBOSE, msg="+ Updating GP", verbose_endl=VERBOSE_ENDL)
    def _updateGP(self):
        self.GANpf.updateGP(self.X, self.Xi, self.strength)

    @verbose_info(verbose=VERBOSE, msg="+ Getting next query", verbose_endl=VERBOSE_ENDL)
    def _next_query(self):
        self.X, self.Xi = self.GANpf.get_next_query()

    def _update_X(self):
        self.GANpf.update_adaptive_query(self.X, self.Xi, self.strength)

    @verbose_info(verbose=VERBOSE, msg="+ Updating image", verbose_endl=VERBOSE_ENDL)
    def _update_image(self):
        prefVec = self.GANpf.calculate_pref_vector(self.X, self.Xi, self.strength)
        layers_range = self.GANpf.get_comp_layers_range(self.Xi)
        img = self.GANpf.update_image(prefVec=prefVec, layers_range=layers_range)
        self.widget_image.value = self.to_bytes(img)

    @verbose_info(verbose=VERBOSE, msg="+ Updating preferred image", verbose_endl=VERBOSE_ENDL)
    def _update_pref_image(self):
        X_star = self.GANpf.get_last_X_star_scaled()
        img = self.GANpf.update_image(prefVec=X_star)
        self.widget_pref_image.value = self.to_bytes(img)

    def _update_strength_slider_value(self):
        self.widget_strength_slider.value = self.strength

    @verbose_info(verbose=VERBOSE, msg="+ Updating strength parameter", verbose_endl=VERBOSE_ENDL)
    def _update_strength_value(self, new_value):
        self.strength = new_value

    # ===============================

    @staticmethod
    def to_bytes(img):
        return widget_image_to_bytes(img)

    # === next query ===

    # def _move_user_Xi(self):
    #     if self.ganpfinder.AQ.custom_Xi_strategy:
    #         if self.widget_comp_slider.value < self.widget_comp_slider.max:
    #             self.widget_comp_slider.value += 1
    #         else:
    #             self.widget_comp_slider.value += 1
    #
    # @verbose_info(verbose=VERBOSE, msg="+ Updating GUI parameters", verbose_endl=VERBOSE_ENDL)
    # def _updateGUI(self):
    #     self.strength = 0
    #     self._move_user_Xi()
    #     if self.start_with_init_img:
    #         img = self.ganpfinder.get_init_img()
    #     else:
    #         prefVec = self.ganpfinder.calculate_pref_vector(self.X, self.Xi, self.strength)
    #         img = self.ganpfinder.update_image(prefVec=prefVec)
    #     self.widget_image.value = self.to_bytes(img)
    #
    # # ==================
    #
    # # === custom change component ===
    #
    # def change_component(self, comp_index):
    #     comp_index_value = comp_index.new
    #     if type(comp_index_value) is int:
    #         self._Xi_from_user(comp_index_value)
    #         if self.ganpfinder.AQ.custom_Xi_strategy:
    #             self._update_image()
    #
    # @verbose_info(verbose=VERBOSE, msg="+ Updating component switch parameter", verbose_endl=VERBOSE_ENDL)
    # def _Xi_from_user(self, comp_index_value):
    #     self.ganpfinder.Xi_from_user(comp_index_value)
    #     self.Xi = self.ganpfinder.AQ.get_Xi()
    #
    # @verbose_info(verbose=VERBOSE, msg="+ Updating GUI parameters", verbose_endl=VERBOSE_ENDL)
    # def _update_image(self):
    #     img = self._modify_by_strength(self.strength)
    #     self.widget_image.value = self.to_bytes(img)
