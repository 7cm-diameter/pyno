void setup() {
  Serial.begin(1000000);
  for (uint8_t i=2; i<=10; i++) {
    pinMode(i, INPUT);
  }
}

unsigned long int starttime;
unsigned long int current_times[9];
uint8_t previous_pin_state[9] = {0, 0, 0, 0, 0, 0, 0, 0, 0};
uint8_t current_pin_state[9] = {0, 0, 0, 0, 0, 0, 0, 0, 0};
uint8_t pin_numbers[9] = {2, 3, 4, 5, 6, 7, 8, 9, 10};
uint8_t number_of_channel = 5;
uint8_t i;

void loop() {
  starttime = micros();

  while(true) {
    for (i=0; i<number_of_channel; i++) {
      current_pin_state[i] = digitalRead(pin_numbers[i]);
      current_times[i] = micros();
    }
    for (i=0; i<number_of_channel; i++) {
      if (current_pin_state[i] & !previous_pin_state[i]) {
        Serial.print(pin_numbers[i]);
        Serial.println(current_times[i]-starttime);
      }
      previous_pin_state[i] = current_pin_state[i];
    }
  }

  /*
  while(true) {
    for (i=0; i<number_of_channel; i++) {
      if (digitalRead(pin_numbers[i])) {
        if (!previous_pin_state[i]) {
          SerialUSB.print(pin_numbers[i]);
          SerialUSB.println(micros()-starttime);
        }
        previous_pin_state[i] = 1;
      } else {
        previous_pin_state[i] = 0;
      }
    }
  }
  */
}
