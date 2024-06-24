import numpy as np


class SG:

    def __init__(
        self,
        num_points: int,
        pol_degree: int,
        diff_order: int = 0,
    ):
        """
        Calculates filter coefficients for symmetric savitzky-golay filter
        http://www.nrbook.com/a/bookcpdf/c14-8.pdf

        Args:
            num_points (int): determines window size (2*num_points+1)
            pol_degree (int): degree of the fitted polynomial
            diff_order (int, optional): degree of implicit differentiation (d^n/dt^n)
        """

        # setup interpolation matrix
        # ... you might use other interpolation points
        # and maybe other functions than monomials ....

        x = np.arange(-num_points, num_points + 1, dtype=int)
        monom = lambda x, deg: pow(x, deg)

        A = np.zeros((2 * num_points + 1, pol_degree + 1), dtype=float)
        for i in range(2 * num_points + 1):
            for j in range(pol_degree + 1):
                A[i, j] = monom(x[i], j)

        # calculate diff_order-th row of inv(A^T A)
        ATA = np.dot(A.transpose(), A)
        rhs = np.zeros((pol_degree + 1,), float)
        rhs[diff_order] = (-1) ** diff_order
        wvec = np.linalg.solve(ATA, rhs)

        # calculate filter-coefficients
        self.coeff: np.ndarray = np.dot(A, wvec)

    def apply(
        self,
        window: list,
    ) -> float:
        """applies coefficients calculated to window"""
        res = np.dot(window, self.coeff)
        return res
