import io
import json
import os
import unittest
from unittest import mock

try:
    from . import evaluation
except ImportError:
    import evaluation

evaluation_function = evaluation.evaluation_function


URL = "https://gateway.example.com/default/symbolicEqual"


class TestEvaluationFunctionInvoker(unittest.TestCase):
    """Tests for calling another function over HTTPS."""

    def call(self, body):
        """Invoke with a mocked HTTP response; returns (result, request)."""
        res = mock.MagicMock()
        res.read.return_value = json.dumps(body).encode("utf-8")
        res.__enter__.return_value = res

        with mock.patch.object(evaluation.urllib.request, "urlopen",
                               return_value=res) as urlopen:
            result = evaluation.EvaluationFunctionInvoker().invoke(
                URL, "a", "a", params={"x": 1})
        return result, urlopen.call_args.args[0]

    def test_returns_result(self):
        result, request = self.call(
            {"command": "eval", "result": {"is_correct": True}})

        self.assertEqual(result, {"is_correct": True})
        self.assertEqual(request.full_url, URL)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Command"), "eval")
        self.assertEqual(json.loads(request.data), {
            "response": "a", "answer": "a", "params": {"x": 1},
        })

    def test_error_raises_evaluation_exception(self):
        with self.assertRaises(evaluation.EvaluationException) as ctx:
            self.call({"error": {"message": "parse failed"}})
        self.assertEqual(ctx.exception.message, "parse failed")

    def test_http_error_raises(self):
        error = evaluation.urllib.error.HTTPError(
            URL, 500, "Internal Server Error", {}, io.BytesIO(b""))
        with mock.patch.object(evaluation.urllib.request, "urlopen",
                               side_effect=error):
            with self.assertRaises(RuntimeError):
                evaluation.EvaluationFunctionInvoker().invoke(URL, "a", "a")

    def test_missing_url_raises(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                evaluation.grade_single_cell("a", "a", {})


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

        env = mock.patch.dict(os.environ,
                              {evaluation.SYMBOLIC_EQUAL_URL_ENV: URL})
        env.start()
        self.addCleanup(env.stop)

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

    def test_vector_for_matrix(self):
        self.assert_size_feedback(
            ["a", "b", "c", "d"], [["a", "b"], ["c", "d"]],
            "Your response has 4 entries, but the expected answer has 2 rows and 2 columns.")

    def test_list_for_single_expression(self):
        self.assert_size_feedback(
            ["a", ["b"]], ["a", "b"],
            "Entry (2) should be a single expression, not a list.")

    def test_single_expression_for_list(self):
        self.assert_size_feedback(
            "a", ["a", "b"],
            "Your response should be an array of 2 entries.")

    def test_irregular_mismatch(self):
        self.assert_size_feedback(
            [["a"], ["b", "c", "d"]], [["a"], ["b", "c"]],
            "Entry (2) has 3 entries, but should have 2 entries.")

    def test_same_size_is_graded(self):
        self.client.invoke.return_value = {"is_correct": True}

        result = evaluation_function([["a", "b"], ["c", "d"]], [["a", "b"], ["c", "d"]], {})

        self.assertEqual(result.get("is_correct"), True)
        self.assertEqual(self.client.invoke.call_count, 4)

    def test_same_shape_different_values_is_graded(self):
        self.client.invoke.return_value = {"is_correct": True}

        result = evaluation_function([["a+b", "c"], ["d", "e"]], [["b+a", "c"], ["d", "e"]], {})

        self.assertEqual(result.get("is_correct"), True)
        self.assertEqual(self.client.invoke.call_count, 4)

    def test_answer_not_list(self):
        with self.assertRaises(evaluation.EvaluationException):
            evaluation_function(["a"], "a", {})

    """
    NOTE: These tests call the deployed symbolicEqual function, so they
    can't run in CI without AWS access.

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