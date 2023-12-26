if __name__ == "__main__":
    from pyno.com import check_connected_board_info
    from time import sleep
    from pyno.ino import (
        ArduinoConnecter,
        ArduinoFlicker,
        ArduinoSetting,
        PinMode,
    )

    LED_BUILTIN = 13

    available_board = check_connected_board_info()
    arduino_uno = list(
        filter(lambda board: board.board == "Arduino Uno", available_board)
    )[0]

    uno_setting = ArduinoSetting.derive_from_portinfo(arduino_uno).apply_setting(
        {"baudrate": 115200}
    )
    connecter = ArduinoConnecter(uno_setting).write_sketch().connect()

    flicker = ArduinoFlicker(connecter)
    flicker.pin_mode(LED_BUILTIN, PinMode.OUTPUT)

    print("Flick 13 pin for 1s with 10 hz")
    flicker.flick_for(LED_BUILTIN, 10, 1000)
    sleep(2.0)
    print("Flick 13 pin for 2s with 10 hz")
    flicker.flick_on(LED_BUILTIN, 10, 10000)
    sleep(2.0)
    flicker.flick_off()
