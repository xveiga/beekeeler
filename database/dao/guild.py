class BotGuild:
    def __init__(
        self,
        gid: int,
        control_channel: int = None,
    ):
        self._gid = gid
        self._control_channel = control_channel

    @property
    def gid(self):
        return self._gid

    @property
    def control_channel(self):
        return self._control_channel
