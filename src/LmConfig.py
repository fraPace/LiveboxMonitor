### Livebox Monitor Configuration module ###

import sys
import os
import platform
import requests
import json
import base64

from enum import IntEnum

from PyQt6 import QtGui
from PyQt6 import QtCore
from PyQt6 import QtWidgets
from cryptography.fernet import Fernet

from src import LmTools


# ################################ VARS & DEFS ################################

# Config file name
CONFIG_FILE = 'Config.txt'

# Config default
LIVEBOX_URL = 'http://livebox.home/'
LIVEBOX_USER = 'admin'
LIVEBOX_PASSWORD = ''
FILTER_DEVICES = True
MACADDR_TABLE_FILE = 'MacAddrTable.txt'
MACADDR_API_KEY = ''

# Static config
ICON_URL = 'assets/common/images/app_conf/'
SECRET = 'mIohg_8Q0pkQCA7x3dOqNTeADYPfcMhJZ4ujomNLNro='

# Graphical config
WIND_HEIGHT_ADJUST = 0
DIAG_HEIGHT_ADJUST = 0
DUAL_PANE_ADJUST = 0
LIST_HEADER_HEIGHT = 30
LIST_LINE_HEIGHT = 30
LIST_STYLESHEET = ''
LIST_HEADER_STYLESHEET = ''

# Interfaces
NET_INTF = []

# LB5 Interfaces
NET_INTF_LB5 = [
	{ 'Key': 'veip0',    'Name': 'Fiber',        'Type': 'ont', 'SwapStats': False },
	{ 'Key': 'bridge',   'Name': 'LAN',          'Type': 'lan', 'SwapStats': True  },
	{ 'Key': 'eth0',     'Name': 'Ethernet 1',   'Type': 'eth', 'SwapStats': True  },
	{ 'Key': 'eth1',     'Name': 'Ethernet 2',   'Type': 'eth', 'SwapStats': True  },
	{ 'Key': 'eth2',     'Name': 'Ethernet 3',   'Type': 'eth', 'SwapStats': True  },
	{ 'Key': 'eth3',     'Name': 'Ethernet 4',   'Type': 'eth', 'SwapStats': True  },
	{ 'Key': 'wl0',      'Name': 'Wifi 2.4GHz',  'Type': 'wif', 'SwapStats': True  },
	{ 'Key': 'eth4',     'Name': 'Wifi 5GHz',    'Type': 'wif', 'SwapStats': True  },
	{ 'Key': 'wlguest2', 'Name': 'Guest 2.4GHz', 'Type': 'wig', 'SwapStats': True  },
	{ 'Key': 'wlguest5', 'Name': 'Guest 5GHz',   'Type': 'wig', 'SwapStats': True  }
]

# LB6 Interfaces
NET_INTF_LB6 = [
	{ 'Key': 'veip0',        'Name': 'Fiber',        'Type': 'ont', 'SwapStats': False },
	{ 'Key': 'bridge',       'Name': 'LAN',          'Type': 'lan', 'SwapStats': True  },
	{ 'Key': 'ETH1',         'Name': 'Ethernet 1',   'Type': 'eth', 'SwapStats': True  },
	{ 'Key': 'ETH2',         'Name': 'Ethernet 2',   'Type': 'eth', 'SwapStats': True  },
	{ 'Key': 'ETH3',         'Name': 'Ethernet 3',   'Type': 'eth', 'SwapStats': True  },
	{ 'Key': 'ETH4',         'Name': 'Ethernet 4',   'Type': 'eth', 'SwapStats': True  },
	{ 'Key': 'ETH0',         'Name': 'Ether 2.5G',   'Type': 'eth', 'SwapStats': True  },
	{ 'Key': 'vap2g0priv0',  'Name': 'Wifi 2.4GHz',  'Type': 'wif', 'SwapStats': True  },
	{ 'Key': 'vap5g0priv0',  'Name': 'Wifi 5GHz',    'Type': 'wif', 'SwapStats': True  },
	{ 'Key': 'vap6g0priv0',  'Name': 'Wifi 6GHz',    'Type': 'wif', 'SwapStats': True  },
	{ 'Key': 'vap2g0guest0', 'Name': 'Guest 2.4GHz', 'Type': 'wig', 'SwapStats': True  },
	{ 'Key': 'vap5g0guest0', 'Name': 'Guest 5GHz',   'Type': 'wig', 'SwapStats': True  }
]

# Interface name mapping
INTF_NAME_MAP = []

# LB5 Interface name mapping
INTF_NAME_MAP_LB5 = {
	"Livebox":  {"eth0":"Eth1", "eth1":"Eth2", "eth2":"Eth3", "eth3":"Eth4"},
	"Repeater": {"eth0":"Eth1", "eth1":"Eth2"}
}

# LB6 Interface name mapping
INTF_NAME_MAP_LB6 = {
	"Livebox":  {"eth0":"Eth4", "eth1":"Eth3", "eth2":"Eth2", "eth3":"Eth1", "eth4":"Eth2.5G"},
	"Repeater": {"eth0":"Eth1", "eth1":"Eth2"}
}

# Device types & icons
DEVICE_TYPES = [
	{ 'Key': 'Unknown',                     'Name': 'Unknown',                    'Icon': 'e_default_device.png' },
	{ 'Key': 'AC Outlet',                   'Name': 'AC Outlet',                  'Icon': 'e_smart_plug.png' },
	{ 'Key': 'Acces Point',                 'Name': 'Acces Point',                'Icon': 'e_pointacceswifi.png' },
	{ 'Key': 'Airbox',                      'Name': 'Airbox',                     'Icon': 'e_airbox_gen.png' },
	{ 'Key': 'Apple AirPort',               'Name': 'Apple AirPort',              'Icon': 'e_apple_express.png' },
	{ 'Key': 'Apple AirPort Time Capsule',  'Name': 'Apple AirPort Time Capsule', 'Icon': 'e_apple_extreme_capsule.png' },
	{ 'Key': 'Apple Time Capsule',          'Name': 'Apple Time Capsule',         'Icon': 'e_apple_extreme_capsule.png' },
	{ 'Key': 'Apple TV',                    'Name': 'Apple TV',                   'Icon': 'e_apple_tv.png' },
	{ 'Key': 'Chromecast',                  'Name': 'Chromecast',                 'Icon': 'e_chromecast.png' },
	{ 'Key': 'Desktop',                     'Name': 'Computer',                   'Icon': 'e_ordibureau.png' },
	{ 'Key': 'Desktop Linux',               'Name': 'Computer (Linux)',           'Icon': 'e_ordibureau_Linux.png' },
	{ 'Key': 'Desktop iOS',                 'Name': 'Computer (MacOS)',           'Icon': 'e_ordibureau_ios.png' },
	{ 'Key': 'Desktop Windows',             'Name': 'Computer (Windows)',         'Icon': 'e_ordibureau_windows.png' },
	{ 'Key': 'Game Console',                'Name': 'Console',                    'Icon': 'e_consolejeux.png' },
	{ 'Key': 'Dimmable Color Bulb',         'Name': 'Dimmer Light',               'Icon': 'e_smart_bulb.png' },
	{ 'Key': 'Djingo Speaker',              'Name': 'Djingo Speaker',             'Icon': 'e_djingospeaker.png' },   # Not (yet?) supported by LB5
	{ 'Key': 'Domestic Robot',              'Name': 'Domestic Robot',             'Icon': 'e_Homelive.png' },
	{ 'Key': 'Domino',                      'Name': 'Domino',                     'Icon': 'e_domino.png' },
	{ 'Key': 'Door Sensor',                 'Name': 'Door Sensor',                'Icon': 'e_door_sensor.png' },
	{ 'Key': 'ExtenderTV',                  'Name': 'Extender TV',                'Icon': 'e_liveplugsolo.png' },
	{ 'Key': 'ExtenderWiFiPlus',            'Name': 'Extender Wi-Fi Plus',        'Icon': 'e_pointacceswifi.png' },
	{ 'Key': 'Femtocell',                   'Name': 'Femtocell',                  'Icon': 'e_femtocell.png' },
	{ 'Key': 'Google OnHub',                'Name': 'Google OnHub',               'Icon': 'e_google_onhub.png' },
	{ 'Key': 'HiFi',                        'Name': 'HiFi',                       'Icon': 'e_enceinte_hifi.png' },
	{ 'Key': 'HomeLibrary',                 'Name': 'Home Library',               'Icon': 'e_homelibrary.png' },
	{ 'Key': 'HomeLive',                    'Name': 'Home Live',                  'Icon': 'e_Homelive.png' },
	{ 'Key': 'Homepoint',                   'Name': 'Home Point',                 'Icon': 'e_homepoint.png' },
	{ 'Key': 'IP Camera',                   'Name': 'IP Camera',                  'Icon': 'e_camera_ip.png' },
	{ 'Key': 'Laptop',                      'Name': 'Laptop',                     'Icon': 'e_ordiportable.png' },
	{ 'Key': 'Laptop iOS',                  'Name': 'Laptop (iOS)',               'Icon': 'e_ordiportable_ios.png' },
	{ 'Key': 'Laptop Linux',                'Name': 'Laptop (Linux)',             'Icon': 'e_ordiportable_Linux.png' },
	{ 'Key': 'Laptop Windows',              'Name': 'Laptop (Windows)',           'Icon': 'e_ordiportable_windows.png' },
	{ 'Key': 'leBloc',                      'Name': 'Le Bloc d\'Orange',          'Icon': 'e_leblocdorange.png' },
	{ 'Key': 'HomePlug',                    'Name': 'Liveplug',                   'Icon': 'e_liveplug_cpl.png' },
	{ 'Key': 'LivePlugWifi',                'Name': 'Liveplug solo Wi-Fi',        'Icon': 'e_liveplugsolo.png' },
	{ 'Key': 'WiFiExtender',                'Name': 'Liveplug Wi-Fi Extender',    'Icon': 'e_liveplug_extender.png' },
	{ 'Key': 'Liveradio',                   'Name': 'LiveRadio',                  'Icon': 'e_liveradio.png' },
	{ 'Key': 'Motion Sensor',               'Name': 'Motion Sensor',              'Icon': 'e_motion_sensor.png' },
	{ 'Key': 'Nas',                         'Name': 'NAS',                        'Icon': 'e_nas.png' },
	{ 'Key': 'Notebook',                    'Name': 'Notebook',                   'Icon': 'e_notebook.png' },
	{ 'Key': 'Notebook Linux',              'Name': 'Notebook (Linux)',           'Icon': 'e_notebook_Linux.png' },
	{ 'Key': 'Notebook Windows',            'Name': 'Notebook (Windows)',         'Icon': 'e_notebook_windows.png' },
	{ 'Key': 'Old Phone',                   'Name': 'Old Handset Phone',          'Icon': 'e_telephoneold.png' },
	{ 'Key': 'Phone',                       'Name': 'Phone',                      'Icon': 'e_telephonenew.png' },
	{ 'Key': 'Power Meter',                 'Name': 'Power Meter',                'Icon': 'e_smart_plug.png' },
	{ 'Key': 'Printer',                     'Name': 'Printer',                    'Icon': 'e_imprimante.png' },
	{ 'Key': 'Set-top Box',                 'Name': 'Set-top Box',                'Icon': 'e_decodeurTV.png' },
	{ 'Key': 'Set-top Box TV 4',            'Name': 'Set-top Box 4',              'Icon': 'e_decodeur_tv_4.png' },
	{ 'Key': 'Set-top Box TV Play',         'Name': 'Set-top Box Play',           'Icon': 'e_decodeur_tv_play.png' },
	{ 'Key': 'Set-top Box TV UHD',          'Name': 'Set-top Box UHD',            'Icon': 'e_decodeur_tv_uhd.png' },
	{ 'Key': 'Set-top Box TV Universal',    'Name': 'Set-top Box Universal',      'Icon': 'e_decodeur_tv_universel.png' },
	{ 'Key': 'Simple Button',               'Name': 'Simple Button',              'Icon': 'e_simple_button.png' },
	{ 'Key': 'Color Bulb',                  'Name': 'Smart Bulb',                 'Icon': 'e_smart_bulb.png' },
	{ 'Key': 'Smart Plug',                  'Name': 'Smart Plug',                 'Icon': 'e_smart_plug.png' },
	{ 'Key': 'Mobile',                      'Name': 'Smartphone',                 'Icon': 'e_mobile.png' },
	{ 'Key': 'Mobile Android',              'Name': 'Smartphone (Android)',       'Icon': 'e_mobile_android.png' },
	{ 'Key': 'Mobile iOS',                  'Name': 'Smartphone (iOS)',           'Icon': 'e_mobile_ios.png' },
	{ 'Key': 'Mobile Windows',              'Name': 'Smartphone (Windows)',       'Icon': 'e_mobile_windows.png' },
	{ 'Key': 'Smoke Detector',              'Name': 'Smoke Detector',             'Icon': 'e_sensorhome.png' },
	{ 'Key': 'Disk',                        'Name': 'Storage Device',             'Icon': 'e_periphstockage.png' },
	{ 'Key': 'Switch4',                     'Name': 'Switch (4 ports)',           'Icon': 'e_switch4.png' },
	{ 'Key': 'Switch8',                     'Name': 'Switch (8 ports)',           'Icon': 'e_switch8.png' },
	{ 'Key': 'Tablet',                      'Name': 'Tablet',                     'Icon': 'e_tablette.png' },
	{ 'Key': 'Tablet Android',              'Name': 'Tablet (Android)',           'Icon': 'e_tablette_android.png' },
	{ 'Key': 'Tablet iOS',                  'Name': 'Tablet (iOS)',               'Icon': 'e_tablette_ios.png' },
	{ 'Key': 'Tablet Windows',              'Name': 'Tablet (Windows)',           'Icon': 'e_tablette_windows.png' },
	{ 'Key': 'TV',                          'Name': 'TV',                         'Icon': 'e_TV.png' },
	{ 'Key': 'TVKey',                       'Name': 'TV Stick',                   'Icon': 'e_cletv.png' },
	{ 'Key': 'TVKey v2',                    'Name': 'TV Stick v2',                'Icon': 'e_cletv_v2.png' },
	{ 'Key': 'USBKey',                      'Name': 'USB Key',                    'Icon': 'e_cleusb.png' },
	{ 'Key': 'WiFi_Access_Point',           'Name': 'Wi-Fi Access Point',         'Icon': 'e_pointacceswifi.png' },
	{ 'Key': 'Window Sensor',               'Name': 'Window Sensor',              'Icon': 'e_door_sensor.png' },
	{ 'Key': 'Computer',                    'Name': 'Windows Computer',           'Icon': 'e_ordibureau_windows.png' },
	{ 'Key': 'SAH AP',                      'Name': 'Wi-Fi Repeater',             'Icon': 'e_pointacceswifi.png' },
	{ 'Key': 'repeteurwifi6',               'Name': 'Wi-Fi Repeater 6',           'Icon': 'e_pointacceswifi.png' }
]


# Tab indexes
class MonitorTab(IntEnum):
	DeviceList = 0
	LiveboxInfos = 1
	DeviceInfos = 2
	DeviceEvents = 3
	Phone = 4
	Actions = 5
	Repeaters = 6  # Index of first, and others incrementally



# ################################ Tools ################################

# Setting up application style depending on platform
def SetApplicationStyle():
	global WIND_HEIGHT_ADJUST
	global DIAG_HEIGHT_ADJUST
	global DUAL_PANE_ADJUST
	global LIST_HEADER_HEIGHT
	global LIST_LINE_HEIGHT
	global LIST_STYLESHEET
	global LIST_HEADER_STYLESHEET

	aKeys = QtWidgets.QStyleFactory.keys()
	aPlatform =  platform.system()
	aStyle = 'Fusion'
	if aPlatform == 'Windows':
		aStyle = 'Windows'
	elif aPlatform == 'Darwin':
		aStyle = 'macOS'

	if aStyle == 'Fusion':
		WIND_HEIGHT_ADJUST = 2
		DIAG_HEIGHT_ADJUST = -4
		DUAL_PANE_ADJUST = 0
		LIST_HEADER_HEIGHT = 22
		LIST_LINE_HEIGHT = 30
		LIST_STYLESHEET = 'color:black; background-color:#FAFAFA'
		LIST_HEADER_STYLESHEET = '''
			QHeaderView::section {
				border-width: 0px 0px 1px 0px;
				border-color: grey;
			}
			'''
	elif aStyle == 'Windows':
		WIND_HEIGHT_ADJUST = 0
		DIAG_HEIGHT_ADJUST = 0
		DUAL_PANE_ADJUST = 0
		LIST_HEADER_HEIGHT = 29	 # Actually 25, but 4 pixels more are required for QTableViews
		LIST_LINE_HEIGHT = 30
		LIST_STYLESHEET = 'color:black; background-color:#FAFAFA'
		LIST_HEADER_STYLESHEET = '''
			QHeaderView::section {
				border-width: 0px 0px 1px 0px;
				border-style: solid;
				border-color: grey;
			}
			'''
	elif aStyle == 'macOS':
		WIND_HEIGHT_ADJUST = 4
		DIAG_HEIGHT_ADJUST = 30
		DUAL_PANE_ADJUST = 20
		LIST_HEADER_HEIGHT = 25
		LIST_LINE_HEIGHT = 30
		LIST_STYLESHEET = 'color:black; background-color:#F0F0F0; font-size: 10px; gridline-color:#FFFFFF'
		LIST_HEADER_STYLESHEET = '''
			QHeaderView::section {
				border-width: 0px 0px 1px 0px;
				border-color: grey;
				font-size: 11px
			}
			'''

	if aStyle in aKeys:
		QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create(aStyle))


# Setting up table style depending on platform
def SetTableStyle(iTable):
	global LIST_STYLESHEET
	global LIST_HEADER_STYLESHEET

	iTable.setGridStyle(QtCore.Qt.PenStyle.SolidLine)
	iTable.setStyleSheet(LIST_STYLESHEET)
	aHeader = iTable.horizontalHeader()
	aHeader.setStyleSheet(LIST_HEADER_STYLESHEET)
	aHeader.setFont(LmTools.BOLD_FONT)


# Setup configuration according to Livebox model
def SetLiveboxModel(iModel):
	global NET_INTF
	global NET_INTF_LB5
	global NET_INTF_LB6
	global INTF_NAME_MAP
	global INTF_NAME_MAP_LB5
	global INTF_NAME_MAP_LB6

	if iModel == 'LB6':
		NET_INTF = NET_INTF_LB6
		INTF_NAME_MAP = INTF_NAME_MAP_LB6
	else:
		NET_INTF = NET_INTF_LB5
		INTF_NAME_MAP = INTF_NAME_MAP_LB5



# ################################ Config Class ################################

class LmConf:
	LiveboxURL = LIVEBOX_URL
	LiveboxUser = LIVEBOX_USER
	LiveboxPassword = LIVEBOX_PASSWORD
	FilterDevices = FILTER_DEVICES
	MacAddrTableFile = MACADDR_TABLE_FILE
	MacAddrTable = {}
	MacAddrApiKey = MACADDR_API_KEY
	AllDeviceIconsLoaded = False


	### Load configuration
	@staticmethod
	def load():
		aConfigFilePath = os.path.join(LmConf.getConfigDirectory(), CONFIG_FILE)
		try:
			with open(aConfigFilePath) as aConfigFile:
				aConfig = json.load(aConfigFile)
				p = aConfig.get('Livebox URL')
				if p is not None:
					LmConf.LiveboxURL = p
				p = aConfig.get('Livebox User')
				if p is not None:
					LmConf.LiveboxUser = p
				p = aConfig.get('Livebox Password')
				if p is not None:
					try:
						LmConf.LiveboxPassword = Fernet(SECRET.encode('utf-8')).decrypt(p.encode('utf-8')).decode('utf-8')
					except:
						LmConf.LiveboxPassword = LIVEBOX_PASSWORD
				p = aConfig.get('Filter Devices')
				if p is not None:
					LmConf.FilterDevices = p
				p = aConfig.get('MacAddr Table File')
				if p is not None:
					LmConf.MacAddrTableFile = p
				p = aConfig.get('MacAddr API Key')
				if p is not None:
					LmConf.MacAddrApiKey = p
		except:
			LmTools.Error('No or wrong configuration file, creating one.')
			LmConf.save()


	### Save configuration file
	@staticmethod
	def save():
		aConfigPath = LmConf.getConfigDirectory()

		# Create config directory if doesn't exist
		if not os.path.exists(aConfigPath):
			try:
				os.makedirs(aConfigPath)
			except BaseException as e:
				LmTools.Error('Cannot create configuration folder. Error: {}'.format(e))
				return

		aConfigFilePath = os.path.join(aConfigPath, CONFIG_FILE)
		try:
			with open(aConfigFilePath, 'w') as aConfigFile:
				aConfig = {}
				aConfig['Livebox URL'] = LmConf.LiveboxURL
				aConfig['Livebox User'] = LmConf.LiveboxUser
				aConfig['Livebox Password'] = Fernet(SECRET.encode('utf-8')).encrypt(LmConf.LiveboxPassword.encode('utf-8')).decode('utf-8')
				aConfig['Filter Devices'] = LmConf.FilterDevices
				aConfig['MacAddr Table File'] = LmConf.MacAddrTableFile
				aConfig['MacAddr API Key'] = LmConf.MacAddrApiKey
				json.dump(aConfig, aConfigFile, indent = 4)
		except BaseException as e:
			LmTools.Error('Cannot save configuration file. Error: {}'.format(e))


	### Set Livebox password
	@staticmethod
	def setLiveboxPassword(iPassword):
		LmConf.LiveboxPassword = iPassword
		LmConf.save()


	### Load MAC address table
	@staticmethod
	def loadMacAddrTable():
		aMacAddrTableFilePath = os.path.join(LmConf.getConfigDirectory(), LmConf.MacAddrTableFile)
		try:
			with open(aMacAddrTableFilePath) as aMacTableFile:
				LmConf.MacAddrTable = json.load(aMacTableFile)
		except:
			LmConf.MacAddrTable = {}


	### Save MAC address table
	@staticmethod
	def saveMacAddrTable():
		aConfigPath = LmConf.getConfigDirectory()

		# Create config directory if doesn't exist
		if not os.path.exists(aConfigPath):
			try:
				os.makedirs(aConfigPath)
			except BaseException as e:
				LmTools.Error('Cannot create configuration folder. Error: {}'.format(e))
				return

		aMacAddrTableFilePath = os.path.join(aConfigPath, LmConf.MacAddrTableFile)
		try:
			with open(aMacAddrTableFilePath, 'w') as aMacTableFile:
				json.dump(LmConf.MacAddrTable, aMacTableFile, indent = 4)
		except BaseException as e:
			LmTools.Error('Cannot save MacAddress file. Error: {}'.format(e))


	### Determine config files directory
	@staticmethod
	def getConfigDirectory():
		if hasattr(sys, 'frozen'):
			# If program is built with PyInstaller, use standard OS dirs
			aPlatform =  platform.system()
			if aPlatform == 'Windows':
				return os.path.join(os.environ['APPDATA'], 'LiveboxMonitor')
			elif aPlatform == 'Darwin':
				return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'LiveboxMonitor')
			else:
				return os.path.join(os.path.expanduser('~'), '.config', 'LiveboxMonitor')
		else:
			# If program is Python script mode, use local dir
			return '.'


	### Get a device icon
	@staticmethod
	def getDeviceIcon(iDevice):
		if LmConf.AllDeviceIconsLoaded:
			return iDevice['PixMap']
		else:
			aIconPixMap = iDevice.get('PixMap', None)
			if aIconPixMap is None:
				aIconPixMap = QtGui.QPixmap()

				try:
					aIconData = requests.get(LmConf.LiveboxURL + ICON_URL + iDevice['Icon'])
					if not aIconPixMap.loadFromData(aIconData.content):
						LmTools.Error('Cannot load device icon ' + iDevice['Icon'] + '.')
				except:
					LmTools.Error('Cannot request device icon ' + iDevice['Icon'] + '.')

				iDevice['PixMap'] = aIconPixMap

			return aIconPixMap


	### Load all device icons
	@staticmethod
	def loadDeviceIcons():
		if not LmConf.AllDeviceIconsLoaded:
			for d in DEVICE_TYPES:
				LmConf.getDeviceIcon(d)

			LmConf.AllDeviceIconsLoaded = True
