// Stepper bridge for the smart telescope.
//
// Listens on USB serial for the line protocol documented in README.md and
// drives two A4988 carriers. Every line is echoed as "OK <cmd>" or
// "ERR <reason>", so the Pi can detect a lost step instead of assuming one.
//
// Board: any AVR/ESP32 with 6 free GPIO. Pins below are for a Nano/Uno.

#include <Arduino.h>

struct Axis {
  uint8_t stepPin;
  uint8_t dirPin;
  uint8_t enablePin;
};

Axis AZ  = {2, 3, 4};
Axis ALT = {5, 6, 7};

const uint8_t STEP_HIGH_US = 5;     // A4988 needs >= 1 us; 5 is safe
const unsigned long MAX_STEP_US = 10000;

Axis* axisByName(const String& name) {
  if (name == "AZ") return &AZ;
  if (name == "ALT") return &ALT;
  return nullptr;
}

void setup() {
  Serial.begin(115200);
  for (Axis* a : {&AZ, &ALT}) {
    pinMode(a->stepPin, OUTPUT);
    pinMode(a->dirPin, OUTPUT);
    pinMode(a->enablePin, OUTPUT);
    digitalWrite(a->enablePin, HIGH);   // active low: start disabled
    digitalWrite(a->stepPin, LOW);
  }
  Serial.println("READY");
}

void loop() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.length() == 0) return;

  int firstSpace = line.indexOf(' ');
  String verb = line.substring(0, firstSpace);
  String rest = firstSpace < 0 ? "" : line.substring(firstSpace + 1);
  rest.trim();

  if (verb == "EN") {
    bool on = rest.toInt() == 1;
    digitalWrite(AZ.enablePin, on ? LOW : HIGH);
    digitalWrite(ALT.enablePin, on ? LOW : HIGH);
    Serial.println("OK EN");
    return;
  }

  int secondSpace = rest.indexOf(' ');
  String name = rest.substring(0, secondSpace);
  String arg = secondSpace < 0 ? "" : rest.substring(secondSpace + 1);
  Axis* axis = axisByName(name);
  if (axis == nullptr) { Serial.println("ERR axis"); return; }

  if (verb == "DIR") {
    digitalWrite(axis->dirPin, arg.toInt() == 1 ? HIGH : LOW);
    Serial.println("OK DIR");
  } else if (verb == "STEP") {
    unsigned long highUs = arg.toInt();
    if (highUs == 0 || highUs > MAX_STEP_US) { Serial.println("ERR width"); return; }
    digitalWrite(axis->stepPin, HIGH);
    delayMicroseconds(highUs);
    digitalWrite(axis->stepPin, LOW);
    Serial.println("OK STEP");
  } else {
    Serial.println("ERR verb");
  }
}
