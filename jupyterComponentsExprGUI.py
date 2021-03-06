import sys
import os

PROJECTDIR = os.getcwd()
GAN_DIR = os.path.join(PROJECTDIR, "ganspace")
sys.path.insert(0, GAN_DIR)

import numpy as np
import pandas as pd
import ipywidgets as widgets

from jupGUI_utils.utils import widget_image_to_bytes


class GUICompExprSes():
    def __init__(self, ganpfinder):
        self.GANpf = ganpfinder

        WIDGET_CONTINIOUS_UPDATE = self.GANpf.USING_CUDA
        WIDGET_WIDTH = 300

        self.strength = 0
        self.component = 0
        self.min_component = 0
        self.max_component = self.GANpf.N_comp_in_use - 1
        self.w = self.GANpf.get_init_W()
        init_img = self.GANpf.get_init_img()

        self.X = np.zeros(self.GANpf.N_comp_in_use)
        self.Xi = np.zeros(self.GANpf.N_comp_in_use)
        self.Xi[self.component] = 1

        self.widget_image = widgets.Image(format='png', width=WIDGET_WIDTH,
                                          value=self.to_bytes(init_img))

        self.widget_strength_slider = widgets.IntSlider(min=self.GANpf.left_bound,
                                                        max=self.GANpf.right_bound,
                                                        value=self.strength,
                                                        continuous_update=WIDGET_CONTINIOUS_UPDATE,
                                                        description='strength:')

        self.widget_comp_slider = widgets.IntSlider(min=self.min_component,
                                                    max=self.max_component,
                                                    value=self.component,
                                                    continuous_update=False,
                                                    description='component:')

        self.widget_button_next_comp = widgets.Button(description="next component",
                                                      buttin_style="info",
                                                      layout=widgets.Layout(width="150px"))

        self.widget_button_prev_comp = widgets.Button(description="previous component",
                                                      buttin_style="info",
                                                      layout=widgets.Layout(width="150px"))

    def run(self):
        self.widget_strength_slider.observe(self.change_strength, names=['value'])
        self.widget_comp_slider.observe(self.change_component, names=['value'])
        self.widget_button_next_comp.on_click(self.next_component)
        self.widget_button_prev_comp.on_click(self.previous_component)

        run_wid = widgets.VBox([
            self.widget_image,
            self.widget_strength_slider,
            self.widget_comp_slider,
            widgets.HBox([self.widget_button_prev_comp,
                          self.widget_button_next_comp])
        ])

        return run_wid

    def change_strength(self, strength):
        self.strength = strength.new
        self._update_image()

    def change_component(self, component):
        self.component = component.new
        self._update_Xi()
        self.widget_strength_slider.value = 0
        self.strength = 0
        self._update_image()

    def next_component(self, _):
        if self.component < self.max_component:
            self.component += 1
            self.widget_comp_slider.value = self.component
            self._update_Xi()
            self.widget_strength_slider.value = 0
            self.strength = 0
            self._update_image()

    def previous_component(self, _):
        if self.component > self.min_component:
            self.component -= 1
            self.widget_comp_slider.value = self.component
            self._update_Xi()
            self.widget_strength_slider.value = 0
            self.strength = 0
            self._update_image()

    def _update_image(self):
        prefVec = self.GANpf.calculate_pref_vector(self.X, self.Xi, self.strength)
        layers_range = self.GANpf.get_comp_layers_range(self.Xi)
        img = self.GANpf.update_image(prefVec=prefVec, layers_range=layers_range)
        self.widget_image.value = self.to_bytes(img)

    def _update_Xi(self):
        self.Xi = np.zeros(self.GANpf.N_comp_in_use)
        self.Xi[self.component] = 1

    @staticmethod
    def to_bytes(img):
        return widget_image_to_bytes(img)








