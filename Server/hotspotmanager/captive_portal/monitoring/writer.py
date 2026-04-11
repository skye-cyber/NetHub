import os
from pathlib import Path


class Writer:
    def __init__(self, file):
        self.file = file

    def write(self, data) -> str:
        if self.dir_exists():
            self.create_file()

        with open(self.file, 'w') as f:
            f.write(">>>>>>>>>>>>>New Log>>>>>>>>>>\n")
            f.write(f"{data}\n")

        return self.file

    def read(self) -> str:
        with open(self.file, 'w') as f:
            return f.read()

    def file_exists(self) -> bool:
        return (Path(self.file).parent).exists()

    def dir_exists(self) -> bool:
        return os.path.exists(self.file)

    def create_file(self) -> bool:
        (Path(self.file).parent).mkdir(parents=True, exist_ok=True)
        return True


writer = Writer('/home/skye/NetHub/backend/hotspotmanager/captive_portal/monitoring/monitoring.log')
