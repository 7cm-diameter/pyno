from enum import Enum
from time import sleep
from typing import Optional

from serial import Serial


class PortInfo(object):
    def __init__(self, rawinfo: dict):
        from serial.tools.list_ports import grep

        self._rawinfo = rawinfo
        _boardinfo: Optional[list[dict]] = rawinfo.get("matchingboards")
        portinfo: Optional[dict] = rawinfo.get("port")
        if _boardinfo is None or portinfo is None:
            # TODO: Use appropriate exception
            raise Exception()
        boardinfo: dict = _boardinfo[0]
        self.__board: Optional[str] = boardinfo.get("name")
        self.__fqbn: Optional[str] = boardinfo.get("fqbn")
        self.__port: Optional[str] = portinfo.get("address")
        if self.__port is not None:
            ports = list(grep(self.__port))
            if len(ports) > 0:
                self.__serial_number = ports[0].serial_number

    @property
    def board(self) -> Optional[str]:
        return self.__board

    @property
    def fqbn(self) -> Optional[str]:
        return self.__fqbn

    @property
    def port(self) -> Optional[str]:
        return self.__port

    @property
    def serial_number(self) -> Optional[str]:
        return self.__serial_number

    def __repr__(self) -> str:
        return f"{self.board} at {self.port}"

    def detail(self) -> dict:
        from yaml import safe_load
        from subprocess import check_output

        return safe_load(
            check_output(
                f"arduino-cli monitor -p {self.port} --describe --format yaml",
                shell=True,
            )
        )

    def to_dict(self) -> dict:
        return {"board": self.board, "port": self.port, "fqbn": self.fqbn}


def check_connected_board_info() -> list[PortInfo]:
    from yaml import safe_load
    from subprocess import check_output

    detected = safe_load(
        check_output("arduino-cli board list --format yaml", shell=True).decode("utf-8")
    )
    boards_raw_info = filter(lambda d: d["matchingboards"] != [], detected)
    return list(map(PortInfo, boards_raw_info))
