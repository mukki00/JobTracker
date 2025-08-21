class DB_props:
    def __init__(self, user, password, dsn):
        self.user = user
        self.password = password
        self.dsn = dsn

    def get_connection_string(self):
        return f"{self.user}/{self.password}@{self.dsn}"

    def __str__(self):
        return f"DB_props(user={self.user}, dsn={self.dsn})"

    def __repr__(self):
        return self.__str__()