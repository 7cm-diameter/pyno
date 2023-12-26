if __name__ == "__main__":
    from pyno.com import check_connected_board_info
    from pyno.ino import (
        ArduinoFlicker,
        ArduinoLineReader,
        ArduinoConnecter,
        ArduinoSetting,
        Mode,
        PinMode,
    )

    # Upload sketch to arduino
    for board in check_connected_board_info():
        setting = ArduinoSetting.derive_from_portinfo(board)
        if board.board == "Arduino Due (Native USB Port)":
            setting.apply_setting({"mode": Mode.readerdue})
        ArduinoConnecter(setting).write_sketch()

    # Connect to arduino
    for board in check_connected_board_info():
        setting = ArduinoSetting.derive_from_portinfo(board).apply_setting(
            {"baudrate": 115200}
        )
        if board.board == "Arduino Uno":
            arduino_uno = ArduinoFlicker(ArduinoConnecter(setting).connect())
            arduino_uno.pin_mode(5, PinMode.OUTPUT)
        else:
            setting.apply_setting(
                {"baudrate": 1000000, "mode": Mode.readerdue, "timeout": 1.0}
            )
            arduino_due = ArduinoLineReader(ArduinoConnecter(setting).connect())

    arduino_uno.flick_for(5, 5.0, 5000)
    count = 0
    while count < 10:
        v = arduino_due.readline()
        if v is None:
            count += 1
            continue
        print(v.decode("utf-8"))
