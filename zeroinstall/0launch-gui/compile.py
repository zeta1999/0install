import os, popen2
import gtk, gobject
import dialog
from logging import info

from zeroinstall.injector import reader
from zeroinstall.injector.policy import Policy
from gui import policy
	
XMLNS_0COMPILE = 'http://zero-install.sourceforge.net/2006/namespaces/0compile'

class Command:
	def __init__(self):
		self.child = None
		self.error = ""

	def run(self, command, success):
		assert self.child is None
		self.success = success
		self.child = popen2.Popen4(command)
		self.child.tochild.close()
		gobject.io_add_watch(self.child.fromchild, gobject.IO_IN | gobject.IO_HUP, self.got_data)
	
	def got_data(self, src, cond):
		data = os.read(src.fileno(), 100)
		if data:
			self.error += data
			return True
		else:
			status = self.child.wait()
			self.child = None

			if os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0:
				self.success()
			else:
				if os.WIFEXITED(status):
					status = os.WEXITSTATUS(status)
					if status == 1 and not self.error:
						return # Cancelled
					dialog.alert(None, "Command failed with exit code %d:\n%s\n" %
						(status, self.error))
				else:
					dialog.alert(None, "Command failed:\n%s\n" % self.error)
			return False

def compile(interface):
	import zeroinstall
	if reader.parse_version(zeroinstall.version) < reader.parse_version('0.24'):
		dialog.alert(None, _('Sorry, the compile feature requires 0launch 0.24 or later, but '
			'you only have version %s.\n\nNew versions are available from http://0install.net')
			% zeroinstall.version)
		return
	def add_feed():
		# A new local feed may have been registered, so update the interface from the cache
		info("0compile command completed successfully. Reloading interface details.")
		reader.update_from_cache(interface)
		policy.recalculate()

	def build():
		# Get the chosen versions
		src_policy = Policy(interface.uri, src = True)
		src_policy.freshness = 0

		src_policy.recalculate()
		if not src_policy.ready:
			raise Exception('Internal error: required source components not found!')

		root_iface = src_policy.get_interface(src_policy.root)
		impl = src_policy.implementation[root_iface]
		min_version = impl.metadata.get(XMLNS_0COMPILE + ' min-version', None)
		if not min_version: min_version = '0.4'
		# Check the syntax is valid and the version is high enough
		if reader.parse_version(min_version) < reader.parse_version('0.4'):
			min_version = '0.4'

		# Do the whole build-and-register-feed
		c = Command()
		c.run(("0launch",
			'--not-before=' + min_version,
			"http://0install.net/2006/interfaces/0compile.xml",
			'gui',
			'--no-prompt',
			interface.uri), add_feed)

	# Prompt user to choose source version
	c = Command()
	c.run(['0launch', '--gui', '--source', '--download-only', interface.uri], build)