#include <math.h>

// Enums
enum Gamestate{
  STATE_IDLE,
  STATE_INPUT
};

// Square Object
class Square{
  public:
    long x;
    long y;
    float rot;
    float scale;
    Square(): x {0}, y {0}, rot {0.0}, scale {0.0} {};
};

// Math Global Constants
const double e = 2.718281828459;

// Pin Global Constants
const int X = A4;
const int Y = A3;
const int ROT = A2;
const int SCALE = A1;

// Game Global Constants
const int BAUDRATE = 9600;
const int DELAY = 30;
const double WINDOW_WIDTH = 1000;
const double WINDOW_HEIGHT = 500;
const double MIN_SCALE = 10.0;
const double MAX_SCALE = 100.0;
const double MIN_ROT = 0.0;
const double MAX_ROT = PI / 2.0;
const long START_TIME_WINDOW = 10000;
const long TIME_LOSS_PER_SCORE = 100;
const long MIN_TIME_WINDOW = 5000;
const double START_ALLOTED_ERROR = 0.10;
const double LENIENCE_LOSS_PER_SCORE = 0.05;
const long RESET_TIME = 3000;

// Game Global Variables
Gamestate gameState;
Square goalSquare;
Square userSquare;
long rawx {0};
long rawy {0};
double rawRot {0};
double rawScale {0};
double percentError {0};
double allotedError {0.0};
int score {0};
unsigned long currentTime {0};
unsigned long timeStart {0};

void setup() {
  // Serial setup
  Serial.begin(BAUDRATE);

  // Initialize each potentiometer
  pinMode(X, INPUT);
  pinMode(Y, INPUT);
  pinMode(ROT, INPUT);
  pinMode(SCALE, INPUT);

  // Start by waiting for python serial message
  gameState = STATE_IDLE;
}

void loop() {
  // IDLE
  if(gameState == STATE_IDLE){
    // Mark Current Time
    currentTime = millis();
    // Reset Scores if in STATE_IDLE for too long
    if((currentTime- timeStart) > RESET_TIME){
      score = 0;
      allotedError = START_ALLOTED_ERROR;
      timeStart = millis();
    }
    // If Serial Message Found
    if(Serial.available() > 0){
      // Fill Goal Square with Values from Serial
      goalSquare.x = Serial.parseInt();
      goalSquare.y = Serial.parseInt();
      goalSquare.rot = Serial.parseFloat();
      goalSquare.scale = Serial.parseFloat();
      // Clear out Rest of Serial
      while(Serial.available() > 0) Serial.read();
      // Update Alloted Error
      allotedError = START_ALLOTED_ERROR * pow(e, (-1 * LENIENCE_LOSS_PER_SCORE * score));
      // Begin Detecting Input
      gameState = STATE_INPUT;
    }
  }
  // INPUT
  if(gameState == STATE_INPUT){
    // Get Raw Data
    rawx = analogRead(X);
    rawy = analogRead(Y);
    rawRot = analogRead(ROT);
    rawScale = analogRead(SCALE);
    // Remap to fit domain
    userSquare.rot = rawRot * (MAX_ROT) / (1023);
    userSquare.scale = MIN_SCALE + (rawScale / 1023.0) * (MAX_SCALE - MIN_SCALE);
    userSquare.x = map(rawx, 0, 1023, round(0 + userSquare.scale * cos(userSquare.rot) + userSquare.scale * sin(userSquare.rot)), round((double(WINDOW_WIDTH) / 2.0) - (userSquare.scale * cos(userSquare.rot) + userSquare.scale * sin(userSquare.rot))));
    userSquare.y = map(rawy, 0, 1023, round(0 + userSquare.scale * cos(userSquare.rot) + userSquare.scale * sin(userSquare.rot)), round(double(WINDOW_HEIGHT) - (userSquare.scale * cos(userSquare.rot) + userSquare.scale * sin(userSquare.rot))));
    // Write to Serial to update user_square in python
    Serial.print(userSquare.x); Serial.print(" ");
    Serial.print(userSquare.y); Serial.print(" ");
    Serial.print(userSquare.rot); Serial.print(" ");
    Serial.println(userSquare.scale);
    // Calculate Percent Error
    percentError = (
      ((abs(userSquare.x + (double(WINDOW_WIDTH) / 2.0) - goalSquare.x) / (double(WINDOW_WIDTH) / 2.0)) + 
      (abs(userSquare.y - goalSquare.y) / double(WINDOW_HEIGHT)) + 
      (abs(log(userSquare.scale / goalSquare.scale) / log(MAX_SCALE / MIN_SCALE))) + 
      ((PI/4) - abs(fmod(abs(userSquare.rot - goalSquare.rot), (PI/2)) - (PI/4))) / (PI/4)) 
    ) / 4.0;
    // On Success
    if(percentError < allotedError){
      // Increment Score
      score++;
      // Return to Idle State
      gameState = STATE_IDLE;
    }
    // Refresh
    delay(DELAY);
  }
}