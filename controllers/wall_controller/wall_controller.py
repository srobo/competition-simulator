from typing import List

from controller import Node, Supervisor

# Velocity matrices contain linear and rotational velocities [x, y, z, rot_x, rot_y, rot_z]
linear_downwards = [0, -0.3, 0, 0, 0, 0]


class WallController:
    def __init__(self, wall_time: int) -> None:
        self._robot = Supervisor()
        self.wall_time = wall_time
        self.walls: List[Node] = [
            self._robot.getFromDef('moving_wall1'),
            self._robot.getFromDef('moving_wall2'),
        ]

    def main(self) -> None:
        # wait for the walls to start moving in ms
        self._robot.step(self.wall_time * 1000)

        print('Moving arena walls')  # noqa: T001
        for wall in self.walls:
            wall.setVelocity(linear_downwards)

        # wait for the walls to reach their final location
        self._robot.step(1000)

        for wall in self.walls:
            wall.resetPhysics()


if __name__ == "__main__":
    wall_controller = WallController(0)
    wall_controller.main()
