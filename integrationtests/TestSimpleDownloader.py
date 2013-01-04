# -*- coding: utf-8 -*-
import BaseTestCase
import nose
import sys
import os
import time
import inspect
from mock import Mock


class TestSimpleDownloader(BaseTestCase.BaseTestCase):
    ssdummy = Mock()
    sys.modules["storageserverdummy"] = Mock()
    sys.modules["storageserverdummy"].StorageServer.return_value = ssdummy
    import SimpleDownloader

    def cacheFun(self, name):
        video_item = repr([(self.ssdummy.cname, self.ssdummy.cvideo)])

        if self.ssdummy.cache_status == 0:  # Send initialy empty queue
            self.ssdummy.cache_status += 1
        elif self.ssdummy.cache_status > 0 and self.ssdummy.cache_status < 2:  # We have an item in queue
            self.ssdummy.cache_status += 1
            print repr(inspect.stack()[3][3])
            if inspect.stack()[3][3] == "_removeItemFromQueue":  # Starting doing empty run with all requesters after _removeItemFromQueue
                print " Starting empty run now"
                self.ssdummy.cache_status = 100
            return video_item  # Return video item

        return []

    def test_plugin_verify_rtmpdump_works(self):
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        downloader = self.SimpleDownloader.SimpleDownloader()
        result = downloader.isRTMPInstalled()

        print repr(result)
        assert(result)

    def test_plugin_verify_vlc_works(self):
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        downloader = self.SimpleDownloader.SimpleDownloader()
        result = downloader.isVLCInstalled()

        print repr(result)
        assert(result)

    def test_plugin_verify_mplayer_works(self):
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        downloader = self.SimpleDownloader.SimpleDownloader()
        result = downloader.isMPlayerInstalled()

        print repr(result)
        assert(result)

    def test_plugin_should_download_standard_ftp(self):
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        sys.modules["__main__"].settings.load_strings("./resources/settings.xml")
        self.ssdummy.lock.return_value = True
        video = {"url": "ftp://ftp.mozilla.org/pub/mozilla.org/README", "download_path": "./tmp/"}
        self.ssdummy.get.side_effect = [[], repr([("ftp", video)]), repr([("ftp", video)]), repr([("ftp", video)]), []]

        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.download("ftp", video, async=False)

        assert(os.path.exists('./tmp/ftp'))
        assert(os.path.getsize('./tmp/ftp') > 100)

    def test_plugin_should_download_standard_http(self):
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        sys.modules["__main__"].settings.load_strings("./resources/settings.xml")
        self.ssdummy.lock.return_value = True
        video = {"url": "http://tobiasussing.dk/index.html", "download_path": "./tmp/"}
        self.ssdummy.get.side_effect = [[], repr([("http", video)]), repr([("http", video)]), repr([("http", video)]), []]

        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.download("http", video, async=False)

        assert(os.path.exists('./tmp/http'))
        assert(os.path.getsize('./tmp/http') > 10)

    def test_plugin_should_download_standard_uri_async(self):
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        sys.modules["__main__"].settings.load_strings("./resources/settings.xml")
        self.ssdummy.lock.return_value = True
        video = {"url": "http://tobiasussing.dk/index.html", "download_path": "./tmp/"}
        self.ssdummy.get.side_effect = [[], repr([("async", video)]), repr([("async", video)]), repr([("async", video)]), []]

        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.download("async", video)
        time.sleep(10)
        assert(os.path.exists('./tmp/async'))
        assert(os.path.getsize('./tmp/async') > 10)

    # This fails on FreeBSD integration test. <- Apparantly not
    def test_plugin_should_download_rtsp_uri(self):  # Works with vlc. Some servers probably work with mplayer.
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        sys.modules["__main__"].settings.load_strings("./resources/settings.xml")
        video = {"url": "rtsp://184.72.239.149/vod/mp4:BigBuckBunny_175k.mov", "download_path": "./tmp/", "duration": "3"}
        self.ssdummy.cache_status = 0
        self.ssdummy.cvideo = video
        self.ssdummy.cname = "rtsp"
        self.ssdummy.lock.return_value = True

        self.ssdummy.get.side_effect = self.cacheFun

        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.download("rtsp", video, async=False)

        assert(os.path.exists('./tmp/rtsp'))
        assert(os.path.getsize('./tmp/rtsp') > 25000)

    def test_plugin_should_download_mms_uri(self):  # Works with vlc and mplayer
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        sys.modules["__main__"].settings.load_strings("./resources/settings.xml")
        video = {"url": "mms://media.eku.edu/mdr/media/tech/fardo/pslab01.wmv", "download_path": "./tmp/", "duration": "3"}
        self.ssdummy.cache_status = 0
        self.ssdummy.cvideo = video
        self.ssdummy.cname = "mms"
        self.ssdummy.lock.return_value = True
        self.ssdummy.get.side_effect = self.cacheFun

        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.download("mms", video, async=False)

        assert(os.path.exists('./tmp/mms'))
        assert(os.path.getsize('./tmp/mms') > 30000)

    def test_plugin_should_download_rtmp_uri(self):  # Works with rtmpdump, mplayer and vlc
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        sys.modules["__main__"].settings.load_strings("./resources/settings.xml")
        video = {"url": "rtmp://edge01.fms.dutchview.nl/botr/bunny", "download_path": "./tmp/", "duration": "3"}
        self.ssdummy.cache_status = 0
        self.ssdummy.cvideo = video
        self.ssdummy.cname = "rtmp"
        self.ssdummy.lock.return_value = True
        self.ssdummy.get.side_effect = self.cacheFun

        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.download("rtmp", video, async=False)

        assert(os.path.exists('./tmp/rtmp'))
        assert(os.path.getsize('./tmp/rtmp') > 30000)

    def test_plugin_should_fail_withbad_url(self):
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        sys.modules["__main__"].settings.load_strings("./resources/settings.xml")
        video = {"url": "rtmp://dedge01.fms.dutchview.nl/botr/bunny", "download_path": "./tmp/", "duration": "3"}
        self.ssdummy.cache_status = 0
        self.ssdummy.cvideo = video
        self.ssdummy.cname = "rtmp_bad"
        self.ssdummy.lock.return_value = True
        self.ssdummy.get.side_effect = self.cacheFun

        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.download("rtmp_bad", video, async=False)

        assert(os.path.exists('./tmp/tmp/rtmp_bad'))
        assert(os.path.getsize('./tmp/tmp/rtmp_bad') < 20000)

    def test_plugin_should_download_rtmp_uri_live(self):
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        sys.modules["__main__"].settings.load_strings("./resources/settings.xml")
        video = {"url": "rtmp://aljazeeraflashlivefs.fplive.net:1935/aljazeeraflashlive-live/aljazeera_english_1",
                 "live": "true",
                 "duration": "3",
                 "download_path": "./tmp/"
                 }

        self.ssdummy.cache_status = 0
        self.ssdummy.cvideo = video
        self.ssdummy.cname = "live"
        self.ssdummy.lock.return_value = True
        self.ssdummy.get.side_effect = self.cacheFun

        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.download("live", video, async=False)

        assert(os.path.exists('./tmp/live'))
        assert(os.path.getsize('./tmp/live') > 30000)

    def test_plugin_should_download_rtmp_uri_live_with_forced_mplayer(self):
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        sys.modules["__main__"].settings.load_strings("./resources/settings.xml")
        video = {"url": "rtmp://aljazeeraflashlivefs.fplive.net:1935/aljazeeraflashlive-live/aljazeera_english_1",
                 "live": "true",
                 "duration": "3",
                 "download_path": "./tmp/",
                 "use_mplayer": "true"
                 }

        self.ssdummy.cache_status = 0
        self.ssdummy.cvideo = video
        self.ssdummy.cname = "live-mplayer"
        self.ssdummy.lock.return_value = True
        self.ssdummy.get.side_effect = self.cacheFun

        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.download("live-mplayer", video, async=False)

        assert(os.path.exists('./tmp/live-mplayer'))
        assert(os.path.getsize('./tmp/live-mplayer') > 30000)

    def ttest_plugin_should_download_rtsp_uri_live_mystreamtv(self):
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        sys.modules["__main__"].settings.load_strings("./resources/settings.xml")
        video = {"url": "rtsp://dist34.mystreams.tv:5190/ch03/q1",
                 "live": "true",
                 "duration": "60",
                 "download_path": "./tmp/"
                 }

        self.ssdummy.cache_status = 0
        self.ssdummy.cvideo = video
        self.ssdummy.cname = "rtsp-mystreamtv"
        self.ssdummy.lock.return_value = True
        self.ssdummy.get.side_effect = self.cacheFun

        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.download("rtmp-mystreamtv", video, async=False)

        assert(os.path.exists('./tmp/rtsp-mystreamtv'))
        assert(os.path.getsize('./tmp/rtsp-mystreamtv') > 30000)

    def ttest_plugin_should_download_rtmp_uri_live_mystreamtv(self):
        sys.modules["__main__"].xbmc.translatePath.side_effect = ["./tmp/tmp/"]
        sys.modules["__main__"].settings.load_strings("./resources/settings.xml")
        video = {"url": "rtmp://dist34.mystreams.tv:5190/ch03/q1",
                 "live": "true",
                 "duration": "60",
                 "download_path": "./tmp/"
                 }

        self.ssdummy.cache_status = 0
        self.ssdummy.cvideo = video
        self.ssdummy.cname = "rtmp-mystreamtv"
        self.ssdummy.lock.return_value = True
        self.ssdummy.get.side_effect = self.cacheFun

        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.download("rtmp-mystreamtv", video, async=False)

        assert(os.path.exists('./tmp/rtmp-mystreamtv'))
        assert(os.path.getsize('./tmp/rtmp-mystreamtv') > 30000)

if __name__ == "__main__":
    nose.runmodule()
