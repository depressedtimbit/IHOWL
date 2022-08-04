

import arcade
import os
import math

SPRITE_SCALING = 1
GUI_SCALING = 0.5

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "IHOWL"

# Important constants for this example

# Speed limit
MAX_SPEED = 3.0
ANGLE_MAX_SPEED = 2.5
# How fast we accelerate
ACCELERATION_RATE = 0.1
ANGLE_ACCELERATION_RATE = 0.1
IMAGE_ROTATION = -90
# How fast to slow down after we let off the key
FRICTION = 0.02
ANGLE_FRICTION = 0.02


class Player(arcade.Sprite):

    def __init__(self, image, scale):
        """ Set up the player """

        # Call the parent init
        super().__init__(image, scale)

        # Create a variable to hold our speed. 'angle' is created by the parent
        self.speed = 0

    def update(self):
        # Convert angle in degrees to radians
        angle_rad = math.radians(self.angle)

        # Rotate the ship
        self.angle += self.change_angle

        # Use math to find our change based on our speed and angle
        self.center_x += -self.speed * math.sin(angle_rad)
        self.center_y += self.speed * math.cos(angle_rad)
        

class Pointer(arcade.Sprite):

    def __init__(self, image, scale):
        """ Set up the Pointer """

        # Call the parent init
        super().__init__(image, scale)

class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self, width, height, title):
        """
        Initializer
        """

        # Call the parent class initializer
        super().__init__(width, height, title)


        # Variables that will hold sprite lists
        self.player_list = None

        # Set up the player info
        self.player_sprite = None

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        
        self.mouse_raw_x = 0
        self.mouse_raw_y = 0
        
        # Set the background color
        arcade.set_background_color(arcade.color.BLACK)

    def setup(self):
        """ Set up the game and initialize the variables. """

        # Sprite lists
        self.player_list = arcade.SpriteList()
        self.pointer_list = arcade.SpriteList()

        # Set up the player
        self.player_sprite = Player("images/ship.png",SPRITE_SCALING)
        self.player_sprite.center_x = 50
        self.player_sprite.center_y = 50
        self.player_list.append(self.player_sprite)

        # Set up the pointer
        self.pointer_sprite = Pointer("images/pointer.png", GUI_SCALING)
        self.player_sprite.center_x = 50
        self.player_sprite.center_y = 50
        self.pointer_list.append(self.pointer_sprite)

        # Setup the Camera
        self.camera = arcade.Camera(self.width, self.height)

    def center_camera_to_player(self):
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (self.camera.viewport_height / 2)
        

        player_centered = screen_center_x, screen_center_y
        self.camera.move_to(player_centered)
    
    def on_draw(self):
        """
        Render the screen.
        """

        # This command has to happen before we start drawing
        arcade.start_render()

        # Activate Camera
        self.camera.use()   

        # Draw all the sprites.
        self.player_list.draw()
        self.pointer_list.draw()
        # Display speed
        arcade.draw_text("use your mouse to steer the ship", 10, 90, arcade.color.WHITE)
        arcade.draw_text("hold right click to move forward", 10, 70, arcade.color.WHITE)
        arcade.draw_text("hold left click to Shoot", 10, 50, arcade.color.WHITE)

    def on_update(self, delta_time):
        """ Movement and game logic """

        # Position the marker 
        self.pointer_sprite.center_x = self.mouse_raw_x + self.player_sprite.center_x - (self.camera.viewport_width / 2)
        self.pointer_sprite.center_y = self.mouse_raw_y + self.player_sprite.center_y - (self.camera.viewport_height / 2)

        # Player Position
        start_x = self.player_sprite.center_x
        start_y = self.player_sprite.center_y

        #get destination 
        dest_x = self.pointer_sprite.center_x
        dest_y = self.pointer_sprite.center_y

        # Do math to calculate how to get the sprite to the destination.
        # Calculation the angle in radians between the start points
        # and end points. This is the angle the player will travel.
        x_diff = dest_x - start_x
        y_diff = dest_y - start_y
        target_angle_radians = math.atan2(y_diff, x_diff)
        # Convert back to degrees
        self.player_sprite.angle = math.degrees(target_angle_radians) + IMAGE_ROTATION
        
        # Add some friction
        """if self.player_sprite.change_angle > ANGLE_FRICTION:
            self.player_sprite.change_angle -= ANGLE_FRICTION
        elif self.player_sprite.change_angle < -ANGLE_FRICTION:
            self.player_sprite.change_angle += ANGLE_FRICTION
        else:
            self.player_sprite.change_angle = 0"""

        """if self.player_sprite.speed > FRICTION:
            self.player_sprite.speed -= FRICTION
        elif self.player_sprite.speed < -FRICTION:
            self.player_sprite.speed += FRICTION
        else:
            self.player_sprite.speed = 0"""

        # Apply acceleration based on the keys pressed
        if self.up_pressed and not self.down_pressed:
            self.player_sprite.speed += ACCELERATION_RATE
        elif self.down_pressed and not self.up_pressed:
            self.player_sprite.speed += -ACCELERATION_RATE
        """if self.left_pressed and not self.right_pressed:
            self.player_sprite.change_angle += -ANGLE_ACCELERATION_RATE
        elif self.right_pressed and not self.left_pressed:
            self.player_sprite.change_angle += ANGLE_ACCELERATION_RATE"""

        """if self.player_sprite.change_angle > ANGLE_MAX_SPEED:
            self.player_sprite.change_angle = ANGLE_MAX_SPEED
        elif self.player_sprite.change_angle < -ANGLE_MAX_SPEED:
            self.player_sprite.change_angle = -ANGLE_MAX_SPEED"""
        if self.player_sprite.speed > MAX_SPEED:
            self.player_sprite.speed = MAX_SPEED
        elif self.player_sprite.speed < -MAX_SPEED:
            self.player_sprite.speed = -MAX_SPEED
        
        # Call update to move the sprite
        # If using a physics engine, call update on it instead of the sprite
        # list.
        self.player_list.update()

        # Position the camera
        self.center_camera_to_player()

    def on_mouse_press(self, x, y, button, modifiers):
        """Called whenever a key is pressed. """

        self.pointer_sprite.center_x = x + self.player_sprite.center_x - (self.camera.viewport_width / 2)
        self.pointer_sprite.center_y = y + self.player_sprite.center_y - (self.camera.viewport_height / 2)

        if button == arcade.MOUSE_BUTTON_LEFT:
            self.up_pressed = True
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            pass

    def on_mouse_release(self, x, y, button, modifiers):
        """Called when the user releases a key. """

        if button == arcade.MOUSE_BUTTON_LEFT:
            self.up_pressed = False
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            pass

    def on_mouse_motion(self, x, y, delta_x, delta_y):
        """Called whenever the mouse moves. """
        self.mouse_raw_x = x
        self.mouse_raw_y = y

        

def main():
    """ Main method """
    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()