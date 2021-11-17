class BotGuild:
    def __init__(
        self,
        gid: int,
        name: str,
        control_channel: int = None,
        bitrate_reduction_amount: int = 2e3,
        bitrate_reduction_interval: int = 2e3,
        min_bitrate: int = 8e3,
        enable: bool = False,
    ):
        self._gid = gid
        self._name = name
        self._control_channel = control_channel
        self._bitrate_reduction_amount = bitrate_reduction_amount
        self._bitrate_reduction_interval = bitrate_reduction_interval
        self._min_bitrate = min_bitrate
        self._enable = enable

    @property
    def gid(self):
        return self._gid

    @property
    def name(self):
        return self._name

    @property
    def control_channel(self):
        return self._control_channel

    @property
    def bitrate_reduction_amount(self):
        return self._bitrate_reduction_amount

    @property
    def bitrate_reduction_interval(self):
        return self._bitrate_reduction_interval

    @property
    def min_bitrate(self):
        return self._min_bitrate

    @property
    def enable(self):
        return self._enable
