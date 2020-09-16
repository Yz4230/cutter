from dataclasses import dataclass

@dataclass
class Clip:
    start: int
    end: int

    @property
    def duration(self):
        return self.end - self.start
