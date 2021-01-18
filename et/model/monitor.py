#!/usr/bin/env python3

import math

import numpy as np


class Monitor:

    def __init__(self, w, h, screen, dist, n=5):
        """
        Create Monitor Configuration

        @param w: Screen Width (px)
        @param h: Screen Height (px)
        @param screen: Screen Size (in)
        @param dist: Distance between Subject and Screen (in)
        @param n: number of target points
        """
        self.n = n
        self.w = float(w)
        self.h = float(h)

        r = math.sqrt(self.w * self.w + self.h * self.h)
        self.dpi = r / float(screen)

        self.D = float(dist)

        # get pixels for degree visual angle (10 deg offset for targets)
        deg_offset = 10.0
        dpi_x = self.deg_to_px(deg_offset)
        dx = dpi_x / float(w)
        dy = dpi_x / float(h)

        # the actual (known) locations of the n target points
        # in (0,0) top-left normalized coordinates
        self.S = np.array([
            [0.5, 0.5],  # center
            [0.5 + dx, 0.5 + dy],  # bottom right
            [0.5 - dx, 0.5 + dy],  # bottom left
            [0.5 - dx, 0.5 - dy],  # top left
            [0.5 + dx, 0.5 - dy],  # top right
        ], dtype=float)

        self.n_dict = {
            'center': 0,
            'bottom_right': 1,
            'bottom_left': 2,
            'top_left': 3,
            'top_right': 4
        }

    def deg_to_px(self, deg):
        px = 2 * self.D * math.tan(math.radians(deg / 2.0)) * self.dpi
        return px

    def px_to_deg(self, px):
        r = math.sqrt(self.w * self.w + self.h * self.h)
        # pixel distances coming in are normalized
        px = px * r
        deg = 2 * math.degrees(math.atan2(px / self.dpi, 2 * self.D))
        return deg
