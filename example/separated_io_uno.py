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
    available_boards = check_connected_board_info()
    for i, board in zip(range(len(available_boards)), available_boards):
        setting = ArduinoSetting.derive_from_portinfo(board)
        if i == 0:
            setting.apply_setting({"mode": Mode.alo})
        else:
            setting.apply_setting({"mode": Mode.readeruno})
        ArduinoConnecter(setting).write_sketch()

    # Connect to arduino
    available_boards = check_connected_board_info()
    for i, board in zip(range(len(available_boards)), available_boards):
        setting = ArduinoSetting.derive_from_portinfo(board)
        if i == 0:
            setting.apply_setting({"mode": Mode.alo, "baudrate": 115200})
            flicker = ArduinoFlicker(ArduinoConnecter(setting).connect())
            flicker.pin_mode(5, PinMode.OUTPUT)
        else:
            setting.apply_setting(
                {"baudrate": 1000000, "mode": Mode.readeruno, "timeout": 1.0}
            )
            reader = ArduinoLineReader(ArduinoConnecter(setting).connect())

    flicker.flick_for(5, 5.0, 5000)
    count = 0
    while count < 10:
        v = reader.readline()
        if v is None:
            count += 1
            continue
        print(v.decode("utf-8"))
