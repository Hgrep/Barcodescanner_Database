"""
scanner.py

Service to manage barcode scans for books.

Data Inputs:
- code (str): A scanned barcode or ISBN string.

Data Outputs:
- start(): Activates scanning and clears the current buffer.
- stop(): Deactivates scanning and returns all scanned codes.
- add_scan(code): Adds a scanned code to the buffer if scanning is active.
"""
class ScannerService:
    """
    Service that manages scanned barcodes in a buffer.
    Allows starting, stopping, and adding scans.
    """

    def __init__(self):
        """
        Initialize the scanner with an empty buffer and inactive state.
        """
        self.buffer = []
        self.active = False

    def start(self):
        """
        Start scanning: clears the current buffer and sets active state to True.

        Returns:
            None
        """
        self.buffer.clear()
        self.active = True

    def stop(self):
        """
        Stop scanning: sets active state to False and returns all scanned codes.

        Returns:
            list[str]: List of scanned barcode/ISBN strings
        """
        self.active = False
        return self.buffer

    def add_scan(self, code):
        """
        Add a scanned code to the buffer if scanning is active.

        Args:
            code (str): The scanned barcode or ISBN

        Returns:
            None
        """
        if self.active:
            self.buffer.append(code.strip())
