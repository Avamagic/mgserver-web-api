class ApiException(Exception):
    def __init__(self, code=500, msg=""):
        self.code = code
        self.msg = msg
