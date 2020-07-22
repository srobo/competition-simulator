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
    pip install -r libraries.txt
    ```

   Note: you can change the version of Python which Webots uses from the UI --
   go to "Tools" > "Preferences" > "General" > "Python command".

   We are using Python 3.7, though it shouldn't matter whether it's a system
   install or a virtual environment.

2. Create a file `robot_mode.txt` in the root of the repo which contains just
   the text `comp`:

    ``` bash
    echo comp > robot_mode.txt
    ```

3. Run

    ```bash
    competition-simulator/script/prepare-comp-match <directory containing team code> <match number> <Zone 0 TLA> <Zone 1 TLA> <Zone 2 TLA> <Zone 3 TLA>
    ```

    Using a dash instead of a TLA if a robot is not present. This provides filenames and sets up the directory structure:

    ``` plain
    .
    ├── competition-simulator
    │   ├── controllers
    │   ├── ...
    │   ├── robot_mode.txt
    │   └── worlds
    ├── zone-0
    |   ├── log-zone-0-match-<match number>.txt
    │   └── robot.py
    └── zone-2
        ├── log-zone-2-match-<match number>.txt
        └── robot.py
    ```

4. Start webots from the command line using:

    ```bash
    webots --mode=pause
    ```
5. Got to File > Make Movie
   Choose: Resolution: 1920x1080, Quality: 100, Video acceleration: 1.0

6. Press Ctrl + 2 to start simulation

7. After match complete robots will stop moving, press esc.
   Wait for video to finish processing and saving before closing webots

8. Copy logs into `competition-simulator/recordings/yyy-mm-dd/match-<match number>/logs`

9. Close webots and repeat for next match
