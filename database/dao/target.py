class BotTarget:
    def __init__(self, gid: int, uid: int, issuer: int):
        self._gid = gid
        self._uid = uid
        self._issuer = issuer

    @property
    def gid(self):
        return self._gid

    @property
    def uid(self):
        return self._uid

    @property
    def issuer(self):
        return self._issuer
