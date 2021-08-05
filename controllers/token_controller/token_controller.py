import sys
import struct
from typing import Dict
from pathlib import Path

# Webots specific library
from controller import Emitter, Supervisor

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(1, str(REPO_ROOT / 'modules'))

from sr.robot.utils import get_robot_device  # isort:skip
from shared_utils import TOKENS, TargetInfo, TargetType  # isort:skip


BROADCASTS_PER_SECOND = 10


class TokenController:

    _emitters: Dict[TargetInfo, Emitter]

    def __init__(self) -> None:
        self._robot = Supervisor()

        self._emitters = {
            code: get_robot_device(
                self._robot,
                f'{code.owner.name}_{code.id} Emitter',
                Emitter,
            )
            for code in TOKENS
            if code.type == TargetType.CONTAINER
        }

        self._emitters.update({
            code: get_robot_device(
                self._robot,
                f'BEACON_{code.id} Emitter',
                Emitter,
            )
            for code in TOKENS
            if code.type == TargetType.BEACON
        })

    def transmit_pulses(self) -> None:
        for token_code, emitter in self._emitters.items():
            emitter.send(
                struct.pack(
                    "!bBb",
                    int(token_code.type),
                    token_code.id,
                    int(token_code.owner),
                ),
            )

    def main(self) -> None:
        broadcast_spacing = int(1000 / BROADCASTS_PER_SECOND)
        while True:
            self.transmit_pulses()
            self._robot.step(broadcast_spacing)


if __name__ == "__main__":
    token_controller = TokenController()
    token_controller.main()
