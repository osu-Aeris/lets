import threading

from common.log import logUtils as log
import helpers.s3
import objects.glob


class ThreadScope(threading.local):
    def __init__(self):
        log.debug("Created thread local scope for thread {}".format(threading.get_ident()))
        self._s3 = None
        self._db = None

    @property
    def s3(self):
        if self._s3 is None:
            self._s3 = helpers.s3.clientFactory()
            log.debug("Created a new S3 client for thread {}".format(threading.get_ident()))
        return self._s3

    @property
    def db(self):
        if self._db is None:
            self._db = objects.glob.db.connectionFactory()
            log.debug("Created a new db connection for thread {}".format(threading.get_ident()))
        return self._db

    def dbClose(self):
        tid = threading.get_ident()
        if self._db is None:
            log.debug(
                "Attempted to close a None db connection for thread {} (this thread has no db conn!)".format(tid)
            )
            return
        try:
            self._db.close()
        except Exception as e:
            log.warning("Error ({}) while closing db connection for thread {}. Failing silently.".format(e, tid))
            pass
        log.debug("Closed and destroyed db connection for thread {}".format(tid))
        self._db = None
