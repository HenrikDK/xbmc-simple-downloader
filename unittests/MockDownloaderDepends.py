import sys
import time


class MockDownloaderDepends:
    common = ""

    def mock(self):
        import sys
        from mock import Mock
        sys.path.append("../plugin/")
        sys.path.append("../plugin/lib/")

        # Setup default test various values
        sys.modules["__main__"].plugin = "SimpleDownloader-0.8"
        sys.modules["__main__"].dbg = True
        sys.modules["__main__"].dbglevel = 10
        sys.modules["__main__"].login = ""
        sys.modules["__main__"].language = Mock()
        sys.modules["__main__"].cache = Mock()
        sys.modules["__main__"].log_override = self

    def mockXBMC(self):
        import sys
        from mock import Mock
        sys.path.append("../xbmc-mocks/")
        import xbmc
        import xbmcaddon
        import xbmcgui
        import xbmcplugin
        import xbmcvfs

        # Setup sqlite
        sys.modules["sqlite"] = __import__("mock")
        sys.modules["sqlite"].connect = Mock()
        sys.modules["sqlite3"] = __import__("mock")
        sys.modules["sqlite3"].connect = Mock()

        # Setup basic xbmc dependencies
        sys.modules["__main__"].xbmc = Mock(spec=xbmc)
        sys.modules["__main__"].xbmc.translatePath = Mock()
        sys.modules["__main__"].xbmc.translatePath.return_value = "testing"
        sys.modules["__main__"].xbmc.getSkinDir = Mock()
        sys.modules["__main__"].xbmc.getSkinDir.return_value = "testSkinPath"
        sys.modules["__main__"].xbmc.getInfoLabel.return_value = "some_info_label"
        sys.modules["__main__"].xbmcaddon = Mock(spec=xbmcaddon)
        sys.modules["__main__"].settingsdummy = Mock()
        sys.modules["__main__"].settingsdummy.getSetting.side_effect = ["true", "5", "", "", "", "10"]
        sys.modules["__main__"].settingsdummy.getAddonInfo.return_value = "some_temporary_path"
        sys.modules["__main__"].settingsdummy.getLocalizedString.return_value = "some_string"
        sys.modules["__main__"].xbmcaddon.Addon.return_value = sys.modules["__main__"].settingsdummy
        sys.modules["__main__"].xbmcgui = Mock(spec=xbmcgui)
        sys.modules["__main__"].xbmcgui.WindowXMLDialog.return_value = "testWindowXML"

        sys.modules["__main__"].xbmcplugin = Mock(spec=xbmcplugin)
        sys.modules["__main__"].xbmcvfs = Mock(spec=xbmcvfs)
        sys.modules["__main__"].settings = Mock(spec=xbmcaddon.Addon())
        sys.modules["__main__"].settings.getAddonInfo.return_value = "somepath"

        sys.modules["__main__"].DialogDownloadProgress = Mock()
        sys.modules["__main__"].DialogDownloadProgress.DownloadProgress = Mock()
        sys.modules["DialogDownloadProgress"] = __import__("mock")
        sys.modules["DialogDownloadProgress"].DownloadProgress = Mock()

        sys.modules["__main__"].common = Mock()
        sys.modules["__main__"].common.log = Mock()
        sys.modules["__main__"].common.log.side_effect = self.log

    def log(self, description, level=0):
        import inspect
        if sys.modules["__main__"].dbg and sys.modules["__main__"].dbglevel > level:
            print "%s [%s] %s : '%s'" % (time.strftime("%H:%M:%S"), "SimpleDownloader", inspect.stack()[3][3], description)
