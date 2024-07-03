# ArraySymbolicEqual

This evaluation function can take any level of nesting for "response" and "answer" fields, as comparison is done recursively (as long as both shapes are identical). Symbolic grading is done using the [SymbolicEqual](https://lambda-feedback.github.io/user-documentation/user_eval_function_docs/symbolicEqual/) function, called using the experimental EvaluationFunctionClient from the evaluation-function-utils library.

## Inputs
This compares cells using the `symbolicEqual` function. Please consult that function's documentation for details on it's allowable parameters, as the ones provided to this function are fed through as they are. 

```json
{
  "response": "<array (of arrays) of strings>",
  "answer": "<array (of arrays) of strings>",
  "params": {
			"Any params accepted by symbolicEqual"
	}
}
```

_Note:_ `response` and `answer` arrays should ultimately have string elements, even though they can have any level of nesting.

## Outputs
Outputs to the `grade` command look like the following:

```json
{
  "command": "eval",
  "result": {
    "is_correct": "<bool>",
    "detailed_feedback": [
      {
        "is_correct": "<bool>",
        "level": "<sympy correctness level>"
      },
      {
        "..."
      }
    ]
  }
}
```

*Note*: The `detailed_feedback` result field is of the same shape as the answer, giving specific information for the correctness of each cell in the evaluated array

## Examples

### Simple Arrays

Correct behaviour
**Input**
```json 
{
  "response": ["a", "b + c"],
  "answer": ["a", "c + b"]
}
```

**Output**
```json 
{
	"command": "eval",
	"result": {
		"is_correct": true,
		"detailed_feedback": [
			{
				"is_correct": true,
				"level": "1"
			},
			{
				"is_correct": true,
				"level": "1"
			}
		]
	}
}
```

Incorrect behaviour
**Input**
```json 
{
  "response": ["a", "b + 2*c"],
  "answer": ["a", "c + b"]
}
```

**Output**
```json 
{
	"command": "eval",
	"result": {
		"is_correct": false,
		"detailed_feedback": [
			{
				"is_correct": true,
				"level": "1"
			},
			{
				"is_correct": false
			}
		]
	}
}
```

