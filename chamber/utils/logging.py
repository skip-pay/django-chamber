import copy
import json
import logging
import platform
import traceback

from django.http import UnreadablePostError

from chamber.utils.json import ChamberJSONEncoder


def skip_unreadable_post(record):
    if record.exc_info:
        exc_type, exc_value = record.exc_info[:2]
        if isinstance(exc_value, UnreadablePostError):
            return False
    return True


class AppendExtraJSONHandler(logging.StreamHandler):

    DEFAULT_STREAM_HANDLER_VARIABLE_KEYS = {
        'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 'module', 'exc_info', 'exc_text',
        'stack_info', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
        'processName', 'process',
    }
    CUSTOM_STREAM_HANDLER_VARIABLE_KEYS = {'hostname'}

    def emit(self, record):
        extra = {
            k: v
            for k, v in record.__dict__.items()
            if k not in self.DEFAULT_STREAM_HANDLER_VARIABLE_KEYS.union(self.CUSTOM_STREAM_HANDLER_VARIABLE_KEYS)
        }

        if record.exc_info:
            extra['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'value': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info),
            }

        # The record is shared with every other handler of the logger, and with anything that
        # inspects it after the handlers are done (the Sentry SDK patches Logger.callHandlers and
        # reads the record in its finally block). Mutating it there would strip the exception from
        # those consumers, so the message and exc_info are changed on a copy instead. exc_info is
        # cleared on the copy because the traceback is already serialized into the extras above and
        # would otherwise be printed twice.
        record = copy.copy(record)
        record.exc_info = None
        record.exc_text = None

        record.msg = '{} --- {}'.format(record.msg, json.dumps(extra, cls=ChamberJSONEncoder))

        super().emit(record)


class HostnameFilter(logging.Filter):

    hostname = platform.node()

    def filter(self, record):
        record.hostname = self.hostname
        return True
