### Livebox Monitor session module ###
# Interfaces copied/adapted from sysbus package

import os
import json
import tempfile
import pickle
import datetime
import requests
import requests.utils

from src import LmTools


# ################################ VARS & DEFS ################################
APP_NAME = 'so_sdkut'
DEFAULT_TIMEOUT = 5


# ################################ LmSession class ################################

class LmSession:

	### Constructor
	def __init__(self, iUrl, iSessionName = 'LiveboxMonitor'):
		self._url = iUrl
		self._user = ''
		self._password = ''
		self._name = iSessionName
		self._session = None
		self._channelID = 0
		self._sahServiceHeaders = None
		self._sahEventHeaders = None


	### Sign in - return -1 in case of connectivity issue, 0 if sign failed, 1 if sign successful
	def signin(self, iUser, iPassword, iNewSession = False):
		# Set cookie & contextID file path
		aStateFilePath = os.path.join(tempfile.gettempdir(), self._name + '_state')

		LmTools.LogDebug(3, 'State file', aStateFilePath)

		# Close current session if any
		self.close()

		# Save current user/password
		self._user = iUser
		self._password = iPassword

		for i in range(2):
			if not iNewSession and os.path.exists(aStateFilePath):
				LmTools.LogDebug(1, 'Loading saved cookies')

				with open(aStateFilePath, 'rb') as f:
					aCookies = requests.utils.cookiejar_from_dict(pickle.load(f))
					self._session = requests.Session()
					self._channelID = 0
					self._session.cookies = aCookies
					aContextID = pickle.load(f)
			else:
				LmTools.LogDebug(1, 'New session')
				self._session = requests.Session()
				self._channelID = 0

				LmTools.LogDebug(2, 'Authentication')
	 
				aAuth = '{"service":"sah.Device.Information","method":"createContext","parameters":{"applicationName":"%s","username":"%s","password":"%s"}}' % (APP_NAME, iUser, iPassword)

				self._sahServiceHeaders = { 'Accept':'*/*',
											'Authorization':'X-Sah-Login',
											'Content-Type':'application/x-sah-ws-4-call+json' }

				LmTools.LogDebug(2, 'Auth with', str(aAuth))
				try:
					r = self._session.post(self._url + 'ws', data = aAuth, headers = self._sahServiceHeaders, timeout = DEFAULT_TIMEOUT)
				except BaseException as e:
					LmTools.Error('Error: {}'.format(e))
					self._session = None
					return -1
				LmTools.LogDebug(2, 'Auth return', r.text)

				if not 'contextID' in r.json()['data']:
					LmTools.Error('Auth error', str(r.text))
					break

				aContextID = r.json()['data']['contextID']

				# Saving cookie & contextID
				LmTools.LogDebug(1, 'Setting cookies')
				with open(aStateFilePath, 'wb') as f:
					aData = requests.utils.dict_from_cookiejar(self._session.cookies)
					pickle.dump(aData, f, pickle.HIGHEST_PROTOCOL)
					aData = aContextID
					pickle.dump(aData, f, pickle.HIGHEST_PROTOCOL)

			self._sahServiceHeaders = { 'Accept':'*/*',
										'Authorization':'X-Sah ' + aContextID,
										'Content-Type':'application/x-sah-ws-4-call+json; charset=UTF-8',
										'X-Context':aContextID }

			self._sahEventHeaders = { 'Accept':'*/*',
									  'Authorization':'X-Sah ' + aContextID,
									  'Content-Type':'application/x-sah-event-4-call+json; charset=UTF-8',
									  'X-Context':aContextID }

			# Check authentication
			try:
				r = self._session.post(self._url + 'ws', data = '{"service":"Time", "method":"getTime", "parameters":{}}', headers = self._sahServiceHeaders, timeout = DEFAULT_TIMEOUT)
			except BaseException as e:
				LmTools.Error('Error: {}'.format(e))
				LmTools.Error('Authentification check query failed.')
				os.remove(aStateFilePath)
				self.close()
				return -1

			if r.json()['status'] == True:
				return 1
			else:
				os.remove(aStateFilePath)

		LmTools.Error('Authentification failed.')
		return 0


	### Close session
	def close(self):
		if self._session is not None:
			# Fails with access denied error (but same behavior from the web interface...)
			self.request('sah.Device.Information:releaseContext', { 'applicationName': APP_NAME })
			self._session = None
			self._channelID = 0
			self._sahServiceHeaders = None
			self._sahEventHeaders = None


	### Send service request
	def request(self, iPath, iArgs = None, iGet = False, iSilent = False, iTimeout = DEFAULT_TIMEOUT):
		# Check session is established
		if self._session is None:
			if self.signin(self._user, self._password) <= 0:
				return { 'errors' : 'No session' }

		# Build request path
		c = 'sysbus/' + iPath.replace('.', '/')

		if iGet:
			if iArgs is None:
				c += '?_restDepth=-1'
			else:
				c += '?_restDepth='  + str(iArgs)

			LmTools.LogDebug(1, 'Request: %s' % (c))
			aTimeStamp = datetime.datetime.now()
			try:
				t = self._session.get(self._url + c, headers = self._sahServiceHeaders, timeout = iTimeout)
				LmTools.LogDebug(2, 'Request duration: %s' % (datetime.datetime.now() - aTimeStamp))
				t = t.content
				#t = b'[' + t.replace(b'}{', b'},{')+b']'
			except requests.exceptions.Timeout as e:
				if not iSilent:
					LmTools.Error('Request timeout error: {}'.format(e))
				return None
			except BaseException as e:
				if not iSilent:
					LmTools.Error('Request error: {}'.format(e))
				return { 'errors' : 'Request exception' }
		else:
			# Setup request parameters
			aData = { }
			if iArgs is not None:
				aData['parameters'] = iArgs
			else:
				aData['parameters'] = { }

			aSep = c.rfind(':')
			aData['service'] = c[0:aSep].replace('/', '.')
			aData['method'] = c[aSep + 1:]
			c = 'ws'

			# Send request & headers
			LmTools.LogDebug(1, 'Request: %s with %s' % (c, str(aData)))
			aTimeStamp = datetime.datetime.now()
			try:
				t = self._session.post(self._url + c, data = json.dumps(aData), headers = self._sahServiceHeaders, timeout = iTimeout)
				LmTools.LogDebug(2, 'Request duration: %s' % (datetime.datetime.now() - aTimeStamp))
				t = t.content
			except requests.exceptions.Timeout as e:
				if not iSilent:
					LmTools.LogDebug(1, 'Request timeout error: {}'.format(e))
				return None
			except BaseException as e:
				if not iSilent:
					LmTools.Error('Request error: {}'.format(e))
				return { 'errors' : 'Request exception' }

		t = t.decode('utf-8', errors = 'replace')
		if iGet and t.find('}{'):
			LmTools.LogDebug(2, 'Multiple json lists')
			t = '[' + t.replace('}{', '},{') + ']'

		try:
			r = json.loads(t)
		except:
			if not iSilent:
				LmTools.Error('Error:', sys.exc_info()[0])
				LmTools.Error('Bad json:', t)
			return None

		aOverview = str(r)
		if len(aOverview) > 128:
			aOverview = aOverview[:128] + '...'
		LmTools.LogDebug(1, 'Reply:', aOverview)

		if not iGet and 'result' in r:
			r = r['result']
			if 'errors' in r:
				if not iSilent:
					LmTools.Error('Error:', t)
				return None

		LmTools.LogDebug(1, '-------------------------')
		return r


	### Send event request
	def eventRequest(self, iEvents, iSilent = False, iTimeout = DEFAULT_TIMEOUT):
		# Check session is established
		if self._session is None:
			if self.signin(self._user, self._password) <= 0:
				return { 'errors' : 'No session' }

		aData = { }

		aData['events'] = iEvents
		if self._channelID:
			aData['channelid'] = str(self._channelID)
		c = 'ws'

		LmTools.LogDebug(1, 'JSON DUMP: %s' % (str(json.dumps(aData))))

		# Send request & headers
		LmTools.LogDebug(1, 'Request: %s with %s' % (c, str(aData)))
		aTimeStamp = datetime.datetime.now()
		try:
			t = self._session.post(self._url + c, data = json.dumps(aData), headers = self._sahEventHeaders, timeout = iTimeout)
			LmTools.LogDebug(2, 'Request duration: %s' % (datetime.datetime.now() - aTimeStamp))
			t = t.content
		except requests.exceptions.Timeout as e:
			if not iSilent:
				LmTools.LogDebug(1, 'Event request timeout error: {}'.format(e))
			return None
		except BaseException as e:
			if not iSilent:
				LmTools.Error('Event request error: {}'.format(e))
			return { 'errors' : 'Event request exception' }

		t = t.decode('utf-8', errors = 'replace')

		# Remove tailing null if present
		if t.endswith('null'):
			t = t[:-4]

		try:
			r = json.loads(t)
		except:
			if not iSilent:
				LmTools.Error('Error:', sys.exc_info()[0])
				LmTools.Error('Bad json:', t)
			return None

		aOverview = str(r)
		if len(aOverview) > 50:
			aOverview = aOverview[:50] + '...'
		LmTools.LogDebug(1, 'Reply:', aOverview)

		if 'result' in r:
			r = r['result']
			if 'errors' in r:
				if not iSilent:
					LmTools.Error('Error:', t)
				return None

		LmTools.LogDebug(1, '-------------------------')
		self._channelID = r.get('channelid', 0)
		return r
