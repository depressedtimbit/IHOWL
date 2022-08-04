import math
import numpy as np
from typing import Optional
import arcade
from arcade.pymunk_physics_engine import PymunkPhysicsEngine
from arcade.experimental.crt_filter import CRTFilter
from pyglet.math import Vec2

SCREEN_TITLE = "IHOWL"

# Size of screen to show, in pixels
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SPRITE_SCALING = 1
GUI_SCALING = 0.5
IMAGE_ROTATION = -90
""" Physics constants """

GRAVITY = (0, 0)

DEFAULT_DAMPING = 0.2

PLAYER_FRICTION = 1.0
PLAYER_MASS = 2.0
PLAYER_MAX_SPEED = 1400
PLAYER_MOVE_FORCE = 4000

BULLET_FORCE = 4500
BULLET_MASS = 0.1
BULLET_STOP_SPEED = 150
FIRE_COOLDOWN = 8

#player class
#note to self: python's inheritance is have the child class take the parent class in as a parameter in the declaration
class Player(arcade.Sprite):

    def __init__(self, image, scale):
        """ Set up the player """

        # Call the parent init
        super().__init__(image, scale)

        self.speed = 0
        self.player_force = [0, 0]
        self.physics_object = None

#pointer class
class Pointer(arcade.Sprite):

    def __init__(self, image, scale):
        """ Set up the player """

        # Call the parent init
        super().__init__(image, scale)

#bullet class
class Bullet(arcade.SpriteSolidColor):
    
    def __init__(self, width, height, color):
        """ Set up the player """

        # Call the parent init
        super().__init__(width, height, color)

        self.sound = arcade.Sound("assets/sfx/ship_fire_light.mp3")

    def fire(self, gamewin, bullet_object, parent_object, fire_angle):
        bullet_object.position = parent_object.position

        bullet_object.size = max(parent_object.width, parent_object.height) / 2

        bullet_object.center_x += bullet_object.size * math.cos(fire_angle) 
        bullet_object.center_y += bullet_object.size * math.sin(fire_angle)

        bullet_object.angle = math.degrees(fire_angle)

        gamewin.physics_engine.add_sprite(bullet_object,
            mass=BULLET_MASS,
            moment=PymunkPhysicsEngine.MOMENT_INF,
            damping=0.5,
            collision_type="bullet_sprite",
            )
        bullet_physcis_object = gamewin.physics_engine.get_physics_object(bullet_object)
        bullet_physcis_object.body.velocity = parent_object.physics_object.body.velocity
        force = (BULLET_FORCE , 0 )
        gamewin.physics_engine.apply_force(bullet_object, force)
        bullet_object.sound.play()
"""
class CargoShip_front(arcade.Sprite):

    def __init__(self, image, scale):

        super().__init__(image,scale)

class CargoShip_mid(arcade.Sprite):

    def __init__(self, image, scale):

        super().__init__(image,scale)

class CargoShip_back(arcade.Sprite):

    def __init__(self, image, scale):

        super().__init__(image,scale)
"""

#game window class
class GameWindow(arcade.Window):

    #constructor
    #this creates the window using the given dimensions
    def __init__(self, width, height, title):
        
        super().__init__(width, height, title)
        # Track controls 
        self.mouse_raw_x = 0
        self.mouse_raw_y = 0
        self.set_mouse_visible(False)
        self.thrust_pressed = False
        self.fire_pressed = False
        self.time_since_last_fire = 0
        # Physics engine
        self.physics_engine: Optional[arcade.PymunkPhysicsEngine] = None
        
        # Create the crt filter
        self.crt_filter = CRTFilter(width, height,
                                    resolution_down_scale=1.0,
                                    hard_scan=-8.0,
                                    hard_pix=-3.0,
                                    display_warp = Vec2(1.0 / 32.0, 1.0 / 24.0),
                                    mask_dark=0.5,
                                    mask_light=1.5)
    
    #setup method
    #loads the camera, physics and game assets before running the game
    def setup(self):
        """ Set up everything with the game """
        # cameras
        self.camera = arcade.Camera(self.width, self.height)
        
        self.physics_engine = PymunkPhysicsEngine(damping=DEFAULT_DAMPING,
                                                  gravity=GRAVITY)

        # Sprite lists
        self.player_list = arcade.SpriteList()
        self.pointer_list = arcade.SpriteList()
        self.ships_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()

        # Set up the player
        self.player_sprite = Player("assets/images/ship.png",SPRITE_SCALING)
        self.player_list.append(self.player_sprite)
        self.physics_engine.add_sprite(self.player_sprite,
                                       collision_type="player",
                                       moment=PymunkPhysicsEngine.MOMENT_INF,
                                       max_velocity=PLAYER_MAX_SPEED)
        self.player_sprite.physics_object = self.physics_engine.get_physics_object(self.player_sprite)
        
        # Set up the pointer 
        self.pointer_sprite = Pointer("assets/images/pointer.png", GUI_SCALING)
        self.pointer_list.append(self.pointer_sprite)
        """
        self.cargo_front = CargoShip_front("images/cargo01.png", SPRITE_SCALING)
        self.ships_list.append(self.cargo_front)
        self.cargo_front.position = [144, 0]
        self.cargo_mid = CargoShip_mid("images/cargo02.png", SPRITE_SCALING)
        self.ships_list.append(self.cargo_mid)
        self.cargo_mid.position = [80, 0]        
        self.cargo_back = CargoShip_back("images/cargo03.png", SPRITE_SCALING)
        self.cargo_back.position = [26, 0]
        self.ships_list.append(self.cargo_back)
        """
        # Set up bullets
        """ Find a way to make bullets not collide instead of doing this """
        def bulletxbullet_hit_handler(bullet_sprite, bullet_sprite_2, _arbiter, _space, _data):
                bullet_sprite.kill()
                bullet_sprite_2.kill()
        self.physics_engine.add_collision_handler("bullet_sprite", "bullet_sprite", post_handler=bulletxbullet_hit_handler)
    
    #on update method
    #runs the game
    def on_update(self, delta_time):
        """ Movement and game logic """

        # Position the marker 
        self.pointer_sprite.center_x = self.mouse_raw_x + self.player_sprite.center_x - (self.camera.viewport_width / 2)
        self.pointer_sprite.center_y = self.mouse_raw_y + self.player_sprite.center_y - (self.camera.viewport_height / 2)

        # Player Position
        start_x = self.player_sprite.center_x
        start_y = self.player_sprite.center_y

        # get pointer position
        dest_x = self.pointer_sprite.center_x
        dest_y = self.pointer_sprite.center_y

        # Apply rotation 
        x_diff = dest_x - start_x
        y_diff = dest_y - start_y
        angle = math.atan2(y_diff, x_diff)

        self.player_force = [math.cos(angle), math.sin(angle)]

        self.player_force[0] *= PLAYER_MOVE_FORCE
        self.player_force[1] *= PLAYER_MOVE_FORCE


        # Apply acceleration
        if self.thrust_pressed:
            self.physics_engine.apply_force(self.player_sprite, self.player_force)

        if self.time_since_last_fire > 0:
            self.time_since_last_fire -= 1

        for bullet_sprite in self.bullet_list:
            physics_object = self.physics_engine.get_physics_object(bullet_sprite)
            velf = physics_object.body.velocity
            if -BULLET_STOP_SPEED <= velf[0] <= BULLET_STOP_SPEED and -BULLET_STOP_SPEED <= velf[1] <= BULLET_STOP_SPEED:
                bullet_sprite.kill()
                
        if self.fire_pressed and self.time_since_last_fire <= 0:
            bullet_sprite = Bullet(20, 5, arcade.color.WHITE_SMOKE)
            self.bullet_list.append(bullet_sprite)
            bullet_sprite.fire(self, bullet_sprite, self.player_sprite, angle)
            self.time_since_last_fire += FIRE_COOLDOWN
                

        # Step the engine 
        self.physics_engine.step()

        self.player_sprite.angle = math.degrees(angle) + IMAGE_ROTATION

        
        # Center camera
        self.center_camera_to_player()

    #camera method
    #centers the camera on the player at all times
    def center_camera_to_player(self):
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (self.camera.viewport_height / 2)

        player_centered = screen_center_x, screen_center_y
        self.camera.move_to(player_centered)


    #draws the objects to the screen
    #also applies any effects invoked such as the CRT filter
    def on_draw(self):
        
        # Draw our stuff into the CRT filter
        self.crt_filter.use()
        self.crt_filter.clear()
        self.camera.use()
        self.player_list.draw()
        self.pointer_list.draw()
        self.ships_list.draw()
        self.bullet_list.draw()
        arcade.draw_text("use your mouse to steer the ship", 10, 90, arcade.color.WHITE)
        arcade.draw_text("hold right click to move forward", 10, 70, arcade.color.WHITE)
        arcade.draw_text("hold left click to Shoot", 10, 50, arcade.color.WHITE)
            # Switch back to our window and draw the CRT filter do
            # draw its stuff to the screen
        self.use()
        self.clear()

        self.crt_filter.draw()

    #method invoked when mouse is moved
    #points the spaceship in a particular direction
    def on_mouse_motion(self, x, y, delta_x, delta_y):
        """Called whenever the mouse moves. """
        self.mouse_raw_x = x
        self.mouse_raw_y = y
    
    #method invoked when mouse is pressed
    #when left mouse is pressed, fire projectiles
    #when right mouse is pressed, apply thrust to ship
    def on_mouse_press(self, x, y, button, modifiers):
        """Called whenever a key is pressed. """

        if button == arcade.MOUSE_BUTTON_LEFT:
            self.fire_pressed = True
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.thrust_pressed = True

    #method invoked when mouse is not pressed
    #when left mouse is not pressed or when is released, stop firing
    #when right mouse is not pressed or when is released, stop applying thrust
    def on_mouse_release(self, x, y, button, modifiers):
        """Called when the user releases a key. """

        if button == arcade.MOUSE_BUTTON_LEFT:
            self.fire_pressed = False
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.thrust_pressed = False

#main function, entry point
def main():
    #initialise a game window
    window = GameWindow(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    
    #run the setup
    window.setup()

    #runs the main loop
    #always initialise the window, run the setup before invoking run()
    arcade.run()