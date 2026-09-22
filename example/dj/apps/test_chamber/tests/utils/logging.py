import io
import json
import logging
import sys

from django.test import TestCase
from germanium.tools import assert_equal, assert_true, assert_in  # pylint: disable=E0401

from chamber.utils.logging import AppendExtraJSONHandler


__all__ = ("AppendExtraJSONHandlerTestCase",)


class AppendExtraJSONHandlerTestCase(TestCase):
    DEFAULT_LOGGER_ATTRS = []

    def setUp(self):
        self.stream = io.StringIO()
        self.handler = AppendExtraJSONHandler(self.stream)
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = [self.handler]
        self.logger.propagate = False

        if sys.version_info >= (3, 12):
            # taskName added in python 3.12
            self.DEFAULT_LOGGER_ATTRS.append("taskName")

    def tearDown(self):
        self.logger.handlers = []

    def _get_logged_output(self):
        return self.stream.getvalue().strip()

    def _parse_extra_json(self, log_output):
        # Format: "message --- {json}"
        if " --- " in log_output:
            json_part = log_output.split(" --- ", 1)[1]
            json_dict = json.loads(json_part)
            return {k: v for (k, v) in json_dict.items() if k not in self.DEFAULT_LOGGER_ATTRS}
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

    def test_record_should_not_be_modified_by_the_handler(self):
        records = []

        class RecordingHandler(logging.Handler):
            def emit(self, record):
                records.append(record)

        # A handler must not modify the record: it is shared with the other handlers of the logger
        # and with anything inspecting it afterwards, such as the Sentry SDK.
        self.logger.handlers = [self.handler, RecordingHandler()]
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()
            self.logger.error("Error occurred", exc_info=True)

        assert_in("ValueError: Test exception", self._get_logged_output())

        record = records[0]
        assert_equal(record.exc_info, exc_info)
        assert_equal(record.msg, "Error occurred")

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
