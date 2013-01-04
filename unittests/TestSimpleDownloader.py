# -*- coding: utf-8 -*-
import BaseTestCase
import nose
import sys
from mock import Mock, patch


class TestSimpleDownloader(BaseTestCase.BaseTestCase):
    ssdummy = Mock()
    sys.modules["storageserverdummy"] = Mock()
    sys.modules["storageserverdummy"].StorageServer.return_value = ssdummy
    import SimpleDownloader

    def test_download_should_use_async_as_default(self):
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader._startDownload = Mock()
        downloader._run_async = Mock()

        downloader.download({})

        print downloader._startDownload.call_count
        print downloader._run_async.call_count
        assert(downloader._startDownload.call_count == 0)
        assert(downloader._run_async.call_count == 1)

    def test_download_should_support_disabled_async(self):
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader._startDownload = Mock()
        downloader._run_async = Mock()

        downloader.download("", {}, async=False)

        print downloader._startDownload.call_count
        print downloader._run_async.call_count

        assert(downloader._startDownload.call_count == 1)
        assert(downloader._run_async.call_count == 0)

    def test_download_should_lock_cache_to_ensure_no_other_downloaders_are_running(self):
        sys.modules["__main__"].cache.lock.return_value = False
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader._processQueue = Mock()

        downloader._startDownload({})

        self.ssdummy.lock.assert_any_call("SimpleDownloaderLock")

    def test_download_should_call_addItemToQueue_if_a_downloader_is_already_running(self):
        sys.modules["__main__"].cache.lock.return_value = False
        self.ssdummy.lock.return_value = False
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader._processQueue = Mock()
        downloader._addItemToQueue = Mock()

        downloader._startDownload("downloadid", {})

        downloader._addItemToQueue.assert_called_with("downloadid", {})
        assert(downloader._processQueue.call_count == 0)

    def test_download_should_call_processQueue_if_no_other_downloads_are_running(self):
        self.ssdummy.lock.return_value = True
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader._processQueue = Mock()
        downloader._addItemToQueue = Mock()

        downloader._startDownload("downloadid", {})

        downloader._addItemToQueue.assert_called_with("downloadid", {})
        print repr(downloader._processQueue.call_args_list)
        downloader._processQueue.assert_called_once_with()

    def test_download_should_unlock_cache_when_done(self):
        self.ssdummy.lock.return_value = True
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader._processQueue = Mock()

        downloader._startDownload({})

        print repr(self.ssdummy.lock.call_args_list)
        print repr(self.ssdummy.unlock.call_args_list)
        self.ssdummy.unlock.assert_called_with("SimpleDownloaderLock")

    def test_processQueue_should_call_storage_getNextItemFromQueue(self):
        videoids = [("download1", {})]
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = "some_dialog"
        downloader._getNextItemFromQueue = Mock()
        downloader._getNextItemFromQueue.side_effect = lambda: videoids.pop()

        downloader._processQueue()

        assert(downloader._getNextItemFromQueue.call_count == 1)

    def test_processQueue_should_call_setPaths(self):
        sys.modules["__main__"].settingsdummy.getLocalizedString.return_value = "some_message"
        progress = Mock()
        progress().create = Mock()
        sys.modules["DialogDownloadProgress"].DownloadProgress = progress
        video = ({"videoid":"some_id", "Title":"some_title", "stream_map":"some_map", "url": "http://some_url", "path_complete": "", "path_incomplete": ""}, 200)
        videoids = [False, ("download1", video)]
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = ""
        downloader._setPaths = Mock()
        downloader._downloadURL = Mock()
        downloader._downloadURL.return_value = video
        downloader._getNextItemFromQueue = Mock()
        downloader._getNextItemFromQueue.side_effect = lambda: videoids.pop()

        downloader._processQueue()

        downloader._setPaths.assert_called_with("download1", video)

    def test_processQueue_should_create_a_DownloadProgress_dialog(self):
        sys.modules["__main__"].settingsdummy.getLocalizedString.return_value = "some_message"
        progress = Mock()
        progress().create = Mock()
        sys.modules["DialogDownloadProgress"].DownloadProgress = progress
        video = ({"videoid": "some_id", "Title": "sometitle", "path_complete": "", "path_incomplete": ""}, 200)
        videoids = [False, ("download1", {"videoid":"some_id", "Title":"some_title", "stream_map":"some_map", "url": "http://some_url", "path_complete": "", "path_incomplete": ""})]
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = ""
        downloader._setPaths = Mock()
        downloader._downloadURL = Mock()
        downloader._downloadURL.return_value = video
        downloader._getNextItemFromQueue = Mock()
        downloader._getNextItemFromQueue.side_effect = lambda: videoids.pop()

        downloader._processQueue()

        progress().create.assert_called_with("some_message", "")

    def test_processQueue_should_show_error_message_if_player_cant_find_video(self):
        sys.modules["__main__"].settingsdummy.getLocalizedString.return_value = "some_message"

        videoids = [False, ("download1", {"bad_url": "no_url", "path_complete": "", "path_incomplete": ""})]
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = ""
        downloader._setPaths = Mock()
        downloader._downloadURL = Mock()
        downloader._getNextItemFromQueue = Mock()
        downloader._getNextItemFromQueue.side_effect = lambda: videoids.pop()
        downloader._showMessage = Mock()

        downloader._processQueue()
        print sys.modules["__main__"].settingsdummy.getLocalizedString.call_args_list
        assert(downloader._downloadURL.call_count == 0)
        downloader._showMessage.assert_called_with("some_message", "some_message")
        assert(sys.modules["__main__"].settingsdummy.getLocalizedString.call_count == 3)

    def test_processQueue_should_remove_video_from_queue_if_player_cant_find_video(self):
        video = ({"apierror": "some_error"}, 303)
        videoids = [False, ("download1", {"videoid":"some_id", "Title":"some_title", "stream_map":"some_map", "apierror": "some_error", "path_complete": "", "path_incomplete": ""})]
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = ""
        downloader._setPaths = Mock()
        downloader._downloadURL = Mock()
        downloader._downloadURL.return_value = video
        downloader._getNextItemFromQueue = Mock()
        downloader._getNextItemFromQueue.side_effect = lambda: videoids.pop()
        downloader._removeItemFromQueue = Mock()

        downloader._processQueue()

        assert(downloader._downloadURL.call_count == 0)
        assert(downloader._removeItemFromQueue.call_args[0][0] == "download1")
        assert(downloader._removeItemFromQueue.call_count == 1)

    def test_processQueue_should_get_new_video_from_queue_if_player_cant_find_video(self):
        video = ({"apierror": "some_error"}, 303)
        videoids = [False, ("download1", {"videoid": "some_id", "path_complete": "", "path_incomplete": ""})]
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = ""
        downloader._setPaths = Mock()
        downloader._downloadURL = Mock()
        downloader._downloadURL.return_value = video
        downloader._getNextItemFromQueue = Mock()
        downloader._getNextItemFromQueue.side_effect = lambda: videoids.pop()

        downloader._processQueue()

        assert(downloader._getNextItemFromQueue.call_count == 2)
        print downloader._downloadURL.call_count
        assert(downloader._downloadURL.call_count == 0)

    def test_processQueue_should_call_downloadURL_if_http_is_found(self):
        video = {"videoid": "some_id", "Title": "some_title", "url": "http://some_url", "path_complete": "", "path_incomplete": ""}
        videoids = [False, ("download1", video)]
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = ""
        downloader._setPaths = Mock()
        downloader._downloadURL = Mock()
        downloader._downloadURL.return_value = 200
        downloader._getNextItemFromQueue = Mock()
        downloader._getNextItemFromQueue.side_effect = lambda: videoids.pop()

        downloader._processQueue()

        downloader._downloadURL.assert_called_with("download1", video)

    def test_processQueue_should_call_downloadURL_if_ftp_is_found(self):
        video = {"videoid": "some_id", "Title": "some_title", "url": "ftp://some_url", "path_complete": "", "path_incomplete": ""}
        videoids = [False, ("download1", video)]
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = ""
        downloader._setPaths = Mock()
        downloader._downloadURL = Mock()
        downloader._downloadURL.return_value = 200
        downloader._getNextItemFromQueue = Mock()
        downloader._getNextItemFromQueue.side_effect = lambda: videoids.pop()

        downloader._processQueue()

        downloader._downloadURL.assert_called_with("download1", video)

    def test_processQueue_should_call_detect_streams_if_not_http_or_ftp(self):
        video = {"videoid": "some_id", "Title": "some_title", "url": "rtsp://some_url", "path_complete": "", "path_incomplete": "", "cmd_call": "mock"}
        videoids = [False, ("download1", video)]
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = ""
        downloader._setPaths = Mock()
        downloader._detectStream = Mock()
        downloader._downloadStream = Mock()
        downloader._getNextItemFromQueue = Mock()
        downloader._getNextItemFromQueue.side_effect = lambda: videoids.pop()

        downloader._processQueue()

        downloader._detectStream.assert_called_with("download1", video)
        downloader._downloadStream.assert_called_with("download1", video)

    def test_processQueue_should_call_removeItemFromQueue_after_downloading(self):
        video = {"videoid": "some_id", "Title": "some_title", "url": "http://some_url", "path_complete": "", "path_incomplete": ""}
        videoids = [False, ("download1", video)]
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = ""
        downloader._setPaths = Mock()
        downloader._downloadURL = Mock()
        downloader._downloadURL.return_value = 200
        downloader._removeItemFromQueue = Mock()
        downloader._getNextItemFromQueue = Mock()
        downloader._getNextItemFromQueue.side_effect = lambda: videoids.pop()

        downloader._processQueue()

        downloader._downloadURL.assert_called_with("download1", video)
        assert(downloader._removeItemFromQueue.call_args[0][0] == "download1")
        assert(downloader._removeItemFromQueue.call_count == 1)

    def test_processQueue_should_call_getNextItemFromQueue_after_downloading(self):
        video = ({"videoid": "some_id", "Title": "some_title", "url": "http://some_url", "path_complete": "", "path_incomplete": ""}, 200)
        videoids = [False, ("download1", {"videoid": "some_id", "Title": "some_title", "url": "http://some_url", "path_complete": "", "path_incomplete": ""})]
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = ""
        downloader._setPaths = Mock()
        downloader._downloadURL = Mock()
        downloader._downloadURL.return_value = video
        downloader._getNextItemFromQueue = Mock()
        downloader._getNextItemFromQueue.side_effect = lambda: videoids.pop()

        downloader._processQueue()

        downloader._downloadURL.assert_called_with("download1", video[0])
        assert(downloader._getNextItemFromQueue.call_count == 2)

    def test_processQueue_should_call_dialog_close_when_processing_is_done(self):
        progress = Mock()
        progress().close = Mock()
        sys.modules["DialogDownloadProgress"].DownloadProgress = progress
        video = ({"videoid": "some_id", "Title": "sometitle", "path_complete": "", "path_incomplete": ""}, 200)
        videoids = [False, ("download1", {"videoid": "some_id", "Title": "some_title", "stream_map": "some_map", "url": "http://some_url", "download_path": "some_path", "path_complete": "", "path_incomplete": ""})]

        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = ""
        downloader._setPaths = Mock()
        downloader._downloadURL = Mock()
        downloader._downloadURL.return_value = video
        downloader._getNextItemFromQueue = Mock()
        downloader._getNextItemFromQueue.side_effect = lambda: videoids.pop()

        downloader._processQueue()

        progress().close.assert_called_with()

    def test__runCommand_should_callsubprocess_Popen(self):
        patcher = patch("subprocess.Popen")
        patcher.start()
        popen = Mock()
        popen.return_value = "TEST"
        import subprocess
        subprocess.Popen = popen

        downloader = self.SimpleDownloader.SimpleDownloader()
        args = ["program", "-tag", "link"]
        result = downloader._runCommand(args)
        patcher.stop()

        print repr(result)
        print popen.call_count

        assert(popen.call_count == 1)
        popen.assert_called_with(['program', '-tag', 'link'], stderr=-2, stdout=-1)

    def test__detectStream_should_set_vlc_cmd_call(self):
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader._showMessage = Mock()
        downloader._runCommand = Mock()
        downloader._readPipe = Mock()
        downloader._readPipe.return_value = "rtsp://url' successfully opened"
        p = Mock()
        p.poll.return_value = False
        downloader._runCommand.return_value = p
        item = {"videoid": "someid", "url": "rtsp://url", "Title": "some_title", "download_path": "some_path", "path_incomplete": "incomplete_path", "duration": 3}
        downloader._detectStream("filename", item)

        assert("cmd_call" in item)
        print repr(item["cmd_call"])
        assert("vlc" in item["cmd_call"])
        assert("-I" in item["cmd_call"])
        assert("dummy" in item["cmd_call"])
        assert("--sout" in item["cmd_call"])
        assert("file/avi:incomplete_path" in item["cmd_call"])
        assert("rtsp://url" in item["cmd_call"])
        assert("vlc://quit" in item["cmd_call"])
        assert("--stop-time" in item["cmd_call"])
        assert("3" in item["cmd_call"])
        assert("-v" in item["cmd_call"])
        assert(len(item["cmd_call"]) == 11)

    def test__detectStream_should_set_mplayer_cmd_call(self):
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader._showMessage = Mock()
        downloader._runCommand = Mock()
        downloader._readPipe = Mock()
        downloader._readPipe.return_value = "Starting playback"
        p = Mock()
        p.poll.side_effect = [True, False, True]
        downloader._runCommand.return_value = p
        item = {"videoid": "someid", "url": "mms://url", "Title": "some_title", "download_path": "some_path", "path_incomplete": "incomplete_path", "use_mplayer": "true"}
        downloader._detectStream("filename", item)

        print repr(item)
        assert("cmd_call" in item)
        print repr(item["cmd_call"])
        assert("mplayer" in item["cmd_call"])
        assert("-v" in item["cmd_call"])
        assert("-dumpstream" in item["cmd_call"])
        assert("-dumpfile" in item["cmd_call"])
        assert("incomplete_path" in item["cmd_call"])
        assert("mms://url" in item["cmd_call"])
        assert(len(item["cmd_call"]) == 6)

    def test__detectStream_should_set_rtmpdump_cmd_call(self):
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader._showMessage = Mock()
        downloader._runCommand = Mock()
        downloader._readPipe = Mock()
        downloader._readPipe.return_value = "Starting"
        p = Mock()
        p.poll.return_value = False
        downloader._runCommand.return_value = p
        item = {"videoid": "someid", "url": "rtmp://url", "Title": "some_title", "download_path": "some_path", "path_incomplete": "incomplete_path", "live": "true", "duration": 3, "player_url": "http://player.swf", "token": "my_token"}
        downloader._detectStream("filename", item)

        print repr(item)
        assert("cmd_call" in item)
        assert("rtmpdump" in item["cmd_call"])
        assert("--rtmp" in item["cmd_call"])
        assert("rtmp://url" in item["cmd_call"])
        assert("--flv" in item["cmd_call"])
        assert("incomplete_path" in item["cmd_call"])
        assert("--live" in item["cmd_call"])
        assert("--stop" in item["cmd_call"])
        assert("3" in item["cmd_call"])
        assert("--swfVfy" in item["cmd_call"])
        assert("http://player.swf" in item["cmd_call"])
        assert("--token" in item["cmd_call"])
        assert("my_token" in item["cmd_call"])
        assert(len(item["cmd_call"]) == 12)

    def test_downloadStream_should_get_size_and_download(self):
        ospatcher = patch("os.path.getsize")
        ospatcher.start()
        import os
        os.path.getsize = Mock()
        os.path.getsize.return_value = 1234

        patcher = patch("subprocess.Popen")
        patcher.start()
        import subprocess
        popen = Mock()
        communicate = Mock()
        communicate.communicate.return_value = ("", "filesize    1234568\n")
        communicate.stdout.read.return_value = "out"
        communicate.returncode = None
        popen.return_value = communicate
        subprocess.Popen = popen
        sys.modules["__main__"].xbmcvfs.exists.return_value = True

        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader._showMessage = Mock()
        downloader._updateProgress = Mock()
        downloader._downloadStream("filename", {"videoid": "someid", "url": "rtmp://url", "Title": "some_title", "download_path": "some_path", "path_incomplete": "incomplete_path", "total_size": 1234.0, "cmd_call": ['rtmpdump', '-r', 'rtmp://url', '-o', 'incomplete_path']})

        ospatcher.stop()
        patcher.stop()

        result = popen.call_args_list[0][0][0]
        print repr(result)
        assert("rtmpdump" in result)
        assert("-r" in result)
        assert("rtmp://url" in result)
        assert("-o" in result)
        assert("incomplete_path" in result)
        assert(len(result) == 5)

    def test_downloadStream_should_timeout_on_stall(self):
        ospatcher = patch("os.path.getsize")
        ospatcher.start()
        import os
        os.path.getsize = Mock()
        os.path.getsize.return_value = 1234

        patcher = patch("subprocess.Popen")
        patcher.start()
        import subprocess
        popen = Mock()
        communicate = Mock()
        communicate.communicate.return_value = ("", "filesize    1234568\n")
        communicate.returncode = None
        popen.return_value = communicate
        subprocess.Popen = popen
        sys.modules["__main__"].xbmcvfs.exists.return_value = True

        downloader = self.SimpleDownloader.SimpleDownloader()
        communicate.stdout.read.return_value = "out"
        downloader._showMessage = Mock()
        downloader._updateProgress = Mock()
        downloader._downloadStream("filename", {"videoid": "someid", "url": "rtmp://url", "Title": "some_title", "download_path": "some_path", "path_incomplete": "incomplete_path", "total_size": 12340.0, "cmd_call": ['rtmpdump', '-r', 'rtmp://url', '-o', 'incomplete_path']})

        ospatcher.stop()
        patcher.stop()

        result = popen.call_args_list[0][0][0]
        print repr(result)
        assert("rtmpdump" in result)
        assert("-r" in result)
        assert("rtmp://url" in result)
        assert("-o" in result)
        assert("incomplete_path" in result)
        assert(len(result) == 5)

    def test_downloadURL_should_download_file_to_temporary_path(self):
        sys.modules["__main__"].common.makeUTF8.return_value = "testing/filename"
        url_patcher = patch("urllib2.urlopen")
        url_patcher.start()
        import urllib2
        dummy_connection = Mock()
        dummy_connection.read.return_value = ""
        dummy_connection.geturl.return_value = ""
        dummy_connection.info().getheader.return_value = ""

        url_patcher(urllib2.urlopen).return_value = dummy_connection
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = Mock()
        input = {"videoid": "someid", "url": "http://some_url", "Title": "some_title", "download_path": "some_path", "path_complete": "", "path_incomplete": "testing/filename"}

        downloader._downloadURL("filename", input)

        url_patcher.stop()
        sys.modules["__main__"].settingsdummy.getAddonInfo.return_value = "tmp"
        sys.modules["__main__"].common.openFile.assert_called_with('testing/filename', 'wb')

    def test__setPaths_should_update_paths(self):
        sys.modules["__main__"].common.makeUTF8.return_value = "filename"
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = Mock()
        video = {"videoid": "someid", "url": "some_url", "Title": "some_title", "download_path": "mypath"}

        downloader._setPaths("filename", video)

        print repr(video)

        assert(video["path_incomplete"] == 'testing/filename')
        assert(video["path_complete"] == 'mypath/filename')

    def test__setPaths_should_check_if_file_exists_before_downloading_and_delete_if_it_does(self):
        sys.modules["__main__"].common.makeUTF8.return_value = "filename"
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = Mock()
        video = {"videoid": "someid", "url": "some_url", "Title": "some_title", "download_path": "mypath"}

        downloader._setPaths("filename", video)

        sys.modules["__main__"].xbmcvfs.exists.assert_called_with('testing/filename')
        sys.modules["__main__"].xbmcvfs.delete.assert_called_with('testing/filename')

    def test__processQueue_should_move_file_to_download_path_when_finished(self):
        sys.modules["__main__"].common.makeUTF8.return_value = "filename"
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = Mock()
        input = {"videoid": "someid", "url": "http://some_url", "Title": "some_title", "download_path": "mypath", "path_complete": "", "path_incomplete": ""}

        downloader._downloadURL = Mock()
        downloader._downloadURL.return_value = 200
        downloader._getNextItemFromQueue = Mock()
        downloader._getNextItemFromQueue.side_effect = [("filename", input), False]

        downloader._processQueue()

        sys.modules["__main__"].xbmcvfs.rename.assert_called_with('testing/filename', 'mypath/filename')

    def test_downloadURL_should_call_con_info_getHeader_to_get_file_size(self):
        sys.modules["__main__"].common.openFile = Mock()
        url_patcher = patch("urllib2.urlopen")
        url_patcher.start()
        import urllib2
        dummy_connection = Mock()
        dummy_connection.read.return_value = ""
        dummy_connection.geturl.return_value = ""
        dummy_connection.info().getheader.return_value = ""
        url_patcher(urllib2.urlopen).return_value = dummy_connection
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = Mock()
        input = {"videoid": "someid", "url": "http://some_url", "Title": "some_title", "download_path": "some_path", "path_complete": "", "path_incomplete": ""}

        downloader._downloadURL("filename", input)

        url_patcher.stop()
        dummy_connection.info().getheader.assert_called_with("Content-Length")

    def test_downloadURL_should_call_con_read_with_correct_chunk_size(self):
        sys.modules["__main__"].common.openFile = Mock()
        url_patcher = patch("urllib2.urlopen")
        url_patcher.start()
        import urllib2
        dummy_connection = Mock()
        dummy_connection.read.return_value = ""
        dummy_connection.geturl.return_value = ""
        dummy_connection.info().getheader.return_value = "1000"
        url_patcher(urllib2.urlopen).return_value = dummy_connection
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = Mock()
        input = {"videoid": "someid", "url": "http://some_url", "Title": "some_title", "download_path": "some_path", "path_complete": "", "path_incomplete": ""}

        downloader._downloadURL("filename", input)

        url_patcher.stop()
        print repr(dummy_connection.call_count)
        dummy_connection.read.assert_called_with(8192)

    def test_downloadURL_should_call_read_until_stream_is_empty(self):
        url_patcher = patch("urllib2.urlopen")
        url_patcher.start()
        import urllib2
        dummy_connection = Mock()
        chunks = ["", "1", "2", "3", "4", "5"]
        dummy_connection.read.side_effect = lambda x: chunks.pop()
        dummy_connection.geturl.return_value = ""
        dummy_connection.info().getheader.return_value = "1000"
        url_patcher(urllib2.urlopen).return_value = dummy_connection
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = Mock()
        input = {"videoid": "someid", "url": "http://some_url", "Title": "some_title", "download_path": "some_path", "path_complete": "", "path_incomplete": ""}

        downloader._downloadURL("filename", input)

        url_patcher.stop()
        assert(dummy_connection.read.call_count == 6)
        dummy_connection.read.assert_called_with(8192)

    def test_downloadURL_should_fetch_download_queue_while_downloading(self):
        sys.modules["__main__"].common.openFile = Mock()
        url_patcher = patch("urllib2.urlopen")
        url_patcher.start()
        import urllib2
        dummy_connection = Mock()
        dummy_connection.read.return_value = ""
        dummy_connection.geturl.return_value = ""
        dummy_connection.info().getheader.return_value = "1000"
        self.ssdummy.get.return_value = ""
        url_patcher(urllib2.urlopen).return_value = dummy_connection
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = Mock()
        input = {"videoid": "someid", "url": "http://some_url", "Title": "some_title", "download_path": "some_path", "path_complete": "", "path_incomplete": ""}

        downloader._downloadURL("filename", input)

        url_patcher.stop()

        self.ssdummy.get.assert_called_with("SimpleDownloaderQueue")

    def test_downloadURL_should_calculate_progress(self):
        sys.modules["__main__"].common.openFile = Mock()
        url_patcher = patch("urllib2.urlopen")
        url_patcher.start()
        import urllib2
        dummy_connection = Mock()
        dummy_connection.read.return_value = ""
        dummy_connection.geturl.return_value = ""
        dummy_connection.info().getheader.return_value = "1000"
        self.ssdummy.get.return_value = ""
        url_patcher(urllib2.urlopen).return_value = dummy_connection
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = Mock()
        input = {"videoid": "someid", "url": "http://some_url", "Title": "some_title", "download_path": "some_path", "path_complete": "", "path_incomplete": ""}

        downloader._downloadURL("filename", input)

        url_patcher.stop()

        self.ssdummy.get.assert_called_with("SimpleDownloaderQueue")

    def test__updateProgress_should_call_dialog_update(self):
        sys.modules["__main__"].xbmc.Player().isPlaying.return_value = False
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = Mock()
        downloader.bytes_so_far = 0
        downloader.mark = 0
        downloader.queue_mark = 0
        item = {"percent": 10, "total_size": 1000}
        params = {"mark": 1.2, "bytes_so_far": 1234, "queue_mark": 0.2}
        downloader._updateProgress("filename", item, params)

        print repr(downloader.dialog.update.call_args_list)
        assert(downloader.dialog.update.call_args_list[0][1]["percent"] == 10)

    def test_downloadURL_should_close_connection_and_filehandle_when_done(self):
        sys.modules["__main__"].common.openFile = Mock()
        url_patcher = patch("urllib2.urlopen")
        url_patcher.start()
        import urllib2
        dummy_connection = Mock()
        dummy_connection.read.return_value = ""
        dummy_connection.geturl.return_value = ""
        dummy_connection.info().getheader.return_value = "1000"
        self.ssdummy.get.return_value = ""
        url_patcher(urllib2.urlopen).return_value = dummy_connection
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = Mock()
        input = {"videoid": "someid", "url": "http://some_url", "Title": "some_title", "download_path": "some_path", "path_complete": "", "path_incomplete": ""}

        downloader._downloadURL("filename", input)

        url_patcher.stop()

        dummy_connection.close.assert_called_with()
        sys.modules["__main__"].common.openFile().close.assert_called_with()

    def test_downloadURL_should_try_to_close_connection_and_filehandle_if_download_fails(self):
        sys.modules["__main__"].common.openFile = Mock()
        url_patcher = patch("urllib2.urlopen")
        url_patcher.start()
        import urllib2
        dummy_connection = Mock()
        dummy_connection.read.return_value = ""
        dummy_connection.geturl.return_value = ""
        dummy_connection.info().getheader.return_value = "1000"
        self.ssdummy.get.return_value = ""
        url_patcher(urllib2.urlopen).return_value = dummy_connection
        sys.modules["__main__"].common.openFile().write.side_effect = Exception("BOOM!")
        downloader = self.SimpleDownloader.SimpleDownloader()
        downloader.dialog = Mock()
        input = {"videoid": "someid", "url": "http://some_url", "Title": "some_title", "download_path": "some_path", "path_complete": "", "path_incomplete": ""}

        downloader._downloadURL("filename", input)

        url_patcher.stop()

        dummy_connection.close.assert_called_with()
        sys.modules["__main__"].common.openFile().close.assert_called_with()

    def test_getNextItemFromQueue_should_return_first_item(self):
        self.ssdummy.lock.return_value = True
        self.ssdummy.get.return_value = repr([("download1", {"videoid": "1"}), ("download2", {"videoid": "2"}), ("download3", {"videoid": "3"})])
        downloader = self.SimpleDownloader.SimpleDownloader()

        video = downloader._getNextItemFromQueue()

        print repr(video)

        self.ssdummy.lock.assert_any_call("SimpleDownloaderLock")
        assert(video[0] == "download1")

    def test_addItemToQueue_should_append_item(self):
        self.ssdummy.lock.return_value = True
        self.ssdummy.get.return_value = repr([("download1", {"videoid": "1"}), ("download2", {"videoid": "2"})])
        downloader = self.SimpleDownloader.SimpleDownloader()

        downloader._addItemToQueue("download3", {"videoid": "3"})

        self.ssdummy.lock.assert_called_with("SimpleDownloaderQueueLock")
        self.ssdummy.set.assert_called_with("SimpleDownloaderQueue", "[('download1', {'videoid': '1'}), ('download2', {'videoid': '2'}), ('download3', {'videoid': '3'})]")

    def test_addItemToQueue_move_existing_item_to_front(self):
        self.ssdummy.lock.return_value = True
        self.ssdummy.get.return_value = repr([("download1", {"videoid": "1"}), ("download2", {"videoid": "2"}), ("download3", {"videoid": "3"})])
        downloader = self.SimpleDownloader.SimpleDownloader()

        downloader._addItemToQueue("download3", {"videoid": "3"})

        self.ssdummy.lock.assert_called_with("SimpleDownloaderQueueLock")
        self.ssdummy.set.assert_called_with("SimpleDownloaderQueue", "[('download1', {'videoid': '1'}), ('download3', {'videoid': '3'}), ('download2', {'videoid': '2'})]")

    def test_movieDownloadToPosition_should_move_correctly(self):
        self.ssdummy.lock.return_value = True
        self.ssdummy.get.return_value = repr([("download1", {"videoid": "1"}), ("download2", {"videoid": "2"}), ("download3", {"videoid": "3"}), ("download4", {"videoid": "4"}), ("download5", {"videoid": "5"}), ("download6", {"videoid": "6"}), ("download7", {"videoid": "7"}), ("download8", {"videoid": "8"})])
        downloader = self.SimpleDownloader.SimpleDownloader()

        downloader.movieItemToPosition("download7", 1)

        self.ssdummy.lock.assert_called_with("SimpleDownloaderQueueLock")
        self.ssdummy.set.assert_called_with("SimpleDownloaderQueue", "[('download1', {'videoid': '1'}), ('download7', {'videoid': '7'}), ('download2', {'videoid': '2'}), ('download3', {'videoid': '3'}), ('download4', {'videoid': '4'}), ('download5', {'videoid': '5'}), ('download6', {'videoid': '6'}), ('download8', {'videoid': '8'})]")

    def test_removeItemFromQueue_should_remove_correct_item(self):
        self.ssdummy.lock.return_value = True
        self.ssdummy.get.return_value = repr([("download1", {"videoid": "1"}), ("download2", {"videoid": "2"}), ("download3", {"videoid": "3"})])
        downloader = self.SimpleDownloader.SimpleDownloader()

        downloader._removeItemFromQueue("download1")

        self.ssdummy.lock.assert_called_with("SimpleDownloaderQueueLock")
        self.ssdummy.set.assert_called_with("SimpleDownloaderQueue", "[('download2', {'videoid': '2'}), ('download3', {'videoid': '3'})]")

    def test_plugin_isRTMPInstalled_should_match(self):
        patcher = patch("subprocess.Popen")
        patcher.start()
        import subprocess
        popen = Mock()
        communicate = Mock()
        communicate.communicate = Mock()
        communicate.communicate.return_value = ("", "RTMPDump")
        popen.return_value = communicate
        subprocess.Popen = popen

        downloader = self.SimpleDownloader.SimpleDownloader()
        result = downloader.isRTMPInstalled()

        patcher.stop()

        print repr(result)
        assert(result)

    def test_plugin_isVLCInstalled_should_match(self):
        patcher = patch("subprocess.Popen")
        patcher.start()
        import subprocess
        popen = Mock()
        communicate = Mock()
        communicate.communicate = Mock()
        communicate.communicate.return_value = ("VLC", "")
        popen.return_value = communicate
        subprocess.Popen = popen

        downloader = self.SimpleDownloader.SimpleDownloader()
        result = downloader.isVLCInstalled()

        patcher.stop()

        print repr(result)
        assert(result)

    def test_plugin_isMPlayerInstalled_should_match(self):
        patcher = patch("subprocess.Popen")
        patcher.start()
        import subprocess
        popen = Mock()
        communicate = Mock()
        communicate.communicate = Mock()
        communicate.communicate.return_value = ("MPlayer", "")
        popen.return_value = communicate
        subprocess.Popen = popen

        downloader = self.SimpleDownloader.SimpleDownloader()
        result = downloader.isMPlayerInstalled()

        patcher.stop()

        print repr(result)
        assert(result)

    def test_plugin_isRTMPInstalled_should_fail(self):
        patcher = patch("subprocess.Popen")
        patcher.start()
        import subprocess
        popen = Mock()
        communicate = Mock()
        communicate.communicate = Mock()
        communicate.communicate.return_value = ("", "")
        popen.return_value = communicate
        subprocess.Popen = popen

        downloader = self.SimpleDownloader.SimpleDownloader()
        result = downloader.isRTMPInstalled()

        patcher.stop()

        print repr(result)
        assert(not result)

    def test_plugin_isVLCInstalled_should_fail(self):
        patcher = patch("subprocess.Popen")
        patcher.start()
        import subprocess
        popen = Mock()
        communicate = Mock()
        communicate.communicate = Mock()
        communicate.communicate.return_value = ("", "")
        popen.return_value = communicate
        subprocess.Popen = popen

        downloader = self.SimpleDownloader.SimpleDownloader()
        result = downloader.isVLCInstalled()

        patcher.stop()

        print repr(result)
        assert(not result)

    def test_plugin_isMPlayerInstalled_should_fail(self):
        patcher = patch("subprocess.Popen")
        patcher.start()
        import subprocess
        popen = Mock()
        communicate = Mock()
        communicate.communicate = Mock()
        communicate.communicate.return_value = ("", "")
        popen.return_value = communicate
        subprocess.Popen = popen

        downloader = self.SimpleDownloader.SimpleDownloader()
        result = downloader.isMPlayerInstalled()

        patcher.stop()

        print repr(result)
        assert(not result)


if __name__ == '__main__':
        nose.runmodule()
