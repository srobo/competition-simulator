from controller import Robot

# Allow up to two changes per second
MAX_FREQUENCY = 2

MIN_TIME_BETWEEN_CHANGES = 1 / MAX_FREQUENCY


class OutputFrequencyLimiter:
    def __init__(self, webot: Robot) -> None:
        self._webot = webot
        self._last_change: float = 0

    def can_change(self) -> bool:
        now = self._webot.getTime()
        diff = now - self._last_change

        # Changes within a timestep always all happen during the same
        # render cycle and therefore cannot contribute to additional strobing.
        # It's therefore safe to allow several changes within the same timestep.
        if diff == 0:
            return True

        if diff < MIN_TIME_BETWEEN_CHANGES:
            return False

        # Assume the caller went ahead with the change
        self._last_change = now
        return True
