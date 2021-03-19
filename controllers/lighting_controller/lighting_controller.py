"""
The controller for altering arena lighting provided by a DirectionalLight and a Background
Currently doesn't support:
- Overlapping lighting fades
- Timed pre-match lighting changes
"""
import sys
from typing import List, Tuple, Optional, NamedTuple
from pathlib import Path

from controller import Node, Supervisor

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(1, str(REPO_ROOT / 'modules'))

import controller_utils  # isort:skip
import webots_utils  # isort:skip


class ArenaLighting(NamedTuple):
    intensity: float = 3.5
    colour: Tuple[float, float, float] = (1, 1, 1)
    luminosity: float = 0.35


class LightingEffect(NamedTuple):
    start_time: float  # Negative start times are relative to the end of the match
    # Negative values 0 - (-0.08) don't get included in the produced recordings
    fade_time: Optional[float] = None
    lighting: ArenaLighting = ArenaLighting()
    name: str = ""

    def __repr__(self) -> str:
        return (
            f"<LightingEffect: \"{self.name}\", "
            f"start={self.start_time}, fade={self.fade_time}, "
            f"int={self.lighting.intensity}, col={self.lighting.colour}, "
            f"lum={self.lighting.intensity}>"
        )


CUE_STACK = [
    LightingEffect(0, lighting=ArenaLighting(intensity=1, luminosity=0.15), name="Pre-set"),
    LightingEffect(0, fade_time=3, name="Fade-up"),
    LightingEffect(-0.1, lighting=ArenaLighting(colour=(1, 0, 0)), name="End of match"),
]


class LightingController:
    def __init__(self, duration: float, cue_stack: List[LightingEffect]) -> None:
        self._robot = Supervisor()
        self.timestep = self._robot.getBasicTimeStep()
        self.start_offset: float = 0

        self.duration = duration
        self.cue_stack = cue_stack

        self.sun_node = webots_utils.node_from_def(self._robot, 'SUN')
        self.ambient_node = webots_utils.node_from_def(self._robot, 'AMBIENT')

    def set_node_luminosity(self, node: Node, luminosity: float) -> None:
        node.getField('luminosity').setSFFloat(luminosity)

    def set_node_intensity(self, node: Node, intensity: float) -> None:
        node.getField('intensity').setSFFloat(intensity)

    def set_node_colour(self, node: Node, colour: Tuple[float, float, float]) -> None:
        node.getField('color').setSFColor(list(colour))

    def get_current_lighting_values(self) -> ArenaLighting:
        return ArenaLighting(
            self.sun_node.getField('intensity').getSFFloat(),
            tuple(self.sun_node.getField('color').getSFColor()),  # type: ignore
            self.ambient_node.getField('luminosity').getSFFloat(),
        )

    def increment_colour(
        self,
        colour: Tuple[float, float, float],
        step: Tuple[float, float, float],
    ) -> Tuple[float, float, float]:
        return tuple(colour[i] + step[i] for i in range(3))  # type: ignore

    def current_match_time(self) -> float:
        return self._robot.getTime() - self.start_offset

    def remaining_match_time(self) -> float:
        return self.duration - self.current_match_time()

    def do_lighting_effect(self, effect: LightingEffect) -> None:
        print(  # noqa: T001
            f"Running lighting effect: {effect.name} @ {self.current_match_time()}",
        )

        if effect.fade_time is None:
            self.set_node_intensity(self.sun_node, effect.lighting.intensity)
            self.set_node_colour(self.sun_node, effect.lighting.colour)
            self.set_node_luminosity(self.ambient_node, effect.lighting.luminosity)
        else:
            (  # get starting values
                current_intensity,
                current_colour,
                current_luminosity,
            ) = self.get_current_lighting_values()

            # figure out steps of each value
            steps = int((effect.fade_time * 1000) / self.timestep)
            intensity_step = (effect.lighting.intensity - current_intensity) / steps
            colour_step: Tuple[float, float, float] = tuple(  # type: ignore
                effect.lighting.colour[i] - current_colour[i]
                for i in range(3)
            )
            luminosity_step = (effect.lighting.luminosity - current_luminosity) / steps

            for step in range(steps - 1):  # loop through for fade time
                self.set_node_intensity(self.sun_node, current_intensity)
                self.set_node_colour(self.sun_node, current_colour)
                self.set_node_luminosity(self.ambient_node, current_luminosity)

                current_intensity += intensity_step
                current_colour = self.increment_colour(current_colour, colour_step)
                current_luminosity += luminosity_step
                self._robot.step(int(self.timestep))

            # directly set final values to remove accumulated errors
            self.set_node_intensity(self.sun_node, effect.lighting.intensity)
            self.set_node_colour(self.sun_node, effect.lighting.colour)
            self.set_node_luminosity(self.ambient_node, effect.lighting.luminosity)

            print(f"Lighting effect '{effect.name}' complete")  # noqa: T001

    def schedule_lighting(self) -> None:
        if controller_utils.get_robot_mode() != 'comp':
            return

        print('Scheduled cues:')  # noqa: T001
        for cue in self.cue_stack:
            print(cue)  # noqa: T001

        # run pre-start snap changes
        for cue in self.cue_stack:
            if cue.start_time == 0 and cue.fade_time is None:
                self.do_lighting_effect(cue)
                self.cue_stack.remove(cue)

        # Interact with the supervisor "robot" to wait for the start of the match.
        while self._robot.getCustomData() != 'start':
            self._robot.step(int(self.timestep))

        self.start_offset = self._robot.getTime()

        while self.cue_stack:
            for cue in self.cue_stack:
                if (
                    cue.start_time >= 0 and
                    self.current_match_time() >= cue.start_time
                ):  # cue relative to start
                    self.do_lighting_effect(cue)
                    self.cue_stack.remove(cue)
                elif (
                    cue.start_time < 0 and
                    self.remaining_match_time() <= -(cue.start_time)
                ):  # cue relative to end
                    self.do_lighting_effect(cue)
                    self.cue_stack.remove(cue)

                self._robot.step(int(self.timestep))


if __name__ == "__main__":
    lighting_controller = LightingController(
        controller_utils.get_match_duration_seconds(),
        CUE_STACK,
    )
    lighting_controller.schedule_lighting()
