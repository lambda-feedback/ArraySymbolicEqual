import unittest
from unittest import mock

from evaluation_function_utils.client import MissingCredentials


def import_evaluation():
    try:
        from . import evaluation
    except ImportError:
        import evaluation
    return evaluation


# The real client needs AWS credentials on creation. Without them, import
# with a mock client so the tests below (which mock the client) can still run.
try:
    evaluation = import_evaluation()
except MissingCredentials:
    with mock.patch("evaluation_function_utils.client.EvaluationFunctionClient"):
        evaluation = import_evaluation()

evaluation_function = evaluation.evaluation_function


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

    def setUp(self):
        patcher = mock.patch.object(evaluation, "client")
        self.client = patcher.start()
        self.addCleanup(patcher.stop)

    def assert_size_feedback(self, response, answer, feedback):
        result = evaluation_function(response, answer, {})

        self.assertEqual(result.get("is_correct"), False)
        self.assertEqual(result.get("feedback"), feedback)
        # Size mismatches are reported before any cell is graded
        self.client.invoke.assert_not_called()

    def test_vector_too_long(self):
        self.assert_size_feedback(
            ["a", "b", "c"], ["a", "b"],
            "Your response has 3 entries, but the expected answer has 2 entries.")

    def test_vector_too_short(self):
        self.assert_size_feedback(
            ["a"], ["a", "b"],
            "Your response has 1 entry, but the expected answer has 2 entries.")

    def test_matrix_wrong_size(self):
        self.assert_size_feedback(
            [["a", "b", "c"], ["d", "e", "f"]], [["a", "b"], ["c", "d"], ["e", "f"]],
            "Your response has 2 rows and 3 columns, but the expected answer has 3 rows and 2 columns.")

    def test_single_expression_for_list(self):
        self.assert_size_feedback(
            "a", ["a", "b"],
            "Your response should be a list of 2 entries, not a single expression.")

    def test_irregular_mismatch(self):
        self.assert_size_feedback(
            [["a"], ["b", "c", "d"]], [["a"], ["b", "c"]],
            "Entry (2) has 3 entries, but should have 2 entries.")

    def test_same_size_is_graded(self):
        self.client.invoke.return_value = {"is_correct": True}

        result = evaluation_function([["a", "b"], ["c", "d"]], [["a", "b"], ["c", "d"]], {})

        self.assertEqual(result.get("is_correct"), True)
        self.assertEqual(self.client.invoke.call_count, 4)

    def test_answer_not_list(self):
        with self.assertRaises(evaluation.EvaluationException):
            evaluation_function(["a"], "a", {})

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