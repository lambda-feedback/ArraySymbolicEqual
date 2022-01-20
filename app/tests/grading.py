import unittest

from ..algorithm import grading_function

class TestGradingFunction(unittest.TestCase):
    """
        TestCase Class used to test the algorithm.
        ---
        Tests are used here to check that the algorithm written 
        is working as it should. 
        
        It's best practise to write these tests first to get a 
        kind of 'specification' for how your algorithm should 
        work, and you should run these tests before committing 
        your code to AWS.

        Read the docs on how to use unittest here:
        https://docs.python.org/3/library/unittest.html

        Use grading_function() to check your algorithm works 
        as it should.
    """
    def test_returns_is_correct_true(self):
        response, answer, params = None, None, dict()
        result = grading_function(response, answer, params)
        
        self.assertEqual(result.get("is_correct"), True)

if __name__ == "__main__":
    unittest.main()