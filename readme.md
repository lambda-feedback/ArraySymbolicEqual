# ArraySymbolicEqual Grading Function
Very similar to the [SymbolicEqual](https://github.com/lambda-feedback/SymbolicEqual) grading function, but grading any list of expressions instead. This algorithm can take any level of nesting for "response" and "answer" fields, as grading is done recursively (as long as both shapes are identical). Symbolic grading is done using the [SymPy](https://docs.sympy.org/latest/index.html) library.
```json
{
  "response": "<array of arrays of strings>",
  "answer": "<array of arrays of strings>",
  "params": {
    "str_replacements": "<number>",
    "allow_implicit": "<bool>"
  }
}
```

_Note:_ `response` and `answer` arrays should ultimately have string elements, even though they can have any level of nesting.

## `str_replacements`
An n by 2 list of lists containing strings, with the following structure:

```json
"str_replacements": [
  ["pattern", "replacement"],
  ["\\d*", "3"], 
]
```
The `pattern` cell can accept any regex string (replacements are done using the python `re` package). Since this is the case, be careful with escaping regex command characters (e.g. the "*" is the wildcard character in regex, if you want to replace it literally, it should be added as "\*")
The `replacement` field can also take regex matched groups from the `pattern`, e.g. the next combo will surroud all digits with pairs of brackets:
```json
"str_replacements": [["(\\d+)", "[$1]"]]
```
**Warning, if only one replacement is needed a list of lists is still required, as shown above**
Please see the python regex docs for more info ([here](https://docs.python.org/3/library/re.html))

## `allow_implicit`

Boolean parameter, when True will allow implicit multiplication when parsing answer and response strings (e.g. `"2x"` instead of `"2*x"`). This is done by adding the sympy `implicit_multiplication_application` transformation to the `parse_expr` function.

*By default this parameter is False*