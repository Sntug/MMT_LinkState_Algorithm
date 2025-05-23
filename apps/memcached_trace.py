class MemcachedTrace:
    def __init__(self, time, func, key, value=0):  # func: 0 = set, 1 = get
        self.time, self.func, self.key, self.value = time, func, key, value

    def __str__(self):
        if self.func == 0:
            return f"{self.time} {self.func} {self.key} {self.value}"
        else:
            return f"{self.time} {self.func} {self.key}"
