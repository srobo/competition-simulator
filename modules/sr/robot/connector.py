from controller import Robot, Connector as WebotsConnector
from sr.robot.utils import get_robot_device


class Connector:
    def __init__(self, webot: Robot):
        self._connector = get_robot_device(webot, "Crane Connector", WebotsConnector)
        self._connector.enablePresence(int(webot.getBasicTimeStep()))

    @property
    def lock(self) -> bool:
        """
        Get the current lock state of the connector. This does not indicate
        whether a physical connection has been successfully made.
        """
        return self._connector.isLocked()

    @lock.setter
    def lock(self, value: bool) -> None:
        if value:
            self._connector.lock()
        else:
            self._connector.unlock()

    def nearby(self) -> bool:
        """
        Detect if a compatible connector is in range. While this is true,
        locking the connector will form a physical connection to the other connector.
        """
        return self._connector.getPresence() == 1
