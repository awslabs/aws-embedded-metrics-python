from enum import Enum


class Environments(Enum):
    Local = 1
    Lambda = 2
    Agent = 3
    EC2 = 4
    Unknown = -1
