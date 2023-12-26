from abc import ABCMeta, abstractmethod
from enum import Enum
from subprocess import check_output
from time import sleep
from typing import Optional

from serial import Serial

from pyno.com import PortInfo


class Mode(Enum):
    alo = "alo"
    readerdue = "reader_due"
    readeruno = "reader"
    user = "user"


class ArduinoSetting(dict):
    """A class store settings for a comport"""

    AVAILABLE_SETTINGS = ["port", "baudrate", "fqbn", "mode", "timeout", "sketch"]

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: Optional[int] = None,
        fqbn: Optional[str] = None,
        mode: Mode = Mode.alo,
        sketch: Optional[str] = None,
        setting: Optional[dict] = None,
    ):
        if mode is not Mode.user:
            from os.path import dirname, join, abspath

            inodir = join("ino", mode.value)
            sketch = join(dirname(abspath(__file__)), inodir)
        super().__init__(
            {
                "port": port,
                "baudrate": baudrate,
                "mode": mode,
                "fqbn": fqbn,
                "mode": mode,
                "sketch": sketch,
            }
        )
        if setting is not None:
            applicables = self.__extract_available_setting_from_dict(setting)
            self.update(applicables)

    def __extract_available_setting_from_dict(self, setting: dict) -> dict:
        return dict(
            filter(lambda kv: kv[0] in self.AVAILABLE_SETTINGS, setting.items())
        )  # extract items are applicable for `Comport` setting.

    def apply_setting(self, setting: dict) -> "ArduinoSetting":
        """Apply comport settings described in an instance of `dictionary`"""
        applicables = self.__extract_available_setting_from_dict(setting)
        self.update(applicables)
        return self

    @staticmethod
    def derive_from_portinfo(portinfo: PortInfo) -> "ArduinoSetting":
        """Construct `ArduinoSetting` from `PortInfo` class"""
        ardset = ArduinoSetting()
        applicables = ardset.__extract_available_setting_from_dict(portinfo.to_dict())
        ardset.update(applicables)
        return ardset


class PinMode(Enum):
    """pin mode used as an argument for `Arduino.pin_mode`"""

    INPUT = b"\x00"
    INPUT_PULLUP = b"\x01"
    SSINPUT = b"\x02"
    SSINPUT_PULLUP = b"\x03"
    OUTPUT = b"\x02"


class PinState(Enum):
    """pin state used as an argument for `Arduino.digital_write`"""

    LOW = b"\x10"
    HIGH = b"\x11"


def as_bytes(x: int, byte: int) -> bytes:
    return x.to_bytes(byte, "little")


class ArduinoConnecterBase(metaclass=ABCMeta):
    @abstractmethod
    def write_sketch(self) -> "ArduinoConnecterBase":
        pass

    @abstractmethod
    def connect(self) -> "ArduinoConnecterBase":
        pass

    @abstractmethod
    def close(self):
        pass


class ModeSetterBase(metaclass=ABCMeta):
    def pin_mode(self, pin: int, mode: PinMode):
        pass


class WriterBase(metaclass=ABCMeta):
    @abstractmethod
    def digital_write(self, pin: int, state: PinState):
        pass

    @abstractmethod
    def analog_write(self, pin: int, v: int):
        pass

    @abstractmethod
    def cancel_write(self):
        pass


class ReaderBase(metaclass=ABCMeta):
    @abstractmethod
    def digital_read(self, pin: int) -> PinState:
        pass

    @abstractmethod
    def analog_read(self, pin: int) -> bytes:
        pass

    @abstractmethod
    def cancel_read(self):
        pass


class LineReaderBase:
    @abstractmethod
    def readline(self) -> Optional[bytes]:
        pass


class FlickerBase(metaclass=ABCMeta):
    @abstractmethod
    def flick_for(self, pin: int, hz: float, millis: int):
        """Flicking the `pin` with the given `hz` for `millis`"""

    @abstractmethod
    def flick_on(self, pin: int, hz: float, millis: int):
        """Flicking the `pin` with the given `hz` until `millis` or calling `flick_off`"""

    def flick_off(self):
        """Stop flicking initiated with `flick_on` but not `flick_for`"""
        pass


class ArduinoConnecter(ArduinoConnecterBase):
    WARMUP = 2.0

    def __init__(self, setting: ArduinoSetting):
        self.__setting = setting
        mode = self.setting.get("mode")
        if mode is not None and mode is not Mode.user:
            from os.path import dirname, join, abspath

            inodir = join("ino", mode.value)
            sketch = join(dirname(abspath(__file__)), inodir)
            self.__setting.update({"sketch": sketch})
        self.__connection = None

    def __del__(self):
        self.close()

    def write_sketch(self) -> "ArduinoConnecter":
        sketch = self.setting.get("sketch")
        port = self.setting.get("port")
        fqbn = self.setting.get("fqbn")

        if None in [port, sketch, fqbn]:
            raise Exception()
        check_output(f"arduino-cli compile -b {fqbn} {sketch} -u -p {port}", shell=True)
        sleep(self.WARMUP)
        return self

    def connect(self, **kwargs) -> "ArduinoConnecter":
        """Open serial port with a given setting"""
        port: Optional[str] = self.setting.get("port")
        baudrate: Optional[int] = self.setting.get("baudrate")
        if port is None or baudrate is None:
            raise Exception()
        timeout: Optional[float] = self.setting.get("timeout")
        self.__connection = Serial(port, baudrate, timeout=timeout, **kwargs)
        sleep(self.WARMUP)
        return self

    def close(self):
        if self.connection is not None:
            if not self.connection.closed:
                self.connection.reset_input_buffer()
                self.connection.reset_output_buffer()
                self.connection.cancel_read()
                self.connection.cancel_write()
                self.connection.close()

    @property
    def connection(self) -> Optional[Serial]:
        return self.__connection

    @property
    def setting(self) -> ArduinoSetting:
        return self.__setting


class ArduinoModeSetter(ModeSetterBase):
    def __init__(self, connecter: ArduinoConnecter):
        if connecter.connection is None:
            raise Exception()
        self.__connecter = connecter
        self.__connection = connecter.connection

    @property
    def connection(self) -> Serial:
        return self.__connection

    def pin_mode(self, pin: int, mode: PinMode):
        """Set the mode of a pin.

        Parameters
        ----------
        pin: int
            Pin number

        mode: PinMode
            Mode to apply to the pin.
        """
        message = mode.value + as_bytes(pin, 1)
        self.connection.write(message)


class ArduinoWriter(WriterBase, ArduinoModeSetter):
    def __init__(self, connecter: ArduinoConnecter):
        super().__init__(connecter)

    def digital_write(self, pin: int, state: PinState) -> None:
        """Set HIGH or LOW to the specified pin.

        Parameters
        ----------
        pin: int
            Pin number.

        state: PinState
            HIGH or LOW. HIGH = 5v (or 3.3V) / LOW = 0V.
        """
        message = state.value + as_bytes(pin, 1)
        self.connection.write(message)

    def analog_write(self, pin: int, v: int) -> None:
        """Output PWM wave from specified pin.

        Parameters
        ----------
        pin: int
            pin number

        v: int
            Output voltage. `v` must be in bound from 0 - 255.
        """
        message = b"\x12" + as_bytes(pin, 1) + as_bytes(v, 1)
        self.connection.write(message)


class ArduinoReader(ReaderBase, ArduinoModeSetter):
    def __init__(self, connecter: ArduinoConnecter):
        super().__init__(connecter)

    def digital_read(self, pin: int, timeout: Optional[float] = None) -> PinState:
        """Read the state of specified pin.

        Parameters
        ----------
        pin: int
            pin number

        timeout: Optional[float] = None
            waiting time to read.

        Returns
        -------
        value: bytes
            Read value which denotes pin state.
        """
        message = b"\x20" + as_bytes(pin, 1)
        self.connection.write(message)
        if self.connection.read(1) == b"\x00":
            return PinState.LOW
        return PinState.HIGH

    def analog_read(
        self, pin: int, size: int = 0, timeout: Optional[float] = None
    ) -> bytes:
        """Read a value from specified analog pin.

        Parameters
        ----------
        pin: int
            pin number

        timeout: Optional[float] = None
            waiting time to read.

        Returns
        -------
        value: bytes
            Read value (ranged from 0 to 1023).
        """
        message = b"\x21" + as_bytes(pin, 1)
        self.connection.write(message)
        return self.connection.read(1)


class ArduinoLineReader(ArduinoModeSetter, LineReaderBase):
    def __init__(self, connecter: ArduinoConnecter):
        super().__init__(connecter)

    def readline(self) -> Optional[bytes]:
        """Read until end of line from serial port.

        Returns
        -------
        line: Optional[bytes]
            Read value as bytes or None if the readignis cancelled.
        """
        line: bytes = self.connection.readline()
        if line == b"":
            return None
        try:
            line.decode("utf-8")
        except UnicodeDecodeError:
            return None
        return line


class ArduinoFlicker(FlickerBase, ArduinoModeSetter):
    def __init__(self, connecter: ArduinoConnecter):
        super().__init__(connecter)

    def flick_for(self, pin: int, hz: float, millis: int):
        hz = int(hz * 10)
        message = b"\x13" + as_bytes(pin, 1) + as_bytes(hz, 1) + as_bytes(millis, 2)
        self.connection.write(message)

    def flick_on(self, pin: int, hz: float, millis: int):
        hz = int(hz * 10)
        message = b"\x14" + as_bytes(pin, 1) + as_bytes(hz, 1) + as_bytes(millis, 2)
        self.connection.write(message)

    def flick_off(self):
        message = b"\x19"
        self.connection.write(message)
