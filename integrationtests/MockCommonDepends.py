import sys
import time
import platform


class MockCommonDepends:
    def mock(self):
        import platform
        from mock import Mock
        sys.path.append("../plugin/")

        # Setup default test various values
        sys.modules["__main__"].plugin = "Common - IntegrationTest"
        sys.modules["__main__"].dbg = True

        try:
            plat = platform.uname()
        except:
            plat = ('', '', '', '', '', '')

        if plat[0] == "FreeBSD":
            sys.modules["__main__"].dbglevel = 10
        else:
            sys.modules["__main__"].dbglevel = 3

        import CommonFunctions
        sys.modules["__main__"].common = CommonFunctions
        sys.modules["__main__"].common.log = Mock()
        sys.modules["__main__"].common.log.side_effect = self.log

    def mockXBMC(self):
        from mock import Mock
        sys.path.append("../xbmc-mocks/")
        import xbmc
        import xbmcaddon
        import xbmcgui
        import xbmcplugin
        import xbmcvfsdummy as xbmcvfs

        # Setup basic xbmc dependencies
        sys.modules["__main__"].xbmc = Mock(spec=xbmc)
        sys.modules["__main__"].xbmc.getSkinDir = Mock()
        sys.modules["__main__"].xbmc.translatePath = Mock()
        sys.modules["__main__"].xbmc.log = Mock()
        sys.modules["__main__"].xbmc.log.side_effect = self.log
        sys.modules["__main__"].xbmc.getSkinDir = Mock()
        sys.modules["__main__"].xbmc.getSkinDir.return_value = "testSkinPath"
        sys.modules["__main__"].xbmc.getInfoLabel = Mock()
        sys.modules["__main__"].xbmc.getInfoLabel.return_value = "some_info_label"
        sys.modules["__main__"].xbmcaddon = Mock(spec=xbmcaddon)
        settingsdummy = Mock()

        try:
            plat = platform.uname()
        except:
            plat = ('', '', '', '', '', '')

        if plat[0] == "FreeBSD":
            settingsdummy.getSetting.side_effect = ["true", "5", "/usr/local/bin/rtmpdump", "usr/local/bin/rtmpdump", "/usr/local/bin/vlc", "/usr/local/bin/vlc", "/usr/local/bin/mplayer", "/usr/local/bin/mplayer", "10", "30"]
        else:
            settingsdummy.getSetting.side_effect = ["true", "5", "", "", "", "10", "30"]

        settingsdummy.getAddonInfo.return_value = "./tmp/tmp"
        sys.modules["__main__"].xbmcaddon.Addon.return_value = settingsdummy
        sys.modules["__main__"].xbmcgui = Mock(spec=xbmcgui)
        sys.modules["__main__"].xbmcgui.WindowXMLDialog.return_value = "testWindowXML"
        sys.modules["__main__"].xbmcgui.getCurrentWindowId.return_value = 1
        sys.modules["__main__"].xbmcplugin = Mock(spec=xbmcplugin)
        sys.modules["__main__"].xbmcvfs = xbmcvfs

        sys.modules["DialogDownloadProgress"] = __import__("mock")
        sys.modules["DialogDownloadProgress"].DownloadProgress = Mock()

        import xbmcSettings
        sys.modules["__main__"].settings = xbmcSettings.xbmcSettings()

    def log(self, description, level=0):
        import inspect
        if sys.modules["__main__"].dbg and sys.modules["__main__"].dbglevel > level:
            try:
                print "%s [%s] %s : '%s'" % (time.strftime("%H:%M:%S"), "Common IntegrationTest", inspect.stack()[3][3], description.decode("utf-8", "ignore"))
            except:
                print "%s [%s] %s : '%s'" % (time.strftime("%H:%M:%S"), "Common IntegrationTest", inspect.stack()[3][3], description)

    def execute(self, function, *args):
        return function(*args)
