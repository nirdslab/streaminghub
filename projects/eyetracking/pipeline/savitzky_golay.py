#!/usr/bin/env python3

import collections
import math
from typing import List

import numpy as np

from .point import Point


class SG:

  def __init__(self, num_points: int, pol_degree: int, diff_order: int = 0):
    """
    Calculates filter coefficients for symmetric savitzky-golay filter.
    See: U{http://www.nrbook.com/a/bookcpdf/c14-8.pdf}

    @param num_points: M{(2*num_points+1)} values contribute to the smoother.
    @param pol_degree: degree of fitting polynomial.
    @param diff_order: degree of implicit differentiation.
                       0 means that filter results in smoothing of function,
                       1 means that filter results in smoothing the first derivative of function,
                       and so on.
    """

    # setup interpolation matrix

    # ... you might use other interpolation points
    x = np.arange(-num_points, num_points + 1, dtype=int)

    # ... and maybe other functions than monomials
    def monomial(val: int, deg: int):
      return math.pow(val, deg)

    a = np.zeros((2 * num_points + 1, pol_degree + 1), float)
    for i in range(2 * num_points + 1):
      for j in range(pol_degree + 1):
        a[i, j] = monomial(x[i], j)

    # calculate diff_order-th row of inv(A^T A)
    a_trans_a = np.dot(a.transpose(), a)
    rhs = np.zeros((pol_degree + 1,), float)
    rhs[diff_order] = (-1) ** diff_order
    w_vec = np.linalg.solve(a_trans_a, rhs)

    # calculate filter-coefficients
    self.coeff = np.dot(a, w_vec)
    self.n = len(self.coeff)
    self.rb = collections.deque([0.0] * self.n, self.n)

  def smooth(self, signal):
    """ applies coefficients calculated to signal """

    n = int((np.size(self.coeff) - 1) / 2)
    res = np.convolve(signal, self.coeff) if len(signal) > 2 else [0.0] * len(signal)
    return res[n:-n]


def apply_sg_filter(gaze_points: List[Point], window: int, degree: int, diff_order: int):
  sg_x = SG(window, degree, diff_order)
  sg_y = SG(window, degree, diff_order)

  points_x = []
  points_y = []
  t = []
  err = []
  points = []

  for point in gaze_points:
    points_x.append(point.at(0))
    points_y.append(point.at(1))
    t.append(point.get_timestamp())
    err.append(point.get_status())

  dx_dt = sg_x.smooth(points_x)
  dy_dt = sg_y.smooth(points_y)

  for i in range(len(dy_dt)):
    points.append(Point(dx_dt[i], dy_dt[i], t[i], err[i]))

  return points
