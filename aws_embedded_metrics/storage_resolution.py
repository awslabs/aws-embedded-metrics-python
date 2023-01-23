from enum import Enum, EnumMeta


class StorageResolutionMeta(EnumMeta):
    def __contains__(self, item: object) -> bool:
        try:
            self(item)
        except (ValueError, TypeError):
            return False
        else:
            return True


class StorageResolution(Enum, metaclass=StorageResolutionMeta):
    STANDARD = 60
    HIGH = 1
