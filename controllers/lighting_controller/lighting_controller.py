"""
The controller for altering arena lighting provided by a DirectionalLight and a Background
Currently doesn't support:
- Timed pre-match lighting changes
"""

from __future__ import annotations

import sys
from typing import NamedTuple
from pathlib import Path
from dataclasses import dataclass

from controller import Node, Supervisor

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(1, str(REPO_ROOT / 'modules'))

import controller_utils  # isort:skip
import webots_utils  # isort:skip


# Note: intensity at the end of the match needs to be non-zero so that the red
# colour shows.
NON_MATCH_LIGHTING_INTENSITY = 0.5
MATCH_LIGHTING_INTENSITY = 1.8


class ArenaLighting(NamedTuple):
    light_def: str
    intensity: float
    colour: tuple[float, float, float] = (1, 1, 1)


class LightingEffect(NamedTuple):
    start_time: float  # Negative start times are relative to the end of the match
    # Negative values 0 - (-0.08) don't get included in the produced recordings
    fade_time: float | None = None
    lighting: list[ArenaLighting] = [ArenaLighting('SUN', intensity=1)]
    luminosity: float = 0.35
    name: str = ""

    def __repr__(self) -> str:
        lights_info = [
            f"({light.light_def}, int={light.intensity}, col={light.colour})"
            for light in self.lighting
        ]
        return (
            f"<LightingEffect: {self.name!r}, "
            f"start={self.start_time}, fade={self.fade_time}, "
            f"lum={self.luminosity}, "
            f"{', '.join(lights_info)}"
            ">"
        )


@dataclass
class LightFade:
    light: Node
    remaining_steps: int
    intensity_step: float
    colour_step: tuple[float, float, float]
    current_intensity: float
    current_colour: tuple[float, float, float]
    effect: ArenaLighting


@dataclass
class LuminosityFade:
    remaining_steps: int
    luminosity_step: float
    current_luminosity: float
    final_luminosity: float


CUE_STACK = [
    LightingEffect(
        0,
        lighting=[ArenaLighting('SUN', intensity=NON_MATCH_LIGHTING_INTENSITY)],
        luminosity=0.05,
        name="Pre-set",
    ),
    LightingEffect(
        0,
        fade_time=1.5,
        lighting=[ArenaLighting('SUN', intensity=MATCH_LIGHTING_INTENSITY)],
        name="Fade-up",
    ),
    LightingEffect(
        -0.1,
        lighting=[
            ArenaLighting(
                'SUN',
                intensity=NON_MATCH_LIGHTING_INTENSITY,
                colour=(1, 0, 0),
            ),
        ],
        luminosity=0.05,
        name="End of match",
    ),
]


class LightingController:
    def __init__(self, duration: float, cue_stack: list[LightingEffect]) -> None:
        self._robot = Supervisor()
        self.timestep = self._robot.getBasicTimeStep()
        self.start_offset: float = 0

        self.duration = duration
        self.cue_stack = cue_stack

        self.ambient_node = webots_utils.node_from_def(self._robot, 'AMBIENT')

        self.luminosity_fade = LuminosityFade(0, 0, 0.35, 0.35)
        self.lighting_fades: list[LightFade] = []

        # fetch all nodes used in effects, any missing nodes will be flagged here
        self.light_nodes: dict[str, Node] = {}
        for cue in cue_stack:
            for light in cue.lighting:
                if self.light_nodes.get(light.light_def) is None:
                    self.light_nodes[light.light_def] = webots_utils.node_from_def(
                        self._robot,
                        light.light_def,
                    )

    def set_node_luminosity(self, node: Node, luminosity: float) -> None:
        node.getField('luminosity').setSFFloat(luminosity)

    def set_node_intensity(self, node: Node, intensity: float) -> None:
        node.getField('intensity').setSFFloat(intensity)

    def set_node_colour(self, node: Node, colour: tuple[float, float, float]) -> None:
        node.getField('color').setSFColor(list(colour))

    def get_current_luminosity(self) -> float:
        return self.ambient_node.getField('luminosity').getSFFloat()

    def get_current_lighting_values(self, light_def: str) -> ArenaLighting:
        light = self.light_nodes[light_def]
        return ArenaLighting(
            light_def,
            light.getField('intensity').getSFFloat(),
            light.getField('color').getSFColor(),  # type: ignore
        )

    def increment_colour(
        self,
        colour: tuple[float, float, float],
        step: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        return tuple(colour[i] + step[i] for i in range(3))  # type: ignore

    def current_match_time(self) -> float:
        return self._robot.getTime() - self.start_offset

    def remaining_match_time(self) -> float:
        return self.duration - self.current_match_time()

    def start_lighting_effect(self, effect: LightingEffect) -> None:
        print(  # noqa: T201
            f"Running lighting effect: {effect.name} @ {self.current_match_time()}",
        )

        if effect.fade_time is None:
            self.set_node_luminosity(self.ambient_node, effect.luminosity)
            for light in effect.lighting:
                self.set_node_intensity(self.light_nodes[light.light_def], light.intensity)
                self.set_node_colour(self.light_nodes[light.light_def], light.colour)

            print(f"Lighting effect '{effect.name}' complete")  # noqa: B028, T201

        else:
            steps = int((effect.fade_time * 1000) / self.timestep)

            # get starting values
            current_luminosity = self.get_current_luminosity()
            luminosity_step = (effect.luminosity - current_luminosity) / steps
            self.luminosity_fade = LuminosityFade(
                steps,
                luminosity_step,
                current_luminosity,
                effect.luminosity,
            )

            for light in effect.lighting:
                # get starting values
                (
                    _,
                    current_intensity,
                    current_colour,
                ) = self.get_current_lighting_values(light.light_def)

                # figure out steps of each value
                intensity_step = (light.intensity - current_intensity) / steps
                colour_step: tuple[float, float, float] = tuple(  # type: ignore
                    light.colour[i] - current_colour[i]
                    for i in range(3)
                )

                # add fade to queue to have steps processed
                self.lighting_fades.append(LightFade(
                    self.light_nodes[light.light_def],
                    steps,
                    intensity_step,
                    colour_step,
                    current_intensity,
                    current_colour,
                    light,
                ))

    def do_lighting_step(self) -> None:
        if self.luminosity_fade.remaining_steps != 0:
            self.luminosity_fade.current_luminosity += self.luminosity_fade.luminosity_step
            self.luminosity_fade.remaining_steps -= 1

            if self.luminosity_fade.remaining_steps == 0:  # final step
                self.luminosity_fade.current_luminosity = self.luminosity_fade.final_luminosity

            self.set_node_luminosity(
                self.ambient_node,
                self.luminosity_fade.current_luminosity,
            )

        for fade in self.lighting_fades:
            if fade.remaining_steps > 1:
                fade.current_intensity += fade.intensity_step
                fade.current_colour = self.increment_colour(
                    fade.current_colour,
                    fade.colour_step,
                )
                fade.remaining_steps -= 1

                self.set_node_intensity(fade.light, fade.current_intensity)
                self.set_node_colour(fade.light, fade.current_colour)
            else:
                self.set_node_intensity(fade.light, fade.effect.intensity)
                self.set_node_colour(fade.light, fade.effect.colour)

                print(f"Lighting effect for '{fade.effect.light_def}' complete")  # noqa: E501, B028, T201

                self.lighting_fades.remove(fade)  # remove completed fade

    def schedule_lighting(self) -> None:
        if controller_utils.get_robot_mode() != 'comp':
            return

        print('Scheduled cues:')  # noqa: T201
        for cue in self.cue_stack:
            print(cue)  # noqa: T201

        # run pre-start snap changes
        for cue in self.cue_stack.copy():
            if cue.start_time == 0 and cue.fade_time is None:
                self.start_lighting_effect(cue)
                self.cue_stack.remove(cue)

        # Interact with the supervisor "robot" to wait for the start of the match.
        while self._robot.getCustomData() != 'start':
            self._robot.step(int(self.timestep))

        self.start_offset = self._robot.getTime()

        while self.cue_stack:
            for cue in self.cue_stack.copy():
                if (
                    cue.start_time >= 0 and
                    self.current_match_time() >= cue.start_time
                ):  # cue relative to start
                    self.start_lighting_effect(cue)
                    self.cue_stack.remove(cue)

                elif (
                    cue.start_time < 0 and
                    self.remaining_match_time() <= -(cue.start_time)
                ):  # cue relative to end
                    self.start_lighting_effect(cue)
                    self.cue_stack.remove(cue)

            self.do_lighting_step()
            self._robot.step(int(self.timestep))


if __name__ == "__main__":
    lighting_controller = LightingController(
        controller_utils.get_match_duration_seconds(),
        CUE_STACK,
    )
    lighting_controller.schedule_lighting()
