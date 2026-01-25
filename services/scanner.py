class ScannerService:
    def __init__(self):
        self.buffer = []
        self.active = False

    def start(self):
        self.buffer.clear()
        self.active = True

    def stop(self):
        self.active = False
        return self.buffer

    def add_scan(self, code):
        if self.active:
            self.buffer.append(code.strip())
