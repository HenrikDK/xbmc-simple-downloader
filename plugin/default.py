import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs
import socket
import xbmcaddon
import cookielib
import urllib2

settings = xbmcaddon.Addon(id='script.module.simple.downloader.beta')
language = settings.getLocalizedString
version = "0.9.4"
plugin = "SimpleDownloader Beta-" + version
core = ""
common = ""
downloader = ""
dbg = settings.getSetting("dbg") == "true"
dbglevel = 3
