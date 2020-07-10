# competition-simulator

A simulator to be used for the Student Robotics Virtual Competition 2020

## Installation instructions

Take a look at [the docs](https://studentrobotics.org/docs/competition-simulator/#installation).

## Overview

Within the IDE, there are a few different panels:

- In the centre of your screen is the 3D simulated view of the arena
- On the left is a tree hierarchy of all elements in this "world"
- At the bottom is your console
- At the top are your general controls which include the time controls. Press the centre play button to run the simulation at normal speed.

**Important:** Changes to the world must happen with the simulation paused at 0:00. If e.g. you move an object at a different time, rewinding back to the start will delete your changes.

On first run, the robot will execute an example program. On first run, this will be copied to the directory `competition-simulator` is stored in to make updating easier:

``` plain
.
├── competition-simulator
│   ├── controllers
│   │   ├── example_controller
│   │   └── sr_controller
│   ├── ...
│   └── worlds
└── robot.py
```

## Doing a release

1. Create a new tag & push
2. Wait for CI to build a zip archive
3. Upload the archive to the GitHub release for the tag
4. Update the [docs](https://github.com/srobo/docs) to point to the new archive
5. Announce the update to teams via the forums and [email](https://github.com/srobo/team-emails)

## Running competition matches

In order to run competition matches you'll need to:

1. Install the third party libraries the teams are depending on, into the same
   Python environment as will be running their code:

    ``` bash
    pip install libraries.txt
    ```

2. Create a file `robot_mode.txt` in the root of the repo which contains just
   the text `comp`:

    ``` bash
    echo comp > robot_mode.txt
    ```

3. Put the competitors' code into the right places for each of the corner zones.
   These are folder `zone-X` for each zone number `X` which are siblings to the
   directory in which this git repo is checked out:

    ``` plain
    .
    ├── competition-simulator
    │   ├── controllers
    │   ├── ...
    │   ├── robot_mode.txt
    │   └── worlds
    ├── zone-0
    |   └── robot.py
    └── zone-2
        └── robot.py
    ```

4. Load the simulation afresh and let it run. This does not need to be a fresh
   launch of the Webots simulator program, but does need to be a fresh load of
   the world.
   There is a supervisor "robot" in the simulation which will remove any robots
   for which there is no competitor code and pause the simulation at the end of
   the match. The only way to restore the robots is to reload the simulation
   between matches.
