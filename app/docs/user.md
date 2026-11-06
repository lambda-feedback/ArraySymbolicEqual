# ArraySymbolicEqual 

This function compares two symbolic expression arrays, with any level of nesting (2D, 3D, irregular shape, ...). Each cell is compared using the [`SymbolicEqual`](https://lambda-feedback.github.io/user-documentation/user_eval_function_docs/symbolicEqual/) evaluation function.

## Inputs
This function support all input parameters that [`SymbolicEqual`](https://lambda-feedback.github.io/user-documentation/user_eval_function_docs/symbolicEqual/) uses.

## Size mismatches
If the response does not have the same size or shape as the answer (e.g. too many or too few entries, or a list where a single expression was expected), the response is marked incorrect and the feedback explains the difference, e.g. "Your response has 2 rows and 3 columns, but the expected answer has 3 rows and 2 columns." No cells are graded in this case.
