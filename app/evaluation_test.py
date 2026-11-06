import unittest

from evaluation_function_utils.client import MissingCredentials

try:
    from .evaluation import evaluation_function
except ImportError:
    from evaluation import evaluation_function
except MissingCredentials:
    pass


class TestEvaluationFunction(unittest.TestCase):
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

        Use evaluation_function() to check your algorithm works 
        as it should.
    """

    def test_blank(self):
        self.assertTrue(True)

    """
    NOTE: This function was converted to use the experimental
    EvaluationFunctionClient which doesn't support testing yet.

    def test_vector_incorrect(self):
        response = ["a + b - a", "2 + c", "d"]
        answer = ["b", "c + 2", "d + 1 "]

        response = evaluation_function(response, answer, {})

        self.assertEqual(response.get("is_correct"), False)

    def test_matrix_correct(self):
        response = [["a*2 - a", "c"], ["b", "d"]]
        answer = [["a", "c"], ["b", "d"]]

        response = evaluation_function(response, answer, {})

        self.assertEqual(response.get("is_correct"), True)

    def test_matrix_incorrect(self):
        response = [["a*2 - a", "c"], ["b", "d-d"]]
        answer = [["a", "p"], ["b", "d"]]

        response = evaluation_function(response, answer, {})

        self.assertEqual(response.get("is_correct"), False)

    def test_AA_matrix_partially_correct(self):
        response = [["|a|b|c|", "c"], ["b", "0,5"]]
        answer = [["|a|*b*|c|", "c"], ["b", "0"]]
        params = {"strict_syntax": False}

        response = evaluation_function(response, answer, params)

        self.assertEqual(response.get("is_correct"), False)
    """

if __name__ == "__main__":
    unittest.main()