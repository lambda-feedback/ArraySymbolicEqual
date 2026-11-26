import json

import boto3
from evaluation_function_utils.errors import EvaluationException

try:
    from .shape import shape_feedback
except ImportError:
    from shape import shape_feedback


class EvaluationFunctionInvoker:
    """
    Invokes other deployed evaluation functions via the AWS Lambda API.

    Credentials come from boto3's default chain, which on Lambda is the
    function's execution role. That role needs lambda:InvokeFunction on the
    functions being called. No access keys are read or required.
    """

    def __init__(self):
        self._client = None

    @property
    def lambda_client(self):
        # Created lazily so importing this module needs no AWS config.
        if self._client is None:
            self._client = boto3.client("lambda")
        return self._client

    def invoke(self, name, response, answer, params=None):
        payload = json.dumps({
            "headers": {"command": "eval"},
            "body": {
                "response": response,
                "answer": answer,
                "params": params or {},
            },
        })

        res = self.lambda_client.invoke(FunctionName=name,
                                        Payload=payload,
                                        InvocationType="RequestResponse")

        if res.get("StatusCode") != 200 or "FunctionError" in res:
            raise RuntimeError(
                f"{name} invocation failed: StatusCode={res.get('StatusCode')}, "
                f"FunctionError={res.get('FunctionError')}")

        decoded_str = res["Payload"].read().decode("utf-8")
        try:
            decoded = json.loads(decoded_str)
        except ValueError:
            raise EvaluationException(
                f"Payload response from the {name} function could not be parsed.",
                raw_response=decoded_str)

        # Re-raise evaluation errors as if the function was run locally.
        if "error" in decoded:
            raise EvaluationException(**decoded["error"])

        if "result" in decoded:
            return decoded["result"]

        raise EvaluationException(
            f"The {name} evaluation function did not return an error or a result.",
            raw_response=decoded)


client = EvaluationFunctionInvoker()


def grade_single_cell(res, ans, params):
    """
    Attempt to grade a single cell using the SymbolicEqual function, 
    fallback to a local version if the request fails
    """
    try:
        return client.invoke('symbolicEqual', res, ans, params=params)
    except EvaluationException as e:
        return e.error_dict

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
        if not isinstance(answer, str):
            raise EvaluationException(
                "Response and Answer do not have the same shape", loc=str(loc))

        detailed_feedback = grade_single_cell(response, answer, params)

        if 'is_correct' in detailed_feedback:
            feedback += [
                ("correct" if detailed_feedback['is_correct'] else "incorrect",loc)
            ]
        else:  # There was an error
            feedback += [f"{loc}"]

    else:
        # Response is not a string, if answer is then there's a shape mismatch
        if not isinstance(answer, list):
            raise EvaluationException(
                "Response and Answer do not have the same shape", loc=str(loc))

        for i in range(len(response)):

            df, f = recursive_grade(params, response[i], answer[i], [],
                                    feedback, loc + [i + 1])

            detailed_feedback += [df]
            feedback = f

    return detailed_feedback, feedback


def evaluation_function(response, answer, params):
    """
    Function used to grade a student response.
    ---
    The handler function passes only one argument to evaluation_function(), 
    which is a dictionary of the structure of the API request body
    deserialised from JSON.

    The output of this function is what is returned as the API response 
    and therefore must be JSON-encodable. This is also subject to 
    standard response specifications.

    Any standard python library may be used, as well as any package 
    available on pip (provided it is added to requirements.txt).

    The way you wish to structure you code (all in this function, or 
    split into many) is entirely up to you. All that matters are the 
    return types and that evaluation_function() is the main function used 
    to output the grading response.
    """

    if not isinstance(answer, list):
        raise EvaluationException(
            f"Answer given of type {type(answer)}: type unsupported"
        )

    # Give feedback on a size/shape mismatch rather than failing during grading
    size_feedback = shape_feedback(response, answer)
    if size_feedback is not None:
        return {
            "is_correct": False,
            "feedback": size_feedback
        }

    # Grade all cells recursively (to allow any shape input)
    detailed_feedback, feedback = recursive_grade(params, response, answer, [],
                                                  [], [])

    remark = ""

    row_format = lambda x: "Entry "+str(x[1][1])
    col_format = lambda x: "Entry "+str(x[1][0])
    table_format = lambda x: "Entry on row "+str(x[1][0])+", column "+str(x[1][1])
    general_format = lambda x: "Entry ("+"".join([str(i) for i in x[1][0:-1]+","])+str(x[1][-1])+")"

    feedback_format = general_format

    if all([len(x) == 1 for x in answer]) or all([not isinstance(x,list) for x in answer]):
        feedback_format = col_format
    elif len(answer) == 1 and all([not isinstance(x,list) for x in answer[0]]):
        feedback_format = row_format
    elif len(answer) > 1 and\
         all([isinstance(elem,list) for elem in answer]) and\
         all([len(elem) == len(answer[0]) for elem in answer]):
        feedback_format = table_format
    for item in feedback:
        content = detailed_feedback[item[1][0]-1]
        for k in range(1,len(item[1])):
            content = content[item[1][k]-1]
        if "feedback" in content.keys():
            separator = "" if len(remark) == 0 else "<br />"
            current_feedback = content["feedback"]
            if item[0] == 'incorrect':
                feedback_message_incorrect = ""  #"Does not match expected value. "
                current_feedback = feedback_message_incorrect+current_feedback
            if len(current_feedback.strip()) > 0:
                remark += separator+feedback_format(item)+": "+current_feedback

    # Correct case
    if all(item[0] == "correct" for item in feedback):
        return {
            "is_correct": True,
            "detailed_feedback": detailed_feedback,
            "feedback": remark
        }
    # Case where there was at least 1 parsing error (reported as a location)
    elif any(item[0] == "[" for item in feedback):
        locations = ', '.join([item for item in feedback if item[0] == '['])
        raise EvaluationException(
            f"symbolicEqual was unable to parse your input(s) in: {locations}",
            detailed_feedback=detailed_feedback)

    # There were no errors, and not all items are correct - response is wrong
    else:
        return {
            "is_correct": False,
            "detailed_feedback": detailed_feedback,
            "feedback": remark
        }
