import unittest

try:
    from .shape import shape_feedback, regular_shape
except ImportError:
    from shape import shape_feedback, regular_shape


class TestShapeFeedback(unittest.TestCase):

    def test_same_shape(self):
        self.assertIsNone(shape_feedback(["a", "b"], ["c", "d"]))
        self.assertIsNone(shape_feedback([["a"], ["b", "c"]], [["x"], ["y", "z"]]))

    def test_regular_shape(self):
        self.assertEqual(regular_shape(["a", "b", "c"]), (3,))
        self.assertEqual(regular_shape([["a", "b"], ["c", "d"]]), (2, 2))
        self.assertIsNone(regular_shape([["a"], ["b", "c"]]))
        self.assertIsNone(regular_shape(["a", ["b"]]))

    def test_vector_too_long(self):
        self.assertEqual(
            shape_feedback(["a", "b", "c"], ["a", "b"]),
            "Your response has 3 entries, but the expected answer has 2 entries.")

    def test_vector_too_short(self):
        self.assertEqual(
            shape_feedback(["a"], ["a", "b"]),
            "Your response has 1 entry, but the expected answer has 2 entries.")

    def test_matrix_wrong_size(self):
        self.assertEqual(
            shape_feedback([["a", "b", "c"], ["d", "e", "f"]], [["a", "b"], ["c", "d"], ["e", "f"]]),
            "Your response has 2 rows and 3 columns, but the expected answer has 3 rows and 2 columns.")

    def test_vector_for_matrix(self):
        self.assertEqual(
            shape_feedback(["a", "b", "c", "d"], [["a", "b"], ["c", "d"]]),
            "Your response has 4 entries, but the expected answer has 2 rows and 2 columns.")

    def test_single_expression_for_list(self):
        self.assertEqual(
            shape_feedback("a", ["a", "b"]),
            "Your response should be a list of 2 entries, not a single expression.")

    def test_irregular_mismatch_location(self):
        self.assertEqual(
            shape_feedback([["a"], ["b", "c", "d"]], [["a"], ["b", "c"]]),
            "Entry (2) has 3 entries, but should have 2 entries.")
        self.assertEqual(
            shape_feedback(["a", ["b"]], ["a", "b"]),
            "Entry (2) should be a single expression, not a list.")


if __name__ == "__main__":
    unittest.main()
