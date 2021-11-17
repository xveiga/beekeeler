class BotVoiceChannel:
    def __init__(self, gid: int, cid: int, br: int, bkill: bool = False):
        self._gid = gid
        self._cid = cid
        self._bitrate = br
        self._bkill = bkill

    @property
    def gid(self):
        return self._gid

    @property
    def cid(self):
        return self._cid

    @property
    def bitrate(self):
        return self._bitrate

    @property
    def bkill(self):
        return self._bkill
