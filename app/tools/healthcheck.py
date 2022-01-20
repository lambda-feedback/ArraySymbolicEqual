import unittest
import time
import os
import sys

from .. import tests

"""
    Extension of the default TestResult class with timing information.
"""

class HealthcheckResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_timings = []

    def startTest(self, test):
        self._start_time = time.time()
        super().startTest(test)

    def addSuccess(self, test):
        elapsed_time_s = time.time() - self._start_time
        elapsed_time_us = round(1000000 * elapsed_time_s)
        self.test_timings.append((test.id(), elapsed_time_us))

        super().addSuccess(test)

    def getTestTimings(self):
        return self.test_timings

"""
    Extension of the default TestRunner class that returns a JSON-encodable result
"""

class HealthcheckRunner(unittest.TextTestRunner):
    def __init__(self, *args, **kwargs):
        return super().__init__(resultclass=HealthcheckResult, *args, **kwargs)
    
    def run(self, test):
        """
        Extension to the original run method that returns the results in a JSON-encodable format.
        ---
        This includes:
            - `tests_passed` (bool): Whether all tests were successful.
            - `successes` (list): A list of all passing tests, including the name and
                time taken to complete in microseconds.
            - `failures` (list): A list of all tests that failed, including the name and
                traceback of failures.
            - `errors` (list): A list of all tests that caused an error, including the
                name and traceback of failures.
        """
        result = super().run(test)

        results = {
            "tests_passed": result.wasSuccessful(),
            "successes": [{"name": n, "time": t} for (n, t) in result.getTestTimings()], 
            "failures": [{"name": i.id()} for (i, _) in result.failures], 
            "errors": [{"name": i.id()} for (i, _) in result.errors]
        }

        return results

def healthcheck() -> dict:
    """
    Function used to return the results of the unittests in a JSON-encodable format.
    ---
    Therefore, this can be used as a healthcheck to make sure the algorithm is 
    running as expected, and isn't taking too long to complete due to, e.g., issues 
    with load balancing.
    """
    # Redirect stderr stream to a null stream so the unittests are not logged on the console.
    no_stream = open(os.devnull, 'w')
    sys.stderr = no_stream

    # Create a test loader and test runner instance
    loader = unittest.TestLoader()

    request_tests = loader.loadTestsFromTestCase(tests.TestRequestValidation)
    response_tests = loader.loadTestsFromTestCase(tests.TestResponseValidation)
    grading_tests = loader.loadTestsFromTestCase(tests.TestGradingFunction)

    suite = unittest.TestSuite([request_tests, response_tests, grading_tests])
    runner = HealthcheckRunner(verbosity=0)

    result = runner.run(suite)

    # Reset stderr and close the null stream
    sys.stderr = sys.__stderr__
    no_stream.close()

    return result