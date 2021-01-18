#!/usr/bin/env python3

from .point import Point


class Fixation(Point):

    def __init__(self, x, y, t, d):
        """
        Fixation Object
        @param x:
        @param y:
        @param t:
        @param d:
        """
        Point.__init__(self, x, y, t, "None")
        self.number = 0
        self.duration = d
        self.percentDuration = 0.

    def set_number(self, n):
        self.number = n

    def set_duration(self, d):
        self.duration = d

    def get_number(self):
        return self.number

    def get_duration(self):
        return self.duration

    def get_percent_duration(self):
        return self.percentDuration

    def normalize_duration(self, min_dur, max_dur):
        dur_range = max_dur - min_dur
        if abs(dur_range) < 0.00001:
            if max_dur < 0.00001:
                # assume 0 duration
                self.percentDuration = 0.0
            else:
                # assume 1 fixation only
                self.percentDuration = 1.0
        else:
            self.percentDuration = (self.duration - min_dur) / (dur_range)
