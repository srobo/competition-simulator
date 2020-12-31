# competition-simulator

A simulator to be used for the Student Robotics Virtual Competition

## Installation instructions

Take a look at [the docs](https://studentrobotics.org/docs/simulator/#installation).

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

## Development setup

In addition to the basic setup for running the simulator, if you are intending
to work on our wrapper API, our controllers or other helper scripts then you
should also install the linting requirements:

``` shell
pip install -r script/linting/requirements.txt
pip install -r script/typing/requirements.txt
```

You can then run all linting/type checking/tests in one go using `script/check`.

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

2. Launch webots and configure it for recordings:

    - close the robot-camera overlays which appear on top of the main view

    - in "Tools" > "Preferences" > "OpenGL" set:

        - Ambient Occlusion to Disabled,
        - Texture Quality to High,
        - Disable shadows to false, and
        - Disable anti-aliasing to false

   Then close webots.

3. Run the match:

    ```bash
    competition-simulator/script/run-comp-match <directory containing team code> <match number> <Zone 0 TLA> <Zone 1 TLA> <Zone 2 TLA> <Zone 3 TLA>
    ```

    Using a dash instead of a TLA if a robot is not present.

    This will orchestrate everything to run the match, including running webots
    and collecting together the logs and recordings. The logs & recordings will
    be within the directory which contains the team code, as follows:
    - The teams' logs will be in a directory named for their TLA
    - The match file (suitable for SRComp) will be within a `matches` directory
    - The recordings will be within a `recordings` directory

    Note: you may see an error like the following regarding the video creation:
    ``` plain
    [libx264 @ 0x562cf1ba9840] Error: 2pass curve failed to converge
    [libx264 @ 0x562cf1ba9840] target: 20250.00 kbit/s, expected: 3339.51 kbit/s, avg QP: 0.0252
    [libx264 @ 0x562cf1ba9840] try reducing target bitrate
    ```
    This warns that we have requested a higher bit-rate from the video than is
    possible given the images the simulation generates. It does not appear to
    create any issues with the rendered videos, though you are encouraged to
    check that your setup is recording the videos correctly.
