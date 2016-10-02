import score
from common.ripple import userUtils
from constants import rankedStatuses
from objects import glob


class scoreboard:
	def __init__(self, username, gameMode, beatmap, setScores = True, country = False, friends = False, mods = -1):
		"""
		Initialize a leaderboard object

		username -- username of who's requesting the scoreboard. None if not known
		gameMode -- requested gameMode
		beatmap -- beatmap objecy relative to this leaderboard
		setScores -- if True, will get personal/top 50 scores automatically. Optional. Default: True
		"""
		self.scores = []				# list containing all top 50 scores objects. First object is personal best
		self.totalScores = 0
		self.personalBestRank = -1		# our personal best rank, -1 if not found yet
		self.username = username		# username of who's requesting the scoreboard. None if not known
		self.userID = userUtils.getID(self.username)	# username's userID
		self.gameMode = gameMode		# requested gameMode
		self.beatmap = beatmap			# beatmap objecy relative to this leaderboard
		self.country = country
		self.friends = friends
		self.mods = mods
		if setScores:
			self.setScores()


	def setScores(self):
		"""
		Set scores list
		"""

		def buildQuery(params):
			return "{select} {joins} {country} {mods} {friends} {order} {limit}".format(**params)
		# Reset score list
		self.scores = []
		self.scores.append(-1)

		# Make sure the beatmap is ranked
		if self.beatmap.rankedStatus < rankedStatuses.RANKED:
			return

		# Query parts
		select = ""
		joins = ""
		country = ""
		mods = ""
		friends = ""
		order = ""
		limit = ""

		# Find personal best score
		if self.userID != 0:
			# Query parts
			select = "SELECT id FROM scores WHERE userid = %(userid)s AND beatmap_md5 = %(md5)s AND play_mode = %(mode)s AND completed = 3"

			# Mods
			if self.mods > -1:
				mods = "AND mods = %(mods)s"

			# Friends ranking
			if self.friends:
				friends = "AND (scores.userid IN (SELECT user2 FROM users_relationships WHERE user1 = %(userid)s) OR scores.userid = %(userid)s)"

			# Sort and limit at the end
			order = "ORDER BY score DESC"
			limit = "LIMIT 1"

			# Build query, get params and run query
			query = buildQuery(locals())
			params = {"userid": self.userID, "md5": self.beatmap.fileMD5, "mode": self.gameMode, "mods": self.mods}
			personalBestScore = glob.db.fetch(query, params)
		else:
			personalBestScore = None

		# Output our personal best if found
		if personalBestScore is not None:
			s = score.score(personalBestScore["id"])
			self.scores[0] = s
		else:
			# No personal best
			self.scores[0] = -1

		# Get top 50 scores
		select = "SELECT *"
		joins = "FROM scores STRAIGHT_JOIN users ON scores.userid = users.id STRAIGHT_JOIN users_stats ON users.id = users_stats.id WHERE scores.beatmap_md5 = %(beatmap_md5)s AND scores.play_mode = %(play_mode)s AND scores.completed = 3 AND (users.privileges & 1 > 0 OR users.id = %(userid)s)"

		# Country ranking
		if self.country:
			country = "AND users_stats.country = (SELECT country FROM users_stats WHERE id = %(userid)s LIMIT 1)"
		else:
			country = ""

		# Mods ranking
		if self.mods > -1:
			mods = "AND scores.mods = %(mods)s"
		else:
			mods = ""

		# Friends ranking
		if self.friends:
			friends = "AND (scores.userid IN (SELECT user2 FROM users_relationships WHERE user1 = %(userid)s) OR scores.userid = %(userid)s)"
		else:
			friends = ""

		# Sort and limit at the end
		order = "ORDER BY score DESC"
		limit = "LIMIT 50"

		# Build query, get params and run query
		query = buildQuery(locals())
		params = {"beatmap_md5": self.beatmap.fileMD5, "play_mode": self.gameMode, "userid": self.userID, "mods": self.mods}
		topScores = glob.db.fetchAll(query, params)

		# Set data for all scores
		c = 1
		if topScores is not None:
			for i in topScores:
				# Create score object
				s = score.score(i["id"], setData=False)

				# Set data and rank from topScores's row
				s.setDataFromDict(i)
				s.setRank(c)

				# Check if this top 50 score is our personal best
				if s.playerName == self.username:
					self.personalBestRank = c

				# Add this score to scores list and increment rank
				self.scores.append(s)
				c+=1

		'''# If we have more than 50 scores, run query to get scores count
		if c >= 50:
			# Count all scores on this map
			select = "SELECT COUNT(*) AS count"
			limit = "LIMIT 1"

			# Build query, get params and run query
			query = buildQuery(locals())
			count = glob.db.fetch(query, params)
			if count == None:
				self.totalScores = 0
			else:
				self.totalScores = count["count"]
		else:
			self.totalScores = c-1'''

		# If personal best score was not in top 50, try to get it from cache
		if personalBestScore is not None and self.personalBestRank < 1:
			self.personalBestRank = glob.personalBestCache.get(self.userID, self.beatmap.fileMD5, self.country, self.friends, self.mods)

		# It's not even in cache, get it from db
		if personalBestScore is not None and self.personalBestRank < 1:
			self.setPersonalBest()

		# Cache our personal best rank so we can eventually use it later as
		# before personal best rank" in submit modular when building ranking panel
		if self.personalBestRank >= 1:
			glob.personalBestCache.set(self.userID, self.personalBestRank, self.beatmap.fileMD5)

	def setPersonalBest(self):
		"""
		Set personal best rank ONLY
		Ikr, that query is HUGE but xd
		"""
		# Before running the HUGE query, make sure we have a score on that map
		query = "SELECT id FROM scores WHERE beatmap_md5 = %(md5)s AND userid = %(userid)s AND play_mode = %(mode)s AND completed = 3"
		# Mods
		if self.mods > -1:
			query += " AND scores.mods = %(mods)s"
		# Friends ranking
		if self.friends:
			query += " AND (scores.userid IN (SELECT user2 FROM users_relationships WHERE user1 = %(userid)s) OR scores.userid = %(userid)s)"
		# Sort and limit at the end
		query += " LIMIT 1"
		hasScore = glob.db.fetch(query, {"md5": self.beatmap.fileMD5, "userid": self.userID, "mode": self.gameMode, "mods": self.mods})
		if hasScore is None:
			return

		# We have a score, run the huge query
		# Base query
		query = """SELECT COUNT(*) AS rank FROM scores STRAIGHT_JOIN users ON scores.userid = users.id STRAIGHT_JOIN users_stats ON users.id = users_stats.id WHERE scores.score >= (
		SELECT score FROM scores WHERE beatmap_md5 = %(md5)s AND play_mode = %(mode)s AND completed = 3 AND userid = %(userid)s LIMIT 1
		) AND scores.beatmap_md5 = %(md5)s AND scores.play_mode = %(mode)s AND scores.completed = 3 AND users.privileges & 1 > 0"""
		# Country
		if self.country:
			query += " AND users_stats.country = (SELECT country FROM users_stats WHERE id = %(userid)s LIMIT 1)"
		# Mods
		if self.mods > -1:
			query += " AND scores.mods = %(mods)s"
		# Friends
		if self.friends:
			query += " AND (scores.userid IN (SELECT user2 FROM users_relationships WHERE user1 = %(userid)s) OR scores.userid = %(userid)s)"
		# Sort and limit at the end
		query += " ORDER BY score DESC LIMIT 1"
		result = glob.db.fetch(query, {"md5": self.beatmap.fileMD5, "userid": self.userID, "mode": self.gameMode, "mods": self.mods})
		if result is not None:
			self.personalBestRank = result["rank"]

	def getScoresData(self):
		"""
		Return scores data for getscores

		return -- score data in getscores format
		"""
		data = ""

		# Output personal best
		if self.scores[0] == -1:
			# We don't have a personal best score
			data += "\n"
		else:
			# NOTE: wtf is this code?!?!?
			# We have a personal best score
			#if self.personalBestRank == -1:
			#	# ...but we don't know our rank in scoreboard. Get it.
			#	c=1
			#	self.userID = userHelper.getID(self.username)
			#	scores = glob.db.fetchAll("SELECT DISTINCT userid, score FROM scores WHERE beatmap_md5 = %s AND play_mode = %s AND completed = 3 ORDER BY score DESC", [self.beatmap.fileMD5, self.gameMode])
			#	if scores != None:
			#		log.debug("w00t p00t")
			#		for i in scores:
			#			if i["userid"] == self.userID:
			#				self.personalBestRank = c
			#			c+=1

			# Set personal best score rank
			self.setPersonalBest()	# sets self.personalBestRank with the huge query
			self.scores[0].setRank(self.personalBestRank)
			data += self.scores[0].getData(self.username)

		# Output top 50 scores
		for i in self.scores[1:]:
			data += i.getData(self.username)

		return data
