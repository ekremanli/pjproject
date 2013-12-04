# $Id$
#
# pjsua Python GUI Demo
#
# Copyright (C)2013 Teluu Inc. (http://www.teluu.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA 
#
import sys
if sys.version_info[0] >= 3: # Python 3
	import tkinter as tk
	from tkinter import ttk
	from tkinter import messagebox as msgbox
else:
	import Tkinter as tk
	import ttk
	import tkMessageBox as msgbox


class TextObserver:
	def onSendMessage(self, msg):
		pass
	def onStartTyping(self):
		pass
	def onStopTyping(self):
		pass
		
class TextFrame(ttk.Frame):
	def __init__(self, master, observer):
		ttk.Frame.__init__(self, master)
		self._observer = observer
		self._isTyping = False
		self._createWidgets()

	def _onSendMessage(self, event):
		send_text = self._typingBox.get("1.0", tk.END).strip()
		if send_text == '':
			return
		
		self.addMessage('me: ' + send_text)
		self._typingBox.delete("0.0", tk.END)
		self._onTyping(None)
		
		# notify app for sending message
		self._observer.onSendMessage(send_text)
		
	def _onTyping(self, event):
		# notify app for typing indication
		is_typing = self._typingBox.get("1.0", tk.END).strip() != ''
		if is_typing != self._isTyping:
			self._isTyping = is_typing
			if is_typing:
				self._observer.onStartTyping()
			else:
				self._observer.onStopTyping()
		
	def _createWidgets(self):
		self.rowconfigure(0, weight=1)
		self.rowconfigure(1, weight=0)
		self.rowconfigure(2, weight=0)
		self.columnconfigure(0, weight=1)
		self.columnconfigure(1, weight=0)
		
		self._text = tk.Text(self, font=("Arial", "10"))
		self._text.grid(row=0, column=0, sticky='nswe')
		self._text.config(state=tk.DISABLED)
		self._text.tag_config("info", foreground="darkgray", font=("Arial", "9", "italic"))
		
		scrl = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._text.yview)
		self._text.config(yscrollcommand=scrl.set)
		scrl.grid(row=0, column=1, sticky='nsw')
		
		self._typingBox = tk.Text(self, height=1, font=("Arial", "10"))
		self._typingBox.grid(row=1, columnspan=2, sticky='we', pady=0)
		
		self._statusBar = tk.Label(self, anchor='w', font=("Arial", "8", "italic"))
		self._statusBar.grid(row=2, columnspan=2, sticky='we')
		
		self._typingBox.bind('<Return>', self._onSendMessage)
		self._typingBox.bind("<Key>", self._onTyping)
		self._typingBox.focus_set()
		
	def addMessage(self, msg, is_chat = True):
		self._text.config(state=tk.NORMAL)
		if is_chat:
			self._text.insert(tk.END, msg+'\r\n')
		else:
			self._text.insert(tk.END, msg+'\r\n', 'info')
		self._text.config(state=tk.DISABLED)
		self._text.yview(tk.END)

	def setTypingIndication(self, who, is_typing):
		if is_typing:
			self._statusBar['text'] = "'%s' is typing.." % (who)
		else:
			self._statusBar['text'] = ''

class AudioState:
	NULL, INITIALIZING, CONNECTED, DISCONNECTED, FAILED = range(5)
			
class AudioObserver:
	def onRetry(self, peer_uri):
		pass
	def onKick(self, peer_uri):
		pass
	def onHold(self, peer_uri):
		pass
	def onRxMute(self, peer_uri, is_muted):
		pass
	def onRxVol(self, peer_uri, vol_pct):
		pass
	def onTxMute(self, peer_uri, is_muted):
		pass
			

class AudioFrame(ttk.Labelframe):
	def __init__(self, master, peer_uri, observer):
		ttk.Labelframe.__init__(self, master, text=peer_uri)
		self.peerUri = peer_uri
		self._observer = observer
		self._initFrame = None
		self._callFrame = None
		self._rxMute = False
		self._txMute = False

		# internal state: 0:init - 1:established - 2:failure/rejected 3:normal cleared
		self._state = AudioState.NULL
		
		self._createInitWidgets()
		self._createWidgets()
		
	def updateState(self, state):
		if self._state == state:
			return

		if state == AudioState.INITIALIZING:
			self._callFrame.pack_forget()
			self._initFrame.pack(fill=tk.BOTH)
			self._btnRetry.pack_forget()
			self._btnCancel.pack(side=tk.TOP)
			self._lblInitState['text'] = 'Intializing..'

		elif state == AudioState.CONNECTED:
			self._initFrame.pack_forget()
			self._callFrame.pack(fill=tk.BOTH)			
		else:
			self._callFrame.pack_forget()
			self._initFrame.pack(fill=tk.BOTH)
			if state == AudioState.FAILED:
				self._lblInitState['text'] = 'Failed'
				self._btnRetry.pack()
			else:
				self._lblInitState['text'] = 'Normal cleared'
				self._btnCancel.pack_forget()
		
		# save last state
		self._state = state
		
	def _onRetry(self):
		self._btnRetry.pack_forget()
		self._state = 0
		# notify app
		self._observer.onRetry(self.peerUri)

	def _onKick(self):
		# notify app
		self._observer.onKick(self.peerUri)
		
	def _onHold(self):
		# notify app
		self._observer.onHold(self.peerUri)

	def _onHangup(self):
		# notify app
		self._observer.onKick(self.peerUri)

	def _onRxMute(self):
		# notify app
		self._rxMute = not self._rxMute
		self._observer.onRxMute(self.peerUri, self._rxMute)
		
	def _onRxVol(self, event):
		# notify app
		vol = self.rxVol.get()
		self._observer.onRxVol(self.peerUri, vol)

	def _onTxMute(self):
		# notify app
		self._txMute = not self._txMute
		self._observer.onTxMute(self.peerUri, self._txMute)

	def _createInitWidgets(self):
		self._initFrame = ttk.Frame(self)
		#self._initFrame.pack(fill=tk.BOTH)

	
		self._lblInitState = tk.Label(self._initFrame, font=("Arial", "12"), text='')
		self._lblInitState.pack(side=tk.TOP, fill=tk.X, expand=1)
		
		# Operation: retry, cancel/kick
		self._btnRetry = ttk.Button(self._initFrame, text = 'Retry', command=self._onRetry)
		self._btnRetry.pack(side=tk.TOP)
		self._btnCancel = ttk.Button(self._initFrame, text = 'Cancel', command=self._onKick)
		self._btnCancel.pack(side=tk.TOP)
				
	def _createWidgets(self):
		self._callFrame = ttk.Frame(self)
		#self._callFrame.pack(fill=tk.BOTH)
		
		# toolbar
		toolbar = ttk.Frame(self._callFrame)
		toolbar.pack(side=tk.TOP, fill=tk.X)
		self._btnHold = ttk.Button(toolbar, text='Hold', command=self._onHold)
		self._btnHold.pack(side=tk.LEFT, fill=tk.Y)
		#self._btnXfer = ttk.Button(toolbar, text='Transfer..')
		#self._btnXfer.pack(side=tk.LEFT, fill=tk.Y)
		self._btnHangUp = ttk.Button(toolbar, text='Hangup', command=self._onHangup)
		self._btnHangUp.pack(side=tk.LEFT, fill=tk.Y)

		# volume tool
		vol_frm = ttk.Frame(self._callFrame)
		vol_frm.pack(side=tk.TOP, fill=tk.X)
		
		self.rxVolFrm = ttk.Labelframe(vol_frm, text='RX volume')
		self.rxVolFrm.pack(side=tk.LEFT, fill=tk.Y)
		
		self.btnRxMute = ttk.Button(self.rxVolFrm, width=5, text='Mute', command=self._onRxMute)
		self.btnRxMute.pack(side=tk.LEFT)
		self.rxVol = tk.Scale(self.rxVolFrm, orient=tk.HORIZONTAL, from_=0.0, to=10.0, showvalue=0) #, tickinterval=10.0, showvalue=1)
		self.rxVol.set(5.0)
		self.rxVol.bind("<ButtonRelease-1>", self._onRxVol)
		self.rxVol.pack(side=tk.LEFT)
		
		self.txVolFrm = ttk.Labelframe(vol_frm, text='TX volume')
		self.txVolFrm.pack(side=tk.RIGHT, fill=tk.Y)
		
		self.btnTxMute = ttk.Button(self.txVolFrm, width=5, text='Mute', command=self._onTxMute)
		self.btnTxMute.pack(side=tk.LEFT)
		
		# stat
		self.stat = tk.Text(self._callFrame, width=20, height=5, font=("Arial", "10"))
		self.stat.insert(tk.END, 'stat here')
		self.stat.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=1)


class ChatObserver(TextObserver, AudioObserver):
	def onAddParticipant(self):
		pass
	def onStartAudio(self):
		pass
	def onStopAudio(self):
		pass
		
class ChatFrame(tk.Toplevel):
	"""
	Room
	"""
	def __init__(self, observer):
		tk.Toplevel.__init__(self)
		self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())
		self._observer = observer

		self._text = None
		self._text_shown = True
		
		self._audioEnabled = False
		self._audioFrames = []
		self._createWidgets()
	
	def _createWidgets(self):
		# toolbar
		self.toolbar = ttk.Frame(self)
		self.toolbar.pack(side=tk.TOP, fill=tk.BOTH)
		
		btnText = ttk.Button(self.toolbar, text='Show/hide text', command=self._onShowHideText)
		btnText.pack(side=tk.LEFT, fill=tk.Y)
		btnAudio = ttk.Button(self.toolbar, text='Start/stop audio', command=self._onStartStopAudio)
		btnAudio.pack(side=tk.LEFT, fill=tk.Y)
		
		ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx = 4)

		btnAdd = ttk.Button(self.toolbar, text='Add participant..', command=self._onAddParticipant)
		btnAdd.pack(side=tk.LEFT, fill=tk.Y)

		# media frame
		self.media = ttk.Frame(self)
		self.media.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=1)
		
		# create Text Chat frame
		self.media_left = ttk.Frame(self.media)
		self._text = TextFrame(self.media_left, self._observer)
		self._text.pack(fill=tk.BOTH, expand=1)
		self.media_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
		
		# create other media frame
		self.media_right = ttk.Frame(self.media)
		
	def _arrangeMediaFrames(self):
		if len(self._audioFrames) == 0:
			self.media_right.pack_forget()
			return
		
		self.media_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)
		MAX_ROWS = 3
		row_num = 0
		col_num = 1
		for frm in self._audioFrames:
			frm.grid(row=row_num, column=col_num, sticky='nsew', padx=5, pady=5)
			row_num += 1
			if row_num >= MAX_ROWS:
				row_num  = 0
				col_num += 1
	
	def _onShowHideText(self):
		self.textShowHide(not self._text_shown)
		
	def _onAddParticipant(self):
		self._observer.onAddParticipant()
	
	def _onStartStopAudio(self):
		self._audioEnabled = not self._audioEnabled
		if self._audioEnabled:
			self._observer.onStartAudio()
		else:
			self._observer.onStopAudio()
		self.enableAudio(self._audioEnabled)
			
	# APIs
	
	def bringToFront(self):
		self.deiconify()
		self.lift()
		self._text._typingBox.focus_set()
		
	def textAddMessage(self, msg, is_chat = True):
		self._text.addMessage(msg, is_chat)
		
	def textSetTypingIndication(self, who, is_typing = True):
		self._text.setTypingIndication(who, is_typing)
		
	def addParticipant(self, participant_uri):
		aud_frm = AudioFrame(self.media_right, participant_uri, self._observer)
		self._audioFrames.append(aud_frm)
	
	def delParticipant(self, participant_uri):
		for aud_frm in self._audioFrames:
			if participant_uri == aud_frm.peerUri:
				self._audioFrames.remove(aud_frm)
				# need to delete aud_frm manually?
				aud_frm.destroy()
				return

	def textShowHide(self, show = True):
		if show:
			self.media_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
			self._text._typingBox.focus_set()
		else:
			self.media_left.pack_forget()
		self._text_shown = show
	
	def enableAudio(self, is_enabled = True):
		if is_enabled:
			self._arrangeMediaFrames()
		else:
			self.media_right.pack_forget()
		self._audioEnabled = is_enabled
			
	def audioUpdateState(self, participant_uri, state):
		for aud_frm in self._audioFrames:
			if participant_uri == aud_frm.peerUri:
				aud_frm.updateState(state)
				break
						
if __name__ == '__main__':
	root = tk.Tk()
	root.title("Chat")
	root.columnconfigure(0, weight=1)
	root.rowconfigure(0, weight=1)
	
	obs = ChatObserver()
	dlg = ChatFrame(obs)
	#dlg = TextFrame(root)
	#dlg = AudioFrame(root)

	#dlg.pack(fill=tk.BOTH, expand=1)
	root.mainloop()