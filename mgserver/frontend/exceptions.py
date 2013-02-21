class CreateClientException(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return repr("{} already exist".format(self.name))


class SignupException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
