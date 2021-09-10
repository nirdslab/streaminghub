#!/usr/bin/env python3

import math

from .point import Point


class Butterworth:

  def __init__(self, n, fs, fc):
    """
    Butterworth Filter.
    See: U{http://www.exstrom.com/journal/sigproc/}

    Hollos, Stefan and Hollos, J. Richard, "Recursive Digital Filters:
    A Concise Guise", Exstrom Laboratories, LLC, Longmont, CO, USA
    April, 2014
    ISBN 9781887187244 (ebook)
    URL: http://www.abrazol.com/books/filter1/

    @param n:
    @param fs:
    @param fc:
    """

    self.n = n / 2
    a = math.tan(math.pi * fc / fs)
    a2 = a * a

    self.A = [0.0] * self.n
    self.d1 = [0.0] * self.n
    self.d2 = [0.0] * self.n
    self.w0 = [0.0] * self.n
    self.w1 = [0.0] * self.n
    self.w2 = [0.0] * self.n

    r = 0.0

    for i in range(self.n):
      r = math.sin(math.pi * (2.0 * float(i) + 1.0) / (4.0 * float(self.n)))
      fs = a2 + (2.0 * a * r) + 1.0
      self.A[i] = a2 / fs
      self.d1[i] = 2.0 * (1.0 - a2) / fs
      self.d2[i] = -(a2 - (2.0 * a * r) + 1.0) / fs

  def bw_lpf(self, x):
    """
    Process a stream of x values.
    It updates w0[], w1[], w2[], the filter output memory,
    as it sees incoming values of x.
    For this reason, each stream of data must use its own instance
    of the Butterworth filter

    @param x: just a value
    @return:
    """
    for i in range(self.n):
      self.w0[i] = self.d1[i] * self.w1[i] + self.d2[i] * self.w2[i] + x
      x = self.A[i] * (self.w0[i] + 2.0 * self.w1[i] + self.w2[i])
      self.w2[i] = self.w1[i]
      self.w1[i] = self.w0[i]

    return x


def apply_bw_filter(gaze_points, degree, hertz, cutoff):
  bw_x = Butterworth(degree, hertz, cutoff)
  bw_y = Butterworth(degree, hertz, cutoff)

  points = []

  for point in gaze_points:
    x = bw_x.bw_lpf(point.at(0))
    y = bw_y.bw_lpf(point.at(1))
    t = point.get_timestamp()
    err = point.get_status()
    points.append(Point(x, y, t, err))

  return points
