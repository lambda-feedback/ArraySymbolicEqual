import io
import json
import unittest
from unittest import mock

try:
    from . import evaluation
except ImportError:
    import evaluation

evaluation_function = evaluation.evaluation_function


class TestEvaluationFunctionInvoker(unittest.TestCase):
    """Tests for invoking other functions with the execution role."""

    def make_invoker(self, payload, **extra):
        lambda_client = mock.Mock()
        lambda_client.invoke.return_value = {
            "StatusCode": 200,
            "Payload": io.BytesIO(json.dumps(payload).encode("utf-8")),
            **extra,
        }
        invoker = evaluation.EvaluationFunctionInvoker()
        invoker._client = lambda_client
        return invoker, lambda_client

    def test_import_does_not_create_boto3_client(self):
        with mock.patch.object(evaluation.boto3, "client") as boto3_client:
            evaluation.EvaluationFunctionInvoker()
        boto3_client.assert_not_called()

    def test_uses_default_credentials(self):
        with mock.patch.object(evaluation.boto3, "client") as boto3_client:
            evaluation.EvaluationFunctionInvoker().lambda_client
        # No explicit access keys: boto3 falls back to the execution role.
        boto3_client.assert_called_once_with("lambda")

    def test_returns_result(self):
        invoker, lambda_client = self.make_invoker({"result": {"is_correct": True}})

        result = invoker.invoke("symbolicEqual", "a", "a", params={"x": 1})

        self.assertEqual(result, {"is_correct": True})
        kwargs = lambda_client.invoke.call_args.kwargs
        self.assertEqual(kwargs["FunctionName"], "symbolicEqual")
        self.assertEqual(json.loads(kwargs["Payload"]), {
            "headers": {"command": "eval"},
            "body": {"response": "a", "answer": "a", "params": {"x": 1}},
        })

    def test_error_raises_evaluation_exception(self):
        invoker, _ = self.make_invoker({"error": {"message": "parse failed"}})

        with self.assertRaises(evaluation.EvaluationException) as ctx:
            invoker.invoke("symbolicEqual", "a", "a")
        self.assertEqual(ctx.exception.message, "parse failed")

    def test_function_error_raises(self):
        invoker, _ = self.make_invoker({"errorMessage": "boom"},
                                       FunctionError="Unhandled")

        with self.assertRaises(RuntimeError):
            invoker.invoke("symbolicEqual", "a", "a")


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