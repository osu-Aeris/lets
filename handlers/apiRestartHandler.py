import json
import tornado
import os
from common.sentry import sentry
from common.web import requestsManager
from objects import glob

class handler(requestsManager.asyncRequestHandler):
	"""
	Handler for /api/v1/status
	"""
	@tornado.web.asynchronous
	@tornado.gen.engine
	@sentry.captureTornado
	def asyncGet(self):
		self.write(json.dumps({"status": 200, "server_status": 1}))
		#self.finish()
		dbkey = glob.conf.config["server"]["adminkey"]
		key = self.get_argument("key")
		if key == dbkey:
			print("> Restarting server")
			os._exit(1)
			
			return True
		else:
			pass