# competition-simulator
A simulator to be used for the Student Robotics Virtual Competition 2020

## Installation instructions

1. Download and install the [Webots IDE](https://cyberbotics.com/#download)
2. Install Python >=3.5
3. Clone this `competition-simulator` repo
4. In the Webots IDE, open `/worlds/Arena.wbt`

## Overview

Within the IDE, there are a few different panels:

- In the centre of your screen is the 3D simulated view of the arena
- On the left is a tree heirarchy of all elements in this "world"
- At the bottom is your console
- At the top are your general controls which include the time controls. Press the centre play button to run the simulation at normal speed.

**Important:** Changes to the world must happen with the simulation paused at 0:00. If e.g. you move an object at a different time, rewinding back to the start will delete your changes.

On first run, the robot will execute an example program. On first run, this will be copied to the directory `competition-simulator` is stored in to make updating easier:

```
.
├── competition-simulator
│   ├── controllers
│   │   ├── example_controller
│   │   └── sr_controller
│   ├── ...
│   └── worlds
└── robot.py
```
