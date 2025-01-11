import os
import subprocess
import signal

class MpvPlayer:
    def __init__(self):
        self.__subprocess = None
        self.os = 'win' if ('WSL2' in os.uname().release or 'MINGW' in os.uname().release) else 'gnu/linux'
        self.player_command = self.__get_player_command()

    def __get_player_command(self):
        return 'mpv.exe' if self.os == 'win' else 'mpv'

    def close_player(self):
        if isinstance(self.__subprocess, subprocess.Popen):
                os.kill(self.__subprocess.pid, signal.SIGTERM)
        self.__subprocess = None

    def player_video(self, title, video_url):
        if isinstance(self.__subprocess, subprocess.Popen):
            self.close_player()
        cmd = [self.player_command,"--fs","--keep-open=no",f"--title='{title}'", video_url]
        self.__subprocess = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
