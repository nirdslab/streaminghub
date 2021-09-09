# tests/runner.py
import unittest

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
