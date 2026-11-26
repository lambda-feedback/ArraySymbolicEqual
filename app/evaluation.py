import json
import os
import urllib.error
import urllib.request

from evaluation_function_utils.errors import EvaluationException

try:
    from .shape import shape_feedback
except ImportError:
    from shape import shape_feedback

# Base URL of the evaluation function gateway, e.g.
# https://<api-id>.execute-api.eu-west-2.amazonaws.com/default
GATEWAY_URL_ENV = "EVALUATION_FUNCTION_GATEWAY_URL"

# API Gateway HTTP APIs time out after 30 seconds.
REQUEST_TIMEOUT_SECONDS = 30


def environment_suffix():
    """
    Suffix the backend adds to function names outside production
    ("-staging" / "-dev"), taken from this function's own name so calls stay
    within the same environment.
    """
    own_name = os.getenv("AWS_LAMBDA_FUNCTION_NAME", "")
    for suffix in ("-staging", "-dev"):
        if own_name.endswith(suffix):
            return suffix
    return ""


class EvaluationFunctionInvoker:
    """
    Calls other deployed evaluation functions over HTTPS through the public
    evaluation function gateway, the same way any other client does. No AWS
    credentials or IAM permissions are needed.
    """

    def gateway_url(self):
        url = os.getenv(GATEWAY_URL_ENV)
        if not url:
            raise RuntimeError(f"{GATEWAY_URL_ENV} is not set")
        return url.rstrip("/")

    def invoke(self, name, response, answer, params=None):
        url = f"{self.gateway_url()}/{name}{environment_suffix()}"
        data = json.dumps({
            "response": response,
            "answer": answer,
            "params": params or {},
        }).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json", "command": "eval"},
        )

        try:
            with urllib.request.urlopen(
                    request, timeout=REQUEST_TIMEOUT_SECONDS) as res:
                decoded_str = res.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{url} returned HTTP {e.code}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Request to {url} failed: {e.reason}") from e

        try:
            decoded = json.loads(decoded_str)
        except ValueError:
            raise EvaluationException(
                f"Response from the {name} function could not be parsed.",
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
