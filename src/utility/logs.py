import datetime as dt
import sys
import json
import logging
import logging.config
import atexit
from logging.config import ConvertingList, valid_ident
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
from atexit import register
LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}




def _resolve_handlers(l):
    if not isinstance(l, ConvertingList):
        return l

    # Indexing the list performs the evaluation.
    return [l[i] for i in range(len(l))]


class QueueListenerHandler(QueueHandler):

    def __init__(self, handlers, respect_handler_level=False, auto_run=True, queue=Queue(-1)):
        super().__init__(queue)
        handlers = _resolve_handlers(handlers)
        self._listener = QueueListener(
            self.queue,
            *handlers,
            respect_handler_level=respect_handler_level)
        if auto_run:
            self.start()
            register(self.stop)


    def start(self):
        self._listener.start()


    def stop(self):
        self._listener.stop()


    def emit(self, record):
        return super().emit(record)

class MyJSONFormatter(logging.Formatter):
    def __init__(
        self,
        *,
        fmt_keys: dict[str, str] | None = None,
    ):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    def format(self, record: logging.LogRecord) -> str:
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: logging.LogRecord):
        always_fields = {
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(
                record.created, tz=dt.timezone.utc
            ).isoformat(),
        }
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        message = {
            key: msg_val
            if (msg_val := always_fields.pop(val, None)) is not None
            else getattr(record, val)
            for key, val in self.fmt_keys.items()
        }
        message.update(always_fields)

        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val

        return message
    
from pathlib import Path
LOG_CONFIGURED=False
def setup_logging(env:str="DEV"):
    global LOG_CONFIGURED
    if not LOG_CONFIGURED:
        parent_dir=Path(__file__).parent
        parent_dir.parent.parent.joinpath("logs").mkdir(exist_ok=True)
        if env=="DEV":
            config_file = parent_dir.joinpath("logging_configs","logs_config_file.json") if sys.version_info.minor >=12 else parent_dir.joinpath("logging_configs","logs_config_file_old.json")
        else:
            config_file = parent_dir.joinpath("logging_configs","logs_config_file_prod.json") if sys.version_info.minor >=12 else parent_dir.joinpath("logging_configs","logs_config_file_old_prod.json")
        with open(config_file) as f_in:
            config = json.load(f_in)
        logging.config.dictConfig(config)
        if sys.version_info.minor >=12 :
            queue_handler = logging.getHandlerByName("queue_handler")
            if queue_handler is not None:
                queue_handler.listener.start()
                atexit.register(queue_handler.listener.stop)
        LOG_CONFIGURED=True


