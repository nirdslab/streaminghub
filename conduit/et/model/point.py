#!/usr/bin/env python3

class Point:

    def __init__(self, x, y, t, err):
        """
        This class represents a gaze point

        @param x:
        @param y:
        @param t:
        @param err:
        """
        self.error = err
        self.timestamp = t

        self.coord = []
        self.coord.append(x)
        self.coord.append(y)

    def at(self, k):
        """
        index into the coords of this Point

        @param k: x if 0, y if 1
        @return: coordinate
        """
        return self.coord[k]

    def set(self, x, y):
        """
        set coords

        @param x:
        @param y:
        """
        self.coord[0] = x
        self.coord[1] = y

    def get_status(self):
        """
        Get error status of point

        @return:
        """
        return self.error

    def valid(self):
        """
        a gaze point is valid if it's normalized coordinates are in the range [0,1] and both eyes are present

        @return:
        """
        if self.error == "None" and \
                self.coord[0] > 0 and self.coord[1] > 0 and \
                self.coord[0] < 1 and self.coord[1] < 1:
            return True
        else:
            return False

    def get_timestamp(self):
        return self.timestamp
