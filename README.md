# competition-simulator

[![Github Actions](https://github.com/srobo/competition-simulator/workflows/Simulator%20tests/badge.svg)](https://github.com/srobo/competition-simulator/actions?query=workflow%3A%22Simulator+tests%22)
[![Github Actions](https://github.com/srobo/competition-simulator/workflows/Simulator%20match/badge.svg)](https://github.com/srobo/competition-simulator/actions?query=workflow%3A%22Simulator+match%22)

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

## Development

In addition to the basic setup for running the simulator, if you are intending
to work on our wrapper API, our controllers or other helper scripts then you
should also install the linting requirements:

``` shell
pip install -r script/linting/requirements.txt
pip install -r script/typing/requirements.txt
```

You can then run all linting/type checking/tests in one go using `script/check`.

### Running Webots

While the default location that our controllers look for `robot.py` files is the
directory above the repo, that is not particularly convenient for development.
Instead you may wish to run Webots having set the `ARENA_ROOT` environment
variable to a suitable location. This is also how `run-comp-match` configures
the arena to use when it runs matches.

For example, you may find it convenient to have a `robots` directory within the
repo and then have a number of code and arena directories within that:

```
robots
├── arena  # A development arena with a single (symlinked) robot
│   └── robot.py -> ../ultrasounds/robot.py
├── brakes-arena  # A competition style arena with two robots
│   ├── zone-0
│   │   └── robot.py
│   └── zone-1
│       └── robot.py
├── dancer  # Some robot code for a robot which dances
│   └── robot.py
├── single-arena  # A competition style arena with a single (symlinked) robot
│   └── zone-0 -> ../dancer/
└── ultrasounds  # Some robot code for testing ultrasound sensors
    └── robot.py
```

Given a setup like the above, running Webots such that it picks up on one of the
arena directories is possible through setting the `ARENA_ROOT` to an absolute
path when launching the webots process:

```
$ ARENA_ROOT=$PWD/robots/brakes-arena webots --mode=pause worlds/Arena.wbt
```

This will launch Webots using our world file, with the simulation paused and the
controllers (when started) will use the robots within `brakes-arena`.

Note: `webots` has a number of useful command line flags which are quite useful.
We won't document them here, though you are encouraged to run `webots --help` to
explore them yourself.

### Competition Mode

In Competition Mode the simulation behaves slightly differently:
- the simulation exits after the game completes
- an animation recording is made of the simulation
- a video recording is made of the simulation

If a match is being run, then the log of score-impacting events is also output
into the match file.

Competition mode is enabled when a `robot_mode.txt` marker file is found in the
arena directory and that file contains only the text `comp`:

``` bash
echo comp > robot_mode.txt
```

The match file is a separate `match.json` file, also in the arena directory.
This file conforms to the [Proton](https://github.com/PeterJCLaw/proton) spec
and is used to enable integration with [SRComp][srcomp]. Primarily this file
captures score-relevant data for SRComp, however it also supports some other
keys which are useful in development. See the `MatchData` structure for details.

During an actual competition, matches will be run using the `run-comp-match`
script, which is documented below. Note however that it consumes robot code from
a Zip archive rather than a directory. Suitable archives contain a `robot.py` at
their root and thus can be created (for some team `ABC`) using:

```
zip ABC.zip robot.py
```

[srcomp]: https://github.com/PeterJCLaw/srcomp/wiki

## Doing a release

1. Create a new tag & push
2. Create a release for the tag
3. Wait for CI to build a zip archive and upload it to the release
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
    competition-simulator/script/run-comp-match <directory containing team code> <match number> <Zone 0 TLA> <Zone 1 TLA>
    ```

    Note: use a dash instead of a TLA if a robot is not present.

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

# Collecting up logs for the Discord bot
The `zip-comp-logs` command allows logs to be collated into a zip with certain combinations of match animations.
To create the zip file used by the discord bot to distribute the logs use the command:

```bash
./script/zip-comp-logs <archive-folder> <output-folder> --with-combined--animations all [--suffix=<zip-name-suffix> ]
```
Once the the zip files have been generated the zip file beginning "combined" can be used with the [discord bot](https://github.com/WillB97/discord-logs-uploader).
