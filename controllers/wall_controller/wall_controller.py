from typing import List

from controller import Node, Supervisor

# Velocity matrices contain linear and rotational velocities [x, y, z, rot_x, rot_y, rot_z]
linear_downwards = [0, -0.3, 0, 0, 0, 0]

def main(wall_time: int) -> None:
    robot = Supervisor()
    walls: List[Node] = [
        robot.getFromDef('moving_wall1'),
        robot.getFromDef('moving_wall2'),
    ]

    # wait for the walls to start moving in ms
    robot.step(wall_time * 1000)

    print('Moving arena walls')  # noqa: T001
    for wall in walls:
        wall.setVelocity(linear_downwards)

    # wait for the walls to reach their final location
    robot.step(1000)

    for wall in walls:
        wall.resetPhysics()


if __name__ == "__main__":
    main(0)  # TODO decide the time that the walls should move
