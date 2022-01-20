from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from sympy import expand, simplify, trigsimp, latex
import numpy as np
import re


def batch_replace(string, replacements):
    """
    Utility function executes regex replacements on `string`
    Replacements is a list of lists of strings (n x 2):
        [[ 'pattern', 'replacement' ],
         [ 'pattern', 'replacement' ],
         ... ]
    """
    for pattern, repl in replacements:
        string = re.sub(pattern, repl, string)

    return string


def grade_single_cell(res, ans, params):
    """ 
    Checks if two equations match using SymPy (Copied from SymbolicEqual function)
    (Could be replaced with a call to the actual SymbolicEqual Lambda...)
    """
    # Apply parameters if they exist
    if "str_replacements" in params:
        res = batch_replace(res, params["str_replacements"])

    # Set Sympy allowed transformations depending on if the flag is set
    # False by default
    if params.get("allow_implicit", False):
        transformations = (standard_transformations +
                           (implicit_multiplication_application, ))
    else:
        transformations = standard_transformations

    # Safely try to parse answer and response into symbolic expressions
    try:
        parsed_res = parse_expr(res, transformations=transformations)
    except SyntaxError as e:
        raise SyntaxError("SymPy was unable to parse your response")
    except TypeError as e:
        raise TypeError("SymPy was unable to parse your response")

    try:
        parsed_ans = parse_expr(ans, transformations=transformations)
    except SyntaxError as e:
        raise SyntaxError(
            "SymPy was unable to parse the Answer, contact the question author"
        )
    except TypeError as e:
        raise TypeError(
            "SymPy was unable to parse the Answer, contact the question author"
        )

    # Going from the simplest to complex tranformations available in sympy, check equality
    # https://github.com/sympy/sympy/wiki/Faq#why-does-sympy-say-that-two-equal-expressions-are-unequal
    parsed_res = parsed_res.expand()
    parsed_ans = parsed_ans.expand()
    is_correct = bool(parsed_res == parsed_ans)
    if is_correct:
        return {"is_correct": True, "level": "1"}

    parsed_res = parsed_res.simplify()
    parsed_ans = parsed_ans.simplify()
    is_correct = bool(parsed_res == parsed_ans)
    if is_correct:
        return {"is_correct": True, "level": "2"}

    # Looks for trig identities
    parsed_res = parsed_res.trigsimp()
    parsed_ans = parsed_ans.trigsimp()
    is_correct = bool(parsed_res == parsed_ans)
    if is_correct:
        return {"is_correct": True, "level": "3"}

    return {"is_correct": False}


def recursive_grade(params, response, answer, detailed_feedback, feedback,
                    loc):
    """
    Recursively grade a list of lists of lists ... 
     - detailed_feedback has the same shape of response and answer
     - feedback is a simplified and flattened version, contains a list of
        - 'correct'
        - 'incorrect'
        - 'error at (loc)'
    """
    if isinstance(response, str):
        detailed_feedback = grade_single_cell(response, answer, params)

        if 'is_correct' in detailed_feedback:
            feedback += [
                "correct" if detailed_feedback['is_correct'] else "incorrect"
            ]
        else:  # There was an error
            feedback += [f"{loc}"]

    else:
        for i in range(len(response)):
            df, f = recursive_grade(params, response[i], answer[i], [],
                                    feedback, loc + [i + 1])
            detailed_feedback += [df]
            feedback = f

    return detailed_feedback, feedback


def grading_function(response, answer, params):
    """
    Function used to grade a student response.
    ---
    The handler function passes only one argument to grading_function(), 
    which is a dictionary of the structure of the API request body
    deserialised from JSON.

    The output of this function is what is returned as the API response 
    and therefore must be JSON-encodable. This is also subject to 
    standard response specifications.

    Any standard python library may be used, as well as any package 
    available on pip (provided it is added to requirements.txt).

    The way you wish to structure you code (all in this function, or 
    split into many) is entirely up to you. All that matters are the 
    return types and that grading_function() is the main function used 
    to output the grading response.
    """

    if not (isinstance(response, list) and isinstance(answer, list)):
        raise Exception(
            f"Response area as given {type(response)}, {type(answer)}: types unsupported"
        )

    # Check response and answer have the same shape
    if np.shape(response) != np.shape(answer):
        raise Exception("Response and Answer do not have the same shape")

    # Grade all cells recursively (to allow any shape input)
    detailed_feedback, feedback = recursive_grade(params, response, answer, [],
                                                  [], [])

    # Correct case
    if all(item == "correct" for item in feedback):
        return {
            "is_correct": True,
            "detailed_feedback": detailed_feedback,
        }

    # Case where there was at least 1 parsing error (reported as a location)
    elif any(item[0] == "[" for item in feedback):
        locations = ', '.join([item for item in feedback if item[0] == '['])
        raise Exception(
            f"SymPy was unable to parse your input(s) in: {locations}")

    # There were no errors, and not all items are correct - response is wrong
    else:
        return {
            "is_correct": False,
            "detailed_feedback": detailed_feedback,
        }
