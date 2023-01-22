### Livebox Monitor device list tab module ###

import datetime

from enum import IntEnum

from PyQt6 import QtGui
from PyQt6 import QtCore
from PyQt6 import QtWidgets

from src import LmTools
from src import LmConfig
from src.LmConfig import LmConf
from src.LmIcons import LmIcon


# ################################ VARS & DEFS ################################

# List columns
class DevCol(IntEnum):
	Key = 0
	Type = 1
	Name = 2
	LBName = 3
	MAC = 4
	IP = 5
	Link = 6
	Active = 7
	Wifi = 8
	Event = 9
	Down = 10
	Up = 11
	DownRate = 12
	UpRate = 13
	Count = 14
ICON_COLUMNS = [DevCol.Type, DevCol.Active, DevCol.Wifi, DevCol.Event]

class DSelCol(IntEnum):
	Key = 0		# Must be the same as DevCol.Key
	Name = 1
	MAC = 2
	Count = 3

# Sorting columns by numeric
class NumericSortItem(QtWidgets.QTableWidgetItem):
	def __lt__(self, iOther):
		x =  self.data(QtCore.Qt.ItemDataRole.UserRole)
		if x is None:
			x = 0
		y = iOther.data(QtCore.Qt.ItemDataRole.UserRole)
		if y is None:
			y = 0
		return x < y

# Drawing centered icons
class CenteredIconsDelegate(QtWidgets.QStyledItemDelegate):
	def paint(self, iPainter, iOption, iIndex):
		if iIndex.column() in ICON_COLUMNS:
			aIcon = iIndex.data(QtCore.Qt.ItemDataRole.DecorationRole)
			if aIcon is not None:
				aIcon.paint(iPainter, iOption.rect)
		else:
			super(CenteredIconsDelegate, self).paint(iPainter, iOption, iIndex)



# ################################ LmDeviceList class ################################
class LmDeviceList:

	### Create device list tab
	def createDeviceListTab(self):
		self._deviceListTab = QtWidgets.QWidget()

		# Device list columns
		self._deviceList = QtWidgets.QTableWidget()
		self._deviceList.setColumnCount(DevCol.Count)
		self._deviceList.setHorizontalHeaderLabels(('Key', 'T', 'Name', 'Livebox Name', 'MAC', 'IP', 'Link', 'A', 'Wifi', 'E', 'Down', 'Up', 'DRate', 'URate'))
		self._deviceList.setColumnHidden(DevCol.Key, True)
		aHeader = self._deviceList.horizontalHeader()
		aHeader.setSectionResizeMode(DevCol.Type, QtWidgets.QHeaderView.ResizeMode.Fixed)
		aHeader.setSectionResizeMode(DevCol.Name, QtWidgets.QHeaderView.ResizeMode.Stretch)
		aHeader.setSectionResizeMode(DevCol.LBName, QtWidgets.QHeaderView.ResizeMode.Stretch)
		aHeader.setSectionResizeMode(DevCol.MAC, QtWidgets.QHeaderView.ResizeMode.Fixed)
		aHeader.setSectionResizeMode(DevCol.IP, QtWidgets.QHeaderView.ResizeMode.Fixed)
		aHeader.setSectionResizeMode(DevCol.Link, QtWidgets.QHeaderView.ResizeMode.Stretch)
		aHeader.setSectionResizeMode(DevCol.Active, QtWidgets.QHeaderView.ResizeMode.Fixed)
		aHeader.setSectionResizeMode(DevCol.Wifi, QtWidgets.QHeaderView.ResizeMode.Fixed)
		aHeader.setSectionResizeMode(DevCol.Event, QtWidgets.QHeaderView.ResizeMode.Fixed)
		aHeader.setSectionResizeMode(DevCol.Down, QtWidgets.QHeaderView.ResizeMode.Fixed)
		aHeader.setSectionResizeMode(DevCol.Up, QtWidgets.QHeaderView.ResizeMode.Fixed)
		aHeader.setSectionResizeMode(DevCol.DownRate, QtWidgets.QHeaderView.ResizeMode.Fixed)
		aHeader.setSectionResizeMode(DevCol.UpRate, QtWidgets.QHeaderView.ResizeMode.Fixed)
		self._deviceList.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
		self._deviceList.setColumnWidth(DevCol.Type, 48)
		self._deviceList.setColumnWidth(DevCol.Name, 400)
		self._deviceList.setColumnWidth(DevCol.LBName, 400)
		self._deviceList.setColumnWidth(DevCol.MAC, 120)
		self._deviceList.setColumnWidth(DevCol.IP, 105)
		self._deviceList.setColumnWidth(DevCol.Link, 150)
		self._deviceList.setColumnWidth(DevCol.Active, 10)
		self._deviceList.setColumnWidth(DevCol.Wifi, 70)
		self._deviceList.setColumnWidth(DevCol.Event, 10)
		self._deviceList.setColumnWidth(DevCol.Down, 75)
		self._deviceList.setColumnWidth(DevCol.Up, 75)
		self._deviceList.setColumnWidth(DevCol.DownRate, 75)
		self._deviceList.setColumnWidth(DevCol.UpRate, 75)
		self._deviceList.verticalHeader().hide()
		self._deviceList.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
		self._deviceList.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
		self._deviceList.setSortingEnabled(True)
		self._deviceList.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
		self._deviceList.setItemDelegate(CenteredIconsDelegate(self))
		LmConfig.SetTableStyle(self._deviceList)

		# Button bar
		aHBox = QtWidgets.QHBoxLayout()
		aHBox.setSpacing(30)
		aRefreshDeviceListButton = QtWidgets.QPushButton('Refresh')
		aRefreshDeviceListButton.clicked.connect(self.refreshDeviceListButtonClick)
		aHBox.addWidget(aRefreshDeviceListButton)
		aDeviceInfoButton = QtWidgets.QPushButton('Device Infos')
		aDeviceInfoButton.clicked.connect(self.deviceInfoButtonClick)
		aHBox.addWidget(aDeviceInfoButton)
		aDeviceEventsButton = QtWidgets.QPushButton('Device Events')
		aDeviceEventsButton.clicked.connect(self.deviceEventsButtonClick)
		aHBox.addWidget(aDeviceEventsButton)
		aIPv6Button = QtWidgets.QPushButton('IPv6...')
		aIPv6Button.clicked.connect(self.ipv6ButtonClick)
		aHBox.addWidget(aIPv6Button)

		# Layout
		aVBox = QtWidgets.QVBoxLayout()
		aVBox.setSpacing(10)
		aVBox.addWidget(self._deviceList, 0)
		aVBox.addLayout(aHBox, 1)
		self._deviceListTab.setLayout(aVBox)

		self._tabWidget.addTab(self._deviceListTab, 'Device List')


	### Init the Livebox Wifi stats collector thread
	def initWifiStatsLoop(self):
		self._liveboxWifiStatsMap = {}
		self._liveboxWifiStatsThread = None
		self._liveboxWifiStatsLoop = None


	### Start the Livebox Wifi stats collector thread
	def startWifiStatsLoop(self):
		self._liveboxWifiStatsThread = QtCore.QThread()
		self._liveboxWifiStatsLoop = LiveboxWifiStatsThread(self._session)
		self._liveboxWifiStatsLoop.moveToThread(self._liveboxWifiStatsThread)
		self._liveboxWifiStatsThread.started.connect(self._liveboxWifiStatsLoop.run)
		self._liveboxWifiStatsLoop._wifiStatsReceived.connect(self.processLiveboxWifiStats)
		self._liveboxWifiStatsLoop._resume.connect(self._liveboxWifiStatsLoop.resume)
		self._liveboxWifiStatsThread.start()


	### Suspend the Livebox Wifi stats collector thread
	def suspendWifiStatsLoop(self):
		if self._liveboxWifiStatsThread is not None:
			self._liveboxWifiStatsLoop.stop()


	### Resume the Livebox Wifi stats collector thread
	def resumeWifiStatsLoop(self):
		if self._liveboxWifiStatsThread is None:
			self.startWifiStatsLoop()
		else:
			self._liveboxWifiStatsLoop._resume.emit()


	### Stop the Livebox Wifi stats collector thread
	def stopWifiStatsLoop(self):
		if self._liveboxWifiStatsThread is not None:
			self._liveboxWifiStatsThread.quit()
			self._liveboxWifiStatsThread.wait()
			self._liveboxWifiStatsThread = None
			self._liveboxWifiStatsLoop = None


	### Click on refresh device list button
	def refreshDeviceListButtonClick(self):
		self._deviceList.clearContents()
		self._deviceList.setRowCount(0)
		self._infoDList.clearContents()
		self._infoDList.setRowCount(0)
		self._infoAList.clearContents()
		self._infoAList.setRowCount(0)
		self._eventDList.clearContents()
		self._eventDList.setRowCount(0)
		self._eventList.clearContents()
		self._eventList.setRowCount(0)
		LmConf.loadMacAddrTable()
		self.loadDeviceList()


	### Click on device infos button
	def deviceInfoButtonClick(self):
		aCurrentSelection = self._deviceList.currentRow()
		if aCurrentSelection >= 0:
			aKey = self._deviceList.item(aCurrentSelection, DevCol.Key).text()
			aLine = self.findDeviceLine(self._infoDList, aKey)
			self._infoDList.selectRow(aLine)
		self.switchToDeviceInfosTab()
	

	### Click on device events button
	def deviceEventsButtonClick(self):
		aCurrentSelection = self._deviceList.currentRow()
		if aCurrentSelection >= 0:
			aKey = self._deviceList.item(aCurrentSelection, DevCol.Key).text()
			aLine = self.findDeviceLine(self._eventDList, aKey)
			self._eventDList.selectRow(aLine)
		self.switchToDeviceEventsTab()


	### Click on IPv6 button
	def ipv6ButtonClick(self):
		self.startTask('Getting IPv6 Information...')

		# Get IPv6 status
		aIPv6Enabled = None
		try:
			d = self._session.request('NMC.IPv6:get')
		except BaseException as e:
			LmTools.Error('Error: {}'.format(e))
			d = None
		if d is not None:
			d = d.get('data')
		if d is not None:
			aIPv6Enabled = d.get('Enable')
		if aIPv6Enabled is None:
			self.endTask()
			LmTools.DisplayError('NMC.IPv6:get service error')
			return

		# Get IPv6 address and prefix
		aIPv6Addr = None
		aIPv6Prefix = None
		try:
			d = self._session.request('NMC:getWANStatus')
		except BaseException as e:
			LmTools.Error('Error: {}'.format(e))
			d = None
		if d is not None:
			s = d.get('status')
			if (s is None) or (not s):
				d = None
			else:
				d = d.get('data')
		if d is not None:
			aIPv6Addr = d.get('IPv6Address')
			aIPv6Prefix = d.get('IPv6DelegatedPrefix')
		if (aIPv6Addr is None) or (aIPv6Prefix is None):
			self.endTask()
			LmTools.DisplayError('NMC:getWANStatus service error')
			return

		# Refresh device list
		d = None
		try:
			d = self._session.request('Devices:get', { 'expression': 'physical and !self and !voice' }, iTimeout = 10)
		except BaseException as e:
			LmTools.Error('Error: {}'.format(e))
			d = None
		if (d is not None):
			d = d.get('status')
		if (d is None):
			self.endTask()
			LmTools.DisplayError('Error getting device list.')
			return
		else:
			self._liveboxDevices = d

		self.endTask()

		aIPv6Dialog = IPv6Dialog(aIPv6Enabled, aIPv6Addr, aIPv6Prefix, self)
		aIPv6Dialog.loadDeviceList(d)
		aIPv6Dialog.exec()


	### Load device list
	def loadDeviceList(self):
		self.startTask('Loading device list...')

		self._deviceList.setSortingEnabled(False)
		self._infoDList.setSortingEnabled(False)
		self._eventDList.setSortingEnabled(False)
		self._eventList.setSortingEnabled(False)

		self._liveboxDevices = self._session.request('Devices:get', { 'expression': 'physical and !self and !voice' }, iTimeout = 10)
		if (self._liveboxDevices is not None):
			self._liveboxDevices = self._liveboxDevices.get('status')
		if (self._liveboxDevices is None):
			LmTools.MouseCursor_Normal()
			LmTools.DisplayError('Error getting device list.')
			LmTools.MouseCursor_Busy()
		self._liveboxTopology = self._session.request('TopologyDiagnostics:buildTopology', { 'SendXmlFile': 'false' }, iTimeout = 20)
		if (self._liveboxTopology is not None):
			self._liveboxTopology = self._liveboxTopology.get('status')
		self._interfaceMap = []
		self._deviceMap = []
		if (self._liveboxTopology is None):
			LmTools.MouseCursor_Normal()
			LmTools.DisplayError('Error getting device topology.')
			LmTools.MouseCursor_Busy()
		else:
			self.buildLinkMaps()

		i = 0
		if (self._liveboxDevices is not None):
			for d in self._liveboxDevices:
				if self.displayableDevice(d):
					self.identifyRepeater(d)
					self.addDeviceLine(i, d)
					self.updateDeviceLine(i, d)
					i += 1

		self._deviceList.sortItems(DevCol.Active, QtCore.Qt.SortOrder.DescendingOrder)

		self._eventDList.insertRow(i)
		self._eventDList.setItem(i, DSelCol.Key, QtWidgets.QTableWidgetItem('#NONE#'))
		self._eventDList.setItem(i, DSelCol.Name, QtWidgets.QTableWidgetItem('<None>'))

		self._deviceList.setCurrentCell(-1, -1)
		self._infoDList.setCurrentCell(-1, -1)
		self._eventDList.setCurrentCell(-1, -1)

		self.initDeviceContext()

		self._deviceList.setSortingEnabled(True)
		self._infoDList.setSortingEnabled(True)
		self._eventDList.setSortingEnabled(True)
		self._eventList.setSortingEnabled(True)

		self.endTask()


	### Check if device is displayable
	def displayableDevice(self, iDevice):
		# If Filter Devices option is on, do not display active devices without Layer2Intf
		if LmConf.FilterDevices:
			aActiveStatus = iDevice.get('Active', False)
			if aActiveStatus:
				aIntf = iDevice.get('Layer2Interface', '')
				if len(aIntf) == 0:
					return False

		return True


	### Add device line
	def addDeviceLine(self, iLine, iDevice):
		aKey = iDevice.get('Key', '')
		self.addDeviceLineKey(self._deviceList, iLine, aKey)
		self.addDeviceLineKey(self._infoDList, iLine, aKey)
		self.addDeviceLineKey(self._eventDList, iLine, aKey)

		aMacAddr = iDevice.get('PhysAddress', '')
		self.formatNameWidget(self._deviceList, iLine, aKey, DevCol.Name)
		self.formatMacWidget(self._deviceList, iLine, aMacAddr, DevCol.MAC)
		self.formatNameWidget(self._infoDList, iLine, aKey, DSelCol.Name)
		self.formatMacWidget(self._infoDList, iLine, aMacAddr, DSelCol.MAC)
		self.formatNameWidget(self._eventDList, iLine, aKey, DSelCol.Name)
		self.formatMacWidget(self._eventDList, iLine, aMacAddr, DSelCol.MAC)


	### Add a line with a device key
	@staticmethod
	def addDeviceLineKey(iList, iLine, iKey):
		iList.insertRow(iLine)
		iList.setItem(iLine, DevCol.Key, QtWidgets.QTableWidgetItem(iKey))


	### Update device line
	def updateDeviceLine(self, iLine, iDevice):
		aDeviceType = iDevice.get('DeviceType', '')
		aDeviceTypeIcon = self.formatDeviceTypeTableWidget(aDeviceType)
		self._deviceList.setItem(iLine, DevCol.Type, aDeviceTypeIcon)

		aLBName = QtWidgets.QTableWidgetItem(iDevice.get('Name', ''))
		self._deviceList.setItem(iLine, DevCol.LBName, aLBName)

		aIPv4Struct = iDevice.get('IPv4Address')
		if (aIPv4Struct is None) or (len(aIPv4Struct) == 0):
			aIPv4 = ''
			aIPv4Reacheable = ''
			aIPv4Reserved = False
		else:
			aIPv4 = aIPv4Struct[0].get('Address', '')
			aIPv4Reacheable = aIPv4Struct[0].get('Status', '')
			aIPv4Reserved = aIPv4Struct[0].get('Reserved', False)
		aIP = self.formatIPv4TableWidget(aIPv4, aIPv4Reacheable, aIPv4Reserved)
		self._deviceList.setItem(iLine, DevCol.IP, aIP)

		aLinkIntf = self.findDeviceLink(iDevice.get('Key', ''))
		if aLinkIntf is None:
			aLinkName = 'Unknown'
			aLinkType = ''
		else:
			aLinkName = aLinkIntf['Name']
			aLinkType = aLinkIntf['Type']
		aLink = QtWidgets.QTableWidgetItem(aLinkName)
		self._deviceList.setItem(iLine, DevCol.Link, aLink)

		aActiveStatus = iDevice.get('Active', False)
		aActiveIcon = self.formatActiveTableWidget(aActiveStatus)
		self._deviceList.setItem(iLine, DevCol.Active, aActiveIcon)

		if aLinkType == 'wif':
			aWifiSignal = iDevice.get('SignalNoiseRatio')
			if aWifiSignal is not None:
				aWifiIcon = NumericSortItem()
				if aWifiSignal >= 40:
					aWifiIcon.setIcon(QtGui.QIcon(LmIcon.WifiSignal5Pixmap))
				elif aWifiSignal >= 32:
					aWifiIcon.setIcon(QtGui.QIcon(LmIcon.WifiSignal4Pixmap))
				elif aWifiSignal >= 25:
					aWifiIcon.setIcon(QtGui.QIcon(LmIcon.WifiSignal3Pixmap))
				elif aWifiSignal >= 15:
					aWifiIcon.setIcon(QtGui.QIcon(LmIcon.WifiSignal2Pixmap))
				elif aWifiSignal >= 10:
					aWifiIcon.setIcon(QtGui.QIcon(LmIcon.WifiSignal1Pixmap))
				else:
					aWifiIcon.setIcon(QtGui.QIcon(LmIcon.WifiSignal0Pixmap))
				aWifiIcon.setData(QtCore.Qt.ItemDataRole.UserRole, aWifiSignal)
				self._deviceList.setItem(iLine, DevCol.Wifi, aWifiIcon)


	### Update device name in all lists & tabs
	def updateDeviceName(self, iDeviceKey):
		aLine = self.findDeviceLine(self._deviceList, iDeviceKey)
		if aLine >= 0:
			self.formatNameWidget(self._deviceList, aLine, iDeviceKey, DevCol.Name)

		aLine = self.findDeviceLine(self._infoDList, iDeviceKey)
		if aLine >= 0:
			self.formatNameWidget(self._infoDList, aLine, iDeviceKey, DSelCol.Name)

		aLine = self.findDeviceLine(self._eventDList, iDeviceKey)
		if aLine >= 0:
			self.formatNameWidget(self._eventDList, aLine, iDeviceKey, DSelCol.Name)

		self.repeaterUpdateDeviceName(iDeviceKey)


	### Format device type cell
	@staticmethod
	def formatDeviceTypeTableWidget(iDeviceType):
		aDeviceTypeIcon = NumericSortItem()

		i = 0
		for d in LmConfig.DEVICE_TYPES:
			if iDeviceType == d['Key']:
				aDeviceTypeIcon.setIcon(QtGui.QIcon(LmConf.getDeviceIcon(d)))
				break
			i += 1

		aDeviceTypeIcon.setData(QtCore.Qt.ItemDataRole.UserRole, i)

		return aDeviceTypeIcon


	### Format Name cell
	@staticmethod
	def formatNameWidget(iList, iLine, iMacAddr, iNameCol):
		try:
			aName = QtWidgets.QTableWidgetItem(LmConf.MacAddrTable[iMacAddr])
		except:
			aName = QtWidgets.QTableWidgetItem('UNKNOWN')
			aName.setBackground(QtCore.Qt.GlobalColor.red)
		iList.setItem(iLine, iNameCol, aName)
		

	### Format MAC address cell
	@staticmethod
	def formatMacWidget(iList, iLine, iMacAddr, iMacCol):
		aMAC = QtWidgets.QTableWidgetItem(iMacAddr)
		aMAC.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
		iList.setItem(iLine, iMacCol, aMAC)


	### Format Active status cell
	@staticmethod
	def formatActiveTableWidget(iActiveStatus):
		aActiveIconItem = NumericSortItem()
		if iActiveStatus:
			aActiveIconItem.setIcon(QtGui.QIcon(LmIcon.TickPixmap))
			aActiveIconItem.setData(QtCore.Qt.ItemDataRole.UserRole, 1)
		else:
			aActiveIconItem.setIcon(QtGui.QIcon(LmIcon.CrossPixmap))
			aActiveIconItem.setData(QtCore.Qt.ItemDataRole.UserRole, 0)
		return aActiveIconItem


	### Format IPv4 cell
	@staticmethod
	def formatIPv4TableWidget(iIPv4, iReacheableStatus, iReserved):
		aIP = QtWidgets.QTableWidgetItem(iIPv4)
		if iReacheableStatus != 'reachable':
			aIP.setForeground(QtCore.Qt.GlobalColor.red)
		if iReserved:
			aIP.setFont(LmTools.BOLD_FONT)
		return aIP


	### Find device line from device key
	@staticmethod
	def findDeviceLine(iList, iDeviceKey):
		if len(iDeviceKey):
			i = 0
			n = iList.rowCount()
			while (i < n):
				if iList.item(i, DevCol.Key).text() == iDeviceKey:
					return i
				i += 1
		return -1


	### Build link map
	def buildLinkMaps(self):
		aRootNode = self._liveboxTopology[0]
		aDeviceKey = aRootNode.get('Key', '')
		self.buildLinksMapNode(aRootNode.get('Children', []), aDeviceKey, 'Livebox', '', '')
#DBG	LmTools.DisplayInfos('Interface map', str(self._interfaceMap))
#DBG	LmTools.DisplayInfos('Device map', str(self._deviceMap))


	### Handle a topology node to build links map
	def buildLinksMapNode(self, iNode, iDeviceKey, iDeviceName, iInterfaceKey, iInterfaceName):
		for d in iNode:
			aTags = d.get('Tags', '').split()

			# Handle interface end points
			if 'interface' in aTags:
				iInterfaceKey = d.get('Key', '')
				aInterfaceType = d.get('InterfaceType', '')
				if aInterfaceType == 'Ethernet':
					aInterfaceType = 'eth'
					iInterfaceName = d.get('NetDevName', '')
					if len(iInterfaceName) == 0:
						iInterfaceName = d.get('Name', '')
					if iDeviceName == 'Livebox':
						aNameMap = LmConfig.INTF_NAME_MAP['Livebox']
					else:
						aNameMap = LmConfig.INTF_NAME_MAP['Repeater']
					aMappedName = aNameMap.get(iInterfaceName)
					if aMappedName is not None:
						iInterfaceName = aMappedName
				else:
					aInterfaceType = 'wif'
					aWifiBand = d.get('OperatingFrequencyBand', '')
					if len(aWifiBand):
						iInterfaceName = 'Wifi ' + aWifiBand
					else:
						iInterfaceName = d.get('Name', '')
				aMapEntry = {}
				aMapEntry['Key'] = iInterfaceKey
				aMapEntry['Type'] = aInterfaceType
				aMapEntry['DevKey'] = iDeviceKey
				aMapEntry['DevName'] = iDeviceName
				aMapEntry['IntName'] = iInterfaceName
				aMapEntry['Name'] = iDeviceName + ' ' + iInterfaceName
				self._interfaceMap.append(aMapEntry)

			# Handle devices
			if 'physical' in aTags:
				iDeviceKey = d.get('Key', '')
				iDeviceName = d.get('Name', '')
				aMapEntry = {}
				aMapEntry['Key'] = iDeviceKey
				aMapEntry['InterfaceKey'] = iInterfaceKey
				self._deviceMap.append(aMapEntry)

			self.buildLinksMapNode(d.get('Children', []), iDeviceKey, iDeviceName, iInterfaceKey, iInterfaceName)


	### Find device link name from device key
	def findDeviceLink(self, iDeviceKey):
		aInterfaceKey = ''

		# First find device interface
		for d in self._deviceMap:
			if d['Key'] == iDeviceKey:
				aInterfaceKey = d['InterfaceKey']

				# Then find interface name
				for i in self._interfaceMap:
					if i['Key'] == aInterfaceKey:
						return i

		return None


	### Update device link interface key
	def updateDeviceLinkInterface(self, iDeviceKey, iInterfaceKey):
		# Find device interface
		for d in self._deviceMap:
			if d['Key'] == iDeviceKey:
				d['InterfaceKey'] = iInterfaceKey
				return


	### Update interface map when a device name changes, and refresh the UI
	def updateInterfaceMap(self, iDeviceKey, iDeviceName):
		# Loop on interface map and update each matching entries
		for i in self._interfaceMap:
			if i['DevKey'] == iDeviceKey:
				i['DevName'] = iDeviceName
				aLinkName = iDeviceName + ' ' + i['IntName']
				i['Name'] = aLinkName

				# Then update each device connected to that interface
				for d in self._deviceMap:
					if d['InterfaceKey'] == i['Key']:
						aLine = self.findDeviceLine(self._deviceList, d['Key'])
						if aLine >= 0:
							self._deviceList.setItem(aLine, DevCol.Link, QtWidgets.QTableWidgetItem(aLinkName))


	### Indicate visually the reception of an event for a device
	def updateEventIndicator(self, iDeviceKey):
		# First remove last event indicator
		aListLine = self.findDeviceLine(self._deviceList, self._lastEventDeviceKey)
		if aListLine >= 0:
			self._deviceList.setItem(aListLine, DevCol.Event, None)

		# Set indicator on new device
		aListLine = self.findDeviceLine(self._deviceList, iDeviceKey)
		if aListLine >= 0:
			aEventIndicator = NumericSortItem()
			aEventIndicator.setIcon(QtGui.QIcon(LmIcon.NotifPixmap))
			aEventIndicator.setData(QtCore.Qt.ItemDataRole.UserRole, 1)
			self._deviceList.setItem(aListLine, DevCol.Event, aEventIndicator)

		self._lastEventDeviceKey = iDeviceKey


	### Process a new statistics event
	def processStatisticsEvent(self, iDeviceKey, iEvent):
		# Get event data
		aDownBytes = iEvent.get('RxBytes', 0)
		aUpBytes = iEvent.get('TxBytes', 0)
		aDownErrors = iEvent.get('RxErrors', 0)
		aUpErrors = iEvent.get('TxErrors', 0)
		aDownRateBytes = 0
		aUpRateBytes = 0
		aDownDeltaErrors = iEvent.get('DeltaRxErrors', 0)
		aUpDeltaErrors = iEvent.get('DeltaTxErrors', 0)
		aTimestamp = LmTools.LiveboxTimestamp(iEvent.get('Timestamp', ''))

		# Try to find a previously received statistic record
		aPrevStats = self._statsMap.get(iDeviceKey)
		if aPrevStats is not None:
			aPrevDownBytes = aPrevStats['Down']
			aPrevUpBytes = aPrevStats['Up']
			aPrevTimestamp = aPrevStats['Time']
			aElapsed = int((aTimestamp - aPrevTimestamp).total_seconds())
			if aElapsed > 0:
				aDownRateBytes = int((aDownBytes - aPrevDownBytes) / aElapsed)
				aUpRateBytes = int((aUpBytes - aPrevUpBytes) / aElapsed)

		# Remember current stats
		aStats = {}
		aStats['Down'] = aDownBytes
		aStats['Up'] = aUpBytes
		aStats['Time'] = aTimestamp
		self._statsMap[iDeviceKey] = aStats

		# Update UI
		aListLine = self.findDeviceLine(self._deviceList, iDeviceKey)
		if aListLine >= 0:
			# Prevent device line to change due to sorting
			self._deviceList.setSortingEnabled(False)

			aDown = NumericSortItem(LmTools.FmtBytes(aDownBytes))
			aDown.setData(QtCore.Qt.ItemDataRole.UserRole, aDownBytes)
			aDown.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVertical_Mask)
			if aDownErrors:
				aDown.setForeground(QtCore.Qt.GlobalColor.red)
			self._deviceList.setItem(aListLine, DevCol.Down, aDown)

			aUp = NumericSortItem(LmTools.FmtBytes(aUpBytes))
			aUp.setData(QtCore.Qt.ItemDataRole.UserRole, aUpBytes)
			aUp.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVertical_Mask)
			if aUpErrors:
				aUp.setForeground(QtCore.Qt.GlobalColor.red)
			self._deviceList.setItem(aListLine, DevCol.Up, aUp)

			if aDownRateBytes:
				aDownRate = NumericSortItem(LmTools.FmtBytes(aDownRateBytes) + '/s')
				aDownRate.setData(QtCore.Qt.ItemDataRole.UserRole, aDownRateBytes)
				if aDownDeltaErrors:
					aDownRate.setForeground(QtCore.Qt.GlobalColor.red)
				aDownRate.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVertical_Mask)
			else:
				aDownRate = QtWidgets.QTableWidgetItem('')
			self._deviceList.setItem(aListLine, DevCol.DownRate, aDownRate)

			if aUpRateBytes:
				aUpRate = NumericSortItem(LmTools.FmtBytes(aUpRateBytes) + '/s')
				aUpRate.setData(QtCore.Qt.ItemDataRole.UserRole, aUpRateBytes)
				if aUpDeltaErrors:
					aUpRate.setForeground(QtCore.Qt.GlobalColor.red)
				aUpRate.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVertical_Mask)
			else:
				aUpRate = QtWidgets.QTableWidgetItem('')
			self._deviceList.setItem(aListLine, DevCol.UpRate, aUpRate)

			# Restore sorting
			self._deviceList.setSortingEnabled(True)


	### Process a new changed event
	def processChangedEvent(self, iDeviceKey, iHandler, iEvent):
		# Check if device is in the UI list
		aListLine = self.findDeviceLine(self._deviceList, iDeviceKey)
		if aListLine >= 0:
			# Prevent device line to change due to sorting
			self._deviceList.setSortingEnabled(False)

			# Check if active status changed
			aActiveStatus = iEvent.get('Active')
			if aActiveStatus is not None:
				aIsActive = aActiveStatus != '0'
				aActiveIcon = self.formatActiveTableWidget(aIsActive)
				self._deviceList.setItem(aListLine, DevCol.Active, aActiveIcon)
				self.repeaterActiveEvent(iDeviceKey, aIsActive)

			# Check if IP reachable status changed
			aIPv4Reacheable = iEvent.get('Status')
			if (aIPv4Reacheable is not None) and ('IPv4Address' in iHandler):
				aCurrIP = self._deviceList.item(aListLine, DevCol.IP)
				aReserved = aCurrIP.font().bold()
				aIP = self.formatIPv4TableWidget(aCurrIP.text(), aIPv4Reacheable, aReserved)
				self._deviceList.setItem(aListLine, DevCol.IP, aIP)

			# Check if IP changed
			aIPv4 = iEvent.get('IPAddress')
			if (aIPv4 is not None) and (LmTools.isIPv4(aIPv4)):
				self._deviceList.item(aListLine, DevCol.IP).setText(aIPv4)
				self.repeaterIPAddressEvent(iDeviceKey, aIPv4)

			# Check if name changed
			aName = iEvent.get('Name')
			if aName is not None:
				self._deviceList.setItem(aListLine, DevCol.LBName, QtWidgets.QTableWidgetItem(aName))
				self.updateInterfaceMap(iDeviceKey, aName)

			# Check if MAC address assigned
			aMacAddr = iEvent.get('PhysAddress')
			if aMacAddr is not None:
				self.formatNameWidget(self._deviceList, aListLine, aMacAddr, DevCol.Name)
				self.formatMacWidget(self._deviceList, aListLine, aMacAddr, DevCol.MAC)

				aLine = self.findDeviceLine(self._infoDList, iDeviceKey)
				if aLine >= 0:
					self.formatNameWidget(self._infoDList, aLine, aMacAddr, DSelCol.Name)
					self.formatMacWidget(self._infoDList, aLine, aMacAddr, DSelCol.MAC)

				aLine = self.findDeviceLine(self._eventDList, iDeviceKey)
				if aLine >= 0:
					self.formatNameWidget(self._eventDList, aLine, aMacAddr, DSelCol.Name)
					self.formatMacWidget(self._eventDList, aLine, aMacAddr, DSelCol.MAC)

			# Restore sorting
			self._deviceList.setSortingEnabled(True)


	### Process a new device_name_changed event
	def processDeviceNameChangedEvent(self, iDeviceKey, iEvent):
		# Check if device is in the UI list
		aListLine = self.findDeviceLine(self._deviceList, iDeviceKey)
		if aListLine >= 0:
			aName = iEvent.get('NewName')
			if aName is not None:
				self._deviceList.setItem(aListLine, DevCol.LBName, QtWidgets.QTableWidgetItem(aName))
				self.updateInterfaceMap(iDeviceKey, aName)


	### Process a new device_updated, eth_device_updated or wifi_device_updated event
	def processDeviceUpdatedEvent(self, iDeviceKey, iEvent):
		# Check if device is in the UI list
		aListLine = self.findDeviceLine(self._deviceList, iDeviceKey)
		if aListLine >= 0:
			# Prevent device line to change due to sorting
			self._deviceList.setSortingEnabled(False)

			# Update the link interface
			aLink = iEvent.get('ULinks', [])
			if len(aLink):
				self.updateDeviceLinkInterface(iDeviceKey, aLink[0])

			# Update the device line
			self.updateDeviceLine(aListLine, iEvent)

			# Update potential repeater infos
			self.repeaterDeviceUpdatedEvent(iDeviceKey, iEvent)

			# Restore sorting
			self._deviceList.setSortingEnabled(True)


	### Process a new ip_address_added event
	def processIPAddressAddedEvent(self, iDeviceKey, iEvent):
		# Check if device is in the UI list
		aListLine = self.findDeviceLine(self._deviceList, iDeviceKey)
		if aListLine >= 0:
			if iEvent.get('Family', '') == 'ipv4':
				aIPv4 = iEvent.get('Address', '')
				aIPv4Reacheable = iEvent.get('Status', '')
				aIPv4Reserved = iEvent.get('Reserved', False)
				aIP = self.formatIPv4TableWidget(aIPv4, aIPv4Reacheable, aIPv4Reserved)
				self._deviceList.setItem(aListLine, DevCol.IP, aIP)
				self.repeaterIPAddressEvent(iDeviceKey, aIPv4)


	### Process a new device_added, eth_device_added or wifi_device_added event
	def processDeviceAddedEvent(self, iDeviceKey, iEvent):
		# Check if device is not already in the UI list
		aListLine = self.findDeviceLine(self._deviceList, iDeviceKey)
		if aListLine >= 0:
			return

		aTags = iEvent.get('Tags', '').split()
		if ('physical' in aTags) and (not 'self' in aTags) and (not 'voice' in aTags) and self.displayableDevice(iEvent):
			# Prevent device lines to change due to sorting
			self._deviceList.setSortingEnabled(False)
			self._infoDList.setSortingEnabled(False)
			self._eventDList.setSortingEnabled(False)

			# Update device map
			aMapEntry = {}
			aMapEntry['Key'] = iDeviceKey
			aMapEntry['InterfaceKey'] = None
			self._deviceMap.append(aMapEntry)

			# Update UI
			self.addDeviceLine(0, iEvent)
			self.updateDeviceLine(0, iEvent)

			# Add as repeater if it is one
			self.addPotentialRepeater(iEvent)

			# Restore sorting
			self._deviceList.setSortingEnabled(True)
			self._infoDList.setSortingEnabled(True)
			self._eventDList.setSortingEnabled(True)


	### Process a new device_deleted, eth_device_deleted or wifi_device_deleted event
	def processDeviceDeletedEvent(self, iDeviceKey):
		# Remove from all UI lists
		aListLine = self.findDeviceLine(self._deviceList, iDeviceKey)
		if aListLine >= 0:
			self._deviceList.removeRow(aListLine)
		aListLine = self.findDeviceLine(self._infoDList, iDeviceKey)
		if aListLine >= 0:
			self._infoDList.removeRow(aListLine)
		aListLine = self.findDeviceLine(self._eventDList, iDeviceKey)
		if aListLine >= 0:
			self._eventDList.removeRow(aListLine)

		# Remove repeater if it is one
		self.removePotentialRepeater(iDeviceKey)

		# Cleanup device map
		for d in self._deviceMap:
			if d['Key'] == iDeviceKey:
				self._deviceMap.remove(d)

		# Cleanup event buffer
		try:
			del self._eventBuffer[iDeviceKey]
		except:
			pass


	### Process a new Livebox Wifi stats
	def processLiveboxWifiStats(self, iStats):
		# Get stats data
		aKey = iStats['Key']
		aDeviceKey = iStats['DeviceKey']
		aTimestamp = iStats['Timestamp']
		aDownBytes = iStats['RxBytes']
		aUpBytes = iStats['TxBytes']
		aDownErrors = iStats['RxErrors']
		aUpErrors = iStats['TxErrors']
		aDownRateBytes = 0
		aUpRateBytes = 0
		aDownDeltaErrors = 0
		aUpDeltaErrors = 0

		# Try to find a previously received statistic record
		aPrevStats = self._liveboxWifiStatsMap.get(aKey)
		if aPrevStats is not None:
			aPrevTimestamp = aPrevStats['Timestamp']
			aPrevDownBytes = aPrevStats['RxBytes']
			aPrevUpBytes = aPrevStats['TxBytes']
			aElapsed = int((aTimestamp - aPrevTimestamp).total_seconds())
			if aElapsed > 0:
				if aDownBytes > aPrevDownBytes:
					aDownRateBytes = int((aDownBytes - aPrevDownBytes) / aElapsed)
				if aUpBytes > aPrevUpBytes:
					aUpRateBytes = int((aUpBytes - aPrevUpBytes) / aElapsed)
			aDownDeltaErrors = aDownErrors - aPrevStats['RxErrors']
			aUpDeltaErrors = aUpErrors - aPrevStats['TxErrors']

		# Remember current stats
		self._liveboxWifiStatsMap[aKey] = iStats

		# Update UI
		aListLine = self.findDeviceLine(self._deviceList, aDeviceKey)
		if (aListLine >= 0) and (aPrevStats is not None):
			# Prevent device line to change due to sorting
			self._deviceList.setSortingEnabled(False)

			if aDownRateBytes:
				aDownRate = NumericSortItem(LmTools.FmtBytes(aDownRateBytes) + '/s')
				aDownRate.setData(QtCore.Qt.ItemDataRole.UserRole, aDownRateBytes)
				if aDownDeltaErrors:
					aDownRate.setForeground(QtCore.Qt.GlobalColor.red)
				else:
					aDownRate.setForeground(QtCore.Qt.GlobalColor.blue)
				aDownRate.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVertical_Mask)
			else:
				aDownRate = QtWidgets.QTableWidgetItem('')
			self._deviceList.setItem(aListLine, DevCol.DownRate, aDownRate)

			if aUpRateBytes:
				aUpRate = NumericSortItem(LmTools.FmtBytes(aUpRateBytes) + '/s')
				aUpRate.setData(QtCore.Qt.ItemDataRole.UserRole, aUpRateBytes)
				if aUpDeltaErrors:
					aUpRate.setForeground(QtCore.Qt.GlobalColor.red)
				else:
					aUpRate.setForeground(QtCore.Qt.GlobalColor.blue)
				aUpRate.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVertical_Mask)
			else:
				aUpRate = QtWidgets.QTableWidgetItem('')
			self._deviceList.setItem(aListLine, DevCol.UpRate, aUpRate)

			# Restore sorting
			self._deviceList.setSortingEnabled(True)



# ############# Display IPv6 dialog #############
# List columns
class IPv6Col(IntEnum):
	Key = 0		# Must be the same as DevCol.Key
	Name = 1
	LBName = 2
	MAC = 3
	Active = 4
	IPv4 = 5
	IPv6 = 6
	Count = 7
IPV6_ICON_COLUMNS = [IPv6Col.Active]


# Drawing centered icons
class IPv6CenteredIconsDelegate(QtWidgets.QStyledItemDelegate):
	def paint(self, iPainter, iOption, iIndex):
		if iIndex.column() in IPV6_ICON_COLUMNS:
			aIcon = iIndex.data(QtCore.Qt.ItemDataRole.DecorationRole)
			if aIcon is not None:
				aIcon.paint(iPainter, iOption.rect)
		else:
			super(IPv6CenteredIconsDelegate, self).paint(iPainter, iOption, iIndex)


class IPv6Dialog(QtWidgets.QDialog):
	def __init__(self, iEnabled, iAddr, iPrefix, iParent = None):
		super(IPv6Dialog, self).__init__(iParent)
		self.resize(850, 110 + LmConfig.DialogHeight(12))

		# IPv6 info box
		aIPv6EnabledLabel = QtWidgets.QLabel('IPv6 enabled:')
		aIPv6Enabled = QtWidgets.QLabel()
		if iEnabled:
			aIPv6Enabled.setPixmap(LmIcon.TickPixmap)
		else:
			aIPv6Enabled.setPixmap(LmIcon.CrossPixmap)

		aAddrLabel = QtWidgets.QLabel('IPv6 address:')
		aAddr = QtWidgets.QLineEdit(iAddr)
		aAddr.setReadOnly(True)

		aPrefixLabel = QtWidgets.QLabel('IPv6 prefix:')
		aPrefix = QtWidgets.QLineEdit(iPrefix)
		aPrefix.setReadOnly(True)

		aIPv6InfoGrid = QtWidgets.QGridLayout()
		aIPv6InfoGrid.setSpacing(10)
		aIPv6InfoGrid.addWidget(aIPv6EnabledLabel, 1, 0)
		aIPv6InfoGrid.addWidget(aIPv6Enabled, 1, 1)
		aIPv6InfoGrid.addWidget(aAddrLabel, 2, 0)
		aIPv6InfoGrid.addWidget(aAddr, 2, 1)
		aIPv6InfoGrid.addWidget(aPrefixLabel, 2, 2)
		aIPv6InfoGrid.addWidget(aPrefix, 2, 3)

		# Device table
		self._deviceTable = QtWidgets.QTableWidget()
		self._deviceTable.setColumnCount(IPv6Col.Count)
		self._deviceTable.setHorizontalHeaderLabels(('Key', 'Name', 'Livebox Name', 'MAC', 'A', 'IPv4', 'IPv6'))
		self._deviceTable.setColumnHidden(IPv6Col.Key, True)
		aHeader = self._deviceTable.horizontalHeader()
		aHeader.setSectionResizeMode(IPv6Col.Name, QtWidgets.QHeaderView.ResizeMode.Stretch)
		aHeader.setSectionResizeMode(IPv6Col.LBName, QtWidgets.QHeaderView.ResizeMode.Stretch)
		aHeader.setSectionResizeMode(IPv6Col.MAC, QtWidgets.QHeaderView.ResizeMode.Fixed)
		aHeader.setSectionResizeMode(IPv6Col.Active, QtWidgets.QHeaderView.ResizeMode.Fixed)
		aHeader.setSectionResizeMode(IPv6Col.IPv4, QtWidgets.QHeaderView.ResizeMode.Fixed)
		aHeader.setSectionResizeMode(IPv6Col.IPv6, QtWidgets.QHeaderView.ResizeMode.Fixed)
		self._deviceTable.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
		self._deviceTable.setColumnWidth(IPv6Col.Name, 300)
		self._deviceTable.setColumnWidth(IPv6Col.LBName, 300)
		self._deviceTable.setColumnWidth(IPv6Col.MAC, 120)
		self._deviceTable.setColumnWidth(IPv6Col.Active, 10)
		self._deviceTable.setColumnWidth(IPv6Col.IPv4, 105)
		self._deviceTable.setColumnWidth(IPv6Col.IPv6, 250)
		self._deviceTable.verticalHeader().hide()
		self._deviceTable.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
		self._deviceTable.setSortingEnabled(True)
		self._deviceTable.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
		self._deviceTable.setItemDelegate(IPv6CenteredIconsDelegate(self))
		LmConfig.SetTableStyle(self._deviceTable)

		# Button bar
		aHBox = QtWidgets.QHBoxLayout()
		aOKButton = QtWidgets.QPushButton('OK')
		aOKButton.clicked.connect(self.accept)
		aOKButton.setDefault(True)
		aHBox.addWidget(aOKButton, 1, QtCore.Qt.AlignmentFlag.AlignRight)

		aVBox = QtWidgets.QVBoxLayout(self)
		aVBox.addLayout(aIPv6InfoGrid, 0)
		aVBox.addWidget(self._deviceTable, 1)
		aVBox.addLayout(aHBox, 1)

		self.setWindowTitle('IPv6 Devices')
		self.setModal(True)
		self.show()


	def loadDeviceList(self, iDevices):
		if (iDevices is not None):
			self._deviceTable.setSortingEnabled(False)
			i = 0
			p = self.parent()
			for d in iDevices:
				if p.displayableDevice(d):
					# First collect global IPv6 addresses
					aIPv6Struct = d.get('IPv6Address')
					aIPv6Addr = []
					if aIPv6Struct is not None:
						for a in aIPv6Struct:
							aScope = a.get('Scope', 'link')
							if aScope != 'link':
								aAddr = a.get('Address')
								if aAddr is not None:
									aIPv6Addr.append(aAddr)
					if not len(aIPv6Addr):
						continue

					# Display data
					aKey = d.get('Key', '')
					p.addDeviceLineKey(self._deviceTable, i, aKey)

					aMacAddr = d.get('PhysAddress', '')
					p.formatNameWidget(self._deviceTable, i, aKey, IPv6Col.Name)

					aLBName = QtWidgets.QTableWidgetItem(d.get('Name', ''))
					self._deviceTable.setItem(i, IPv6Col.LBName, aLBName)

					p.formatMacWidget(self._deviceTable, i, aMacAddr, IPv6Col.MAC)

					aActiveStatus = d.get('Active', False)
					aActiveIcon = p.formatActiveTableWidget(aActiveStatus)
					self._deviceTable.setItem(i, IPv6Col.Active, aActiveIcon)

					aIPv4Struct = d.get('IPv4Address')
					if (aIPv4Struct is None) or (len(aIPv4Struct) == 0):
						aIPv4 = ''
						aIPv4Reacheable = ''
						aIPv4Reserved = False
					else:
						aIPv4 = aIPv4Struct[0].get('Address', '')
						aIPv4Reacheable = aIPv4Struct[0].get('Status', '')
						aIPv4Reserved = aIPv4Struct[0].get('Reserved', False)
					aIP = p.formatIPv4TableWidget(aIPv4, aIPv4Reacheable, aIPv4Reserved)
					self._deviceTable.setItem(i, IPv6Col.IPv4, aIP)

					aIPv6Str = ''
					aResize = False
					for a in aIPv6Addr:
						if len(aIPv6Str):
							aIPv6Str += '\n'
							aResize = True
						aIPv6Str += a
					self._deviceTable.setItem(i, IPv6Col.IPv6, QtWidgets.QTableWidgetItem(aIPv6Str))
					if aResize:
						self._deviceTable.resizeRowToContents(i)

					i += 1

			self._deviceTable.sortItems(IPv6Col.Active, QtCore.Qt.SortOrder.DescendingOrder)
			self._deviceTable.setSortingEnabled(False)



# ############# Livebox Wifi device stats collector thread #############
class LiveboxWifiStatsThread(QtCore.QObject):
	_wifiStatsReceived = QtCore.pyqtSignal(dict)
	_resume = QtCore.pyqtSignal()

	def __init__(self, iSession):
		super(LiveboxWifiStatsThread, self).__init__()
		self._session = iSession
		self._timer = None
		self._loop = None
		self._isRunning = False


	def run(self):
		self._timer = QtCore.QTimer()
		self._timer.timeout.connect(self.collectStats)
		self._loop = QtCore.QEventLoop()
		self.resume()


	def resume(self):
		if not self._isRunning:
			self._timer.start(1000)
			self._isRunning = True
			self._loop.exec()
			self._timer.stop()
			self._isRunning = False


	def stop(self):
		if self._isRunning:
			self._loop.exit()


	def collectStats(self):
		for s in LmConfig.NET_INTF:
			if s['Type'] != 'wif':
				continue
			try:
				aResult = self._session.request('NeMo.Intf.' + s['Key'] + ':getStationStats')
			except BaseException as e:
				LmTools.Error('Error: {}'.format(e))
				aResult = None
			if aResult is not None:
				aStats = aResult.get('status')
				if type(aStats).__name__ == 'list':
					for aStat in aStats:
						e = {}
						e['DeviceKey'] = aStat.get('MACAddress', '')
						e['Key'] = e['DeviceKey'] + '_' + s['Key']
						e['Timestamp'] = datetime.datetime.now()
						e['RxBytes'] = aStat.get('TxBytes', 0)
						e['TxBytes'] = aStat.get('RxBytes', 0)
						e['RxErrors'] = aStat.get('TxErrors', 0)
						e['TxErrors'] = aStat.get('RxErrors', 0)
						self._wifiStatsReceived.emit(e)

