import unittest
import pprint

from ..tools.handler import handler

class TestHandlerFunction(unittest.TestCase):
    def __init__(self, methodName: str):
        super().__init__(methodName=methodName)
        self.__response = None

    def tearDown(self) -> None:
        if self.__response is not None:
            pprint.pprint(self.__response)
        
        self.__response = None

        return super().tearDown()

    def test_handle_bodyless_event(self):
        event = {
            "random": "metadata",
            "without": "a body"
        }

        self.__response = handler(event)
        error = self.__response.get("error")

        self.assertEqual(
            error.get("message"), 
            "No grading data supplied in request body.")

    def test_non_json_body(self):
        event = {
            "random": "metadata",
            "body": "{}}}{{{[][] this is not json."
        }

        self.__response = handler(event)
        error = self.__response.get("error")

        self.assertEqual(
            error.get("message"),
            "Request body is not valid JSON.")

    def test_grade(self):
        event = {
            "random": "metadata",
            "body": {
                "response": "hello",
                "answer": "world!",
                "params": {}
            },
            "headers": {
                "command": "grade"
            }
        }

        self.__response = handler(event)
        self.assertEqual(self.__response.get("command"), "grade")

        result = self.__response.get("result")
        self.assertTrue(result.get("is_correct"))

    def test_grade_no_params(self):
        event = {
            "random": "metadata",
            "body": {
                "response": "hello",
                "answer": "world!"
            }
        }

        self.__response = handler(event)
        self.assertEqual(self.__response.get("command"), "grade")

        result = self.__response.get("result")
        self.assertTrue(result.get("is_correct"))

    def test_healthcheck(self):
        event = {
            "random": "metadata",
            "body": "{}",
            "headers": {
                "command": "healthcheck"
            }
        }

        self.__response = handler(event)
        self.assertEqual(self.__response.get("command"), "healthcheck")

        result = self.__response.get("result")
        self.assertNotEqual(len(result.get("successes")), 0)
        self.assertTrue(result.get("tests_passed"))

    def test_invalid_command(self):
        event = {
            "random": "metadata",
            "body": "{}",
            "headers": {
                "command": "not a command"
            }
        }

        self.__response = handler(event)
        error = self.__response.get("error")
    
        self.assertEqual(
            error.get("message"),
            "Unknown command 'not a command'. Only 'grade' and 'healthcheck' are allowed.")

if __name__ == "__main__":
    unittest.main()