import io
import json
import logging

from django.test import TestCase
from germanium.tools import assert_equal, assert_true, assert_in  # pylint: disable=E0401

from chamber.utils.logging import AppendExtraJSONHandler


class AppendExtraJSONHandlerTestCase(TestCase):
    def setUp(self):
        self.stream = io.StringIO()
        self.handler = AppendExtraJSONHandler(self.stream)
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = [self.handler]
        self.logger.propagate = False

    def tearDown(self):
        self.logger.handlers = []

    def _get_logged_output(self):
        return self.stream.getvalue().strip()

    def _parse_extra_json(self, log_output):
        # Format: "message --- {json}"
        if " --- " in log_output:
            json_part = log_output.split(" --- ", 1)[1]
            return json.loads(json_part)
        return {}

    def test_basic_logging_without_extra(self):
        self.logger.info("Basic message")
        output = self._get_logged_output()
        assert_in("Basic message", output)
        extra = self._parse_extra_json(output)
        assert_equal(extra, {})

    def test_logging_with_extra_fields(self):
        self.logger.info(
            "Message with extras", extra={"user_id": 123, "action": "login"}
        )
        output = self._get_logged_output()

        assert_in("Message with extras", output)
        extra = self._parse_extra_json(output)
        assert_equal(extra["user_id"], 123)
        assert_equal(extra["action"], "login")

    def test_logging_with_exception_info(self):
        try:
            raise ValueError("Test exception")
        except ValueError:
            self.logger.error("Error occurred", exc_info=True)

        output = self._get_logged_output()
        assert_in("Error occurred", output)

        extra = self._parse_extra_json(output)
        assert_in("exception", extra)
        assert_equal(extra["exception"]["type"], "ValueError")
        assert_equal(extra["exception"]["value"], "Test exception")
        assert_true(isinstance(extra["exception"]["traceback"], list))
        assert_true(len(extra["exception"]["traceback"]) > 0)
        assert_in("ValueError: Test exception", "".join(extra["exception"]["traceback"]))

    def test_logging_with_exception_and_extra_fields(self):
        try:
            raise RuntimeError("Something went wrong")
        except RuntimeError:
            self.logger.error(
                "Error with context", exc_info=True, extra={"request_id": "abc123"}
            )

        output = self._get_logged_output()
        extra = self._parse_extra_json(output)

        # Check exception info
        assert_in("exception", extra)
        assert_equal(extra["exception"]["type"], "RuntimeError")
        assert_equal(extra["exception"]["value"], "Something went wrong")

        # Check extra fields
        assert_equal(extra["request_id"], "abc123")
