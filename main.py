# cd /home/sodiumtf/Downloads/Programming/PythonScripts/squareMatch

# Imports
import pygame, random, math, serial, time, sys
# Global Constants
SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 9600
DELAY = 30
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 500
MIN_SCALE = 10.0
MAX_SCALE = 100.0
MIN_ROT = 0.0
MAX_ROT = math.pi / 2.0
START_TIME_WINDOW = 10.0
TIME_LOSS_PER_SCORE = 0.1
MIN_TIME_WINDOW = 5.0
START_ALLOTED_ERROR = 0.10
LENIENCE_LOSS_PER_SCORE = 0.05

# Square Object
class Square:
    # Constructor
    def __init__(self, arg_x:int=0, arg_y:int=0, arg_rot:float=MIN_ROT, arg_scale:float=MIN_SCALE):
        self.x = arg_x
        self.y = arg_y
        self.rot = arg_rot
        self.scale = arg_scale
    # Draw Square to Window
    def draw(self, window):
        # Generate Vertices
        p1_x = round(self.x + self.scale * math.cos(self.rot) + self.scale * math.sin(self.rot))
        p1_y = round(self.y + self.scale * math.sin(self.rot) - self.scale * math.cos(self.rot))
        p2_x = round(self.x + self.scale * math.cos(self.rot) - self.scale * math.sin(self.rot))
        p2_y = round(self.y + self.scale * math.sin(self.rot) + self.scale * math.cos(self.rot))
        p3_x = round(self.x - self.scale * math.cos(self.rot) - self.scale * math.sin(self.rot))
        p3_y = round(self.y - self.scale * math.sin(self.rot) + self.scale * math.cos(self.rot))
        p4_x = round(self.x - self.scale * math.cos(self.rot) + self.scale * math.sin(self.rot))
        p4_y = round(self.y - self.scale * math.sin(self.rot) - self.scale * math.cos(self.rot))
        # Draw Lines Between Points
        pygame.draw.line(window, (255, 255, 255), (p1_x, p1_y), (p2_x, p2_y))
        pygame.draw.line(window, (255, 255, 255), (p2_x, p2_y), (p3_x, p3_y))
        pygame.draw.line(window, (255, 255, 255), (p3_x, p3_y), (p4_x, p4_y))
        pygame.draw.line(window, (255, 255, 255), (p4_x, p4_y), (p1_x, p1_y))

def get_goal_square(goal_square:Square, window):
    # Generate Scale
    goal_square.scale = random.uniform(MIN_SCALE, MAX_SCALE)
    # Generate Rotation
    goal_square.rot = random.uniform(MIN_ROT, MAX_ROT)
    # Store Max Side Length based on Scale and Rotation
    max_side = round(goal_square.scale * math.cos(goal_square.rot) + goal_square.scale * math.sin(goal_square.rot))
    # Generate Point Center 
    goal_square.x = random.randint(WINDOW_WIDTH // 2 + max_side, WINDOW_WIDTH - max_side)
    goal_square.y = random.randint(0 + max_side, WINDOW_HEIGHT - max_side)
    # Draw Goal Square
    goal_square.draw(window)

def get_user_square(user_square:Square, window, arduino):
    # Empty Serial and Fill Square Values
    while(arduino.in_waiting > 0):
        # Take in a Full Line
        line = arduino.readline().decode("utf-8").strip()
        # Confirm Line was Filled
        if line:
            # Split Line
            user_square.x, user_square.y, user_square.rot, user_square.scale = line.split()
            # Type Conversion
            user_square.x = round(float((user_square.x)))
            user_square.y = round(float((user_square.y)))
            user_square.rot = float(user_square.rot)
            user_square.scale = float(user_square.scale)
    # Draw User Square
    user_square.draw(window)

def calculate_difficulty(score):
    # Time Window Calculation
    time_window = START_TIME_WINDOW - score * TIME_LOSS_PER_SCORE
    if(time_window < MIN_TIME_WINDOW):
        time_window = MIN_TIME_WINDOW
    # Alloted Error Calculation
    alloted_error = START_ALLOTED_ERROR * (math.e ** (-1 * LENIENCE_LOSS_PER_SCORE * score))
    # Return Adjusted Difficulty
    return time_window, alloted_error

def reset():
    # Return Defaults
    return 0, START_TIME_WINDOW, START_ALLOTED_ERROR

def main():
    # Serial Setup
    arduino = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    time.sleep(2)
    arduino.reset_input_buffer()
    # Initialize Pygame
    pygame.init()
    # Window Creation
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Square Match")
    # Draw Borders (Offsets by 1 because Pygame starts pixels on the bottom right side of the pixel, so 1000 doesn't show)
    pygame.draw.line(window, (255, 255, 255), (WINDOW_WIDTH / 2, WINDOW_HEIGHT - 1), (WINDOW_WIDTH / 2, 0))
    pygame.draw.line(window, (255, 255, 255), (0, 0), (WINDOW_WIDTH, 0))
    pygame.draw.line(window, (255, 255, 255), (0, 0), (0, WINDOW_HEIGHT - 1))
    pygame.draw.line(window, (255, 255, 255), (0, WINDOW_HEIGHT - 1), (WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1))
    pygame.draw.line(window, (255, 255, 255), (WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1), (WINDOW_WIDTH - 1, 0))
    # Game Variables
    run = True
    goal_square = Square()
    user_square = Square()
    square_match = False
    score = 0
    time_window = START_TIME_WINDOW
    time_start = 0.0
    current_time = 0.0
    alloted_error = START_ALLOTED_ERROR
    percent_error = 0.0
    # Stay in Game Loop until Quit
    while(run):
        # Check for Quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        # Update Score File
        with open("score.txt", "w", encoding="utf-8") as file:
            file.write("SCORE: ")
            file.write(str(score))
            file.write("\n")
        # Mark the Square as Not Matching
        square_match = False
        # Generate Goal Square
        get_goal_square(goal_square, window)
        # Write Goal Square to Serial
        arduino.write(f"{goal_square.x} {goal_square.y} {goal_square.rot:.8f} {goal_square.scale:.8f}\n".encode("utf-8"))
        # Give Arduino time to Receive 
        pygame.time.wait(DELAY)
        # Mark Start of Time Window
        time_start = current_time = time.perf_counter()
        # Loop while Squares aren't matching and Time Window isn't expired
        while(square_match == False and (current_time - time_start) <= time_window):
            # Check for Quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    break
            # Mark Current Time
            current_time = time.perf_counter()
            # Get User Square
            get_user_square(user_square, window, arduino)
            # Calculate Percent Error / Match
            percent_error = (
                ((abs(user_square.x + (WINDOW_WIDTH / 2.0) - goal_square.x) / (WINDOW_WIDTH / 2.0)) + 
                 (abs(user_square.y - goal_square.y) / WINDOW_HEIGHT) + 
                 (abs(math.log(user_square.scale / goal_square.scale) / math.log(MAX_SCALE / MIN_SCALE))) + 
                 (math.pi/4.0 - abs((abs(user_square.rot - goal_square.rot) % (math.pi/2.0)) - math.pi/4.0)) / (math.pi/4.0))
            ) / 4.0
            if(percent_error < alloted_error):
                square_match = True
            else:
                print(percent_error)
            # Update
            pygame.display.update()
            window.fill((0, 0, 0), (1, 1, 498, 498))
            # Give time to cool down
            pygame.time.wait(DELAY)
        # Check for Loss
        if(percent_error > alloted_error):
            # Give Player (and Arduino) Time to Process
            time.sleep(5)
            # Reset Variables
            score, time_window, alloted_error = reset()
        # If Success
        else:
            # Increment Score
            score += 1
            # Scale Difficulty
            time_window, alloted_error = calculate_difficulty(score)
        # Clear Goal Square
        window.fill((0, 0, 0), ((WINDOW_WIDTH / 2) + 1, 1, 498, 498))

# Run Main
if __name__ == "__main__":
    main()
# Exit Program
pygame.quit()
sys.exit()