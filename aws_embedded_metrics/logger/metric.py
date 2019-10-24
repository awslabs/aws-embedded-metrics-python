class Metric(object):
    def __init__(self, value: float, unit: str = None):
        self.values = [value]
        self.unit = unit or "None"

    def add_value(self, value: float) -> None:
        self.values.append(value)
