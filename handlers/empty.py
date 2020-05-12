import json
import sys
import traceback

import tornado.gen
import tornado.web
from raven.contrib.tornado import SentryMixin

from objects import beatmap
from common.constants import gameModes, mods
from common.log import logUtils as log
from common.web import requestsManager
from constants import exceptions
from helpers import osuapiHelper
from objects import glob
from pp import rippoppai, relaxoppai
from common.sentry import sentry

MODULE_NAME = "api/empty"
class handler(requestsManager.asyncRequestHandler):
	"""
	Handler for /api/v1/pp
	"""
	@tornado.web.asynchronous
	@tornado.gen.engine
	@sentry.captureTornado
	def asyncGet(self):
		statusCode = 200
		data = {"response" : "empty", "status" : 200}
		# Debug output
		log.debug(str(data))
		# Send response
		#self.clear()
		self.write(json.dumps(data))
		self.set_header("Content-Type", "application/json")
		self.set_status(statusCode)
	def asyncPost(self):
		statusCode = 200
		data = {"response" : "empty", "status" : 200}
		# Debug output
		log.debug(str(data))
		# Send response
		#self.clear()
		self.write(json.dumps(data))
		self.set_header("Content-Type", "application/json")
		self.set_status(statusCode)

def calculatePPFromAcc(ppcalc, acc):
	ppcalc.acc = acc
	ppcalc.calculatePP()
	return ppcalc.pp
