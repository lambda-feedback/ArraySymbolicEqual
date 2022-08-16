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

    def test_unequal_input_shapes(self):
        response = [["a"]]
        answer = [["a"], ["b"]]

        with self.assertRaises(Exception) as context:
            response = evaluation_function(response, answer, {})

        self.assertEqual(str(context.exception),
                         "Response and Answer do not have the same shape")

    def test_parse_error(self):
        response = ["2x"]
        answer = ["2*x"]

        with self.assertRaises(Exception) as context:
            response = evaluation_function(response, answer, {})

        self.assertEqual(str(context.exception),
                         "SymPy was unable to parse your response")

    def test_vector_correct(self):
        response = ["a + b - a", "2 + c", "d"]
        answer = ["b", "c + 2", "d + 1 - 1 "]

        response = evaluation_function(response, answer, {})

        self.assertEqual(response.get("is_correct"), True)

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
        answer = [["a", "c"], ["b", "d"]]

        response = evaluation_function(response, answer, {})

        self.assertEqual(response.get("is_correct"), False)

    def test_replacement(self):
        response = ["replaceme"]
        answer = ["correct_answer"]
        params = {"str_replacements": [["replaceme", "correct_answer"]]}

        response = evaluation_function(response, answer, params)

        self.assertEqual(response.get("is_correct"), True)

    def test_replacements(self):
        response = ["omega * fr + pi"]
        answer = ["w * f + p"]
        params = {
            "str_replacements": [
                ["omega", "w"],
                ["fr", 'f'],
                ["pi", "p"],
            ]
        }

        response = evaluation_function(response, answer, params)

        self.assertEqual(response.get("is_correct"), True)

    def test_allow_implicit(self):
        response = ["2w"]
        answer = ["2*w"]
        params = {"allow_implicit": True}

        response = evaluation_function(response, answer, params)

        self.assertEqual(response.get("is_correct"), True)

    def test_allow_implicit_multiword(self):
        response = ["2omega"]
        answer = ["2 * omega"]
        params = {"allow_implicit": True}

        response = evaluation_function(response, answer, params)

        self.assertEqual(response.get("is_correct"), True)
    """


if __name__ == "__main__":
    unittest.main()