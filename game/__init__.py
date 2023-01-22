import math
import arcade
from typing import Optional
from arcade.experimental.crt_filter import CRTFilter
from arcade.pymunk_physics_engine import PymunkPhysicsEngine
from . import entitys
from game.constants import *
import random

SCREEN_TITLE = "IHOWL"

# Size of screen to show, in pixels
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SPRITE_SCALING = 1
GUI_SCALING = 0.5
IMAGE_ROTATION = -90






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
        self.scene = None
        self.debug = False
        self.background = None
        # Physics engine
        self.physics_engine: Optional[arcade.PymunkPhysicsEngine] = None

        # Create the crt filter
        self.crt_filter = CRTFilter(width, height,
                                    resolution_down_scale=1.0,
                                    hard_scan=-8.0,
                                    hard_pix=-3.0,
                                    display_warp = (1.0 / 32.0, 1.0 / 24.0),
                                    mask_dark=0.5,
                                    mask_light=1.5)
    
    #setup method
    #loads the camera, physics and game assets before running the game
    def setup(self):
        """ Set up everything with the game """
        # cameras
        self.camera = arcade.Camera(self.width, self.height)
        #self.background = arcade.load_texture("assets/images/background.png")
         

        self.physics_engine = PymunkPhysicsEngine(damping=DEFAULT_DAMPING,
                                                  gravity=GRAVITY)


        self.scene = arcade.Scene()

        self.scene.add_sprite_list("player_list")
        self.scene.add_sprite_list("pointer_list")
        self.scene.add_sprite_list("ships_list")
        self.scene.add_sprite_list("bullet_list")
        self.scene.add_sprite_list("Ai_list")


        
        # Set up the pointer 
        self.pointer_sprite = entitys.Pointer("assets/images/pointer.png", GUI_SCALING)
        self.mini_pointer = entitys.Pointer("assets/images/minipointer.png", GUI_SCALING)
        
        self.scene.add_sprite("pointer_list", self.pointer_sprite)
        self.scene.add_sprite("pointer_list", self.mini_pointer)
        
        # Set up the player
        self.player_sprite = entitys.ship("assets/images/ship.png", SPRITE_SCALING, scene=self.scene, physicsEngine=self.physics_engine, max_vel=PLAYER_MAX_SPEED, mass=PLAYER_MASS,moment=PLAYER_MOMENT, cooldown=PLAYER_GUN_COOLDOWN, list="player_list", collision_type="player", target=self.pointer_sprite)
        self.player_sprite.physics_object.body._set_position((500, 0))
        # debug cargo ship
        self.cargodebug = entitys.ship("assets/images/cargo_base.png",  SPRITE_SCALING, scene=self.scene, physicsEngine=self.physics_engine, max_vel=CARGO_MAX_SPEED, mass=CARGO_MASS,moment=CARGO_MOMENT, cooldown=CARGO_GUN_COOLDOWN, list="Ai_list", collision_type="cargoship", targetcoord=(0, 0))

        # Set up bullets
        """ Find a way to make bullets not collide instead of doing this """
        def bulletxplayerbullet_hit_handler(bullet_sprite, bullet_sprite_2, _arbiter, _space, _data):
                bullet_sprite.kill()
                bullet_sprite_2.kill()
        self.physics_engine.add_collision_handler("bullet", "playerbullet", post_handler=bulletxplayerbullet_hit_handler)
        # Set up Cargoships 
        def bulletxcargo_hit_handler(bullet_sprite:entitys.Bullet, cargo_sprite:entitys.CargoShip_base, _arbiter, _space, _data):
            cargo_sprite.damage(bullet_sprite.health) 
            bullet_sprite.kill()
        self.physics_engine.add_collision_handler("bullet", "cargoship", post_handler=bulletxcargo_hit_handler)
    
    #on update method
    #runs the game and takes care of player input and physics
    def on_update(self, delta_time):
        """ Movement and game logic """

        # Update pointer
        self.pointer_sprite.update((self.mouse_raw_x, self.mouse_raw_y), (self.player_sprite.center_x, self.player_sprite.center_y), self.camera)
        self.mini_pointer.update_mini(self.player_sprite.position, self.player_sprite.physics_object.body.angle, self.player_sprite.distance_to_target)
    
        # Apply acceleration
        if self.thrust_pressed:
            thrust_amout = self.player_sprite.distance_to_target
            print(thrust_amout)
            thrust_amout = math.log(thrust_amout)
            self.player_sprite.thrust(PLAYER_MOVE_FORCE*thrust_amout)

        self.scene.on_update(delta_time, ["bullet_list", "Ai_list", "player_list"])


        if self.fire_pressed:
            self.player_sprite.fire_guns()
            
        for sprite in self.scene.name_mapping['Ai_list']:
            sprite:entitys.ship
            if sprite.distance_to_target <= 20: #check if the Ai ship is within 20 units of its old target
                player_x = self.player_sprite.center_x
                player_y = self.player_sprite.center_y

                #make a new target based thats within 500 units of the players pos 
                target = (random.uniform(player_x - 500, player_x + 500),
                               random.uniform(player_y - 500, player_y + 500))
                sprite.change_target(target)
            if abs(sprite.pid_output) <= 10: # if the Ai ship is not correcting its rotation by a large amount, apply thrust
                sprite.thrust(CARGO_MOVE_FORCE)

        # Step the engine 
        self.physics_engine.step()

        

        
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
    #for each frame, the shapes and objects will be drawn and then cleared
    #also applies any visual effects invoked such as the CRT filter
    def on_draw(self):
        
        # Draw our stuff into the CRT filter
        self.crt_filter.use()
        self.crt_filter.clear()
        self.camera.use()
        self.scene.draw()
       #arcade.draw_lrwh_rectangle_textured(0, 0,
        #                                    SCREEN_WIDTH, SCREEN_HEIGHT,
        #                                    self.background)
        arcade.draw_text("use your mouse to steer the ship", 10, 90, arcade.color.WHITE)
        arcade.draw_text("hold right click to move forward", 10, 70, arcade.color.WHITE)
        arcade.draw_text("hold left click to Shoot", 10, 50, arcade.color.WHITE)
            # Switch back to our window and draw the CRT filter do
            # draw its stuff to the screen
        self.use()
        self.clear()

        self.crt_filter.draw()

        if self.debug:
           arcade.draw_text(arcade.get_distance(self.player_sprite.center_x, self.player_sprite.center_y, 0, 0), self.pointer_sprite.center_x, self.pointer_sprite.center_y - 50, arcade.color.RED)
           #arcade.draw_text(self.player_sprite.pid_output, self.pointer_sprite.center_x, self.pointer_sprite.center_y - 50, arcade.color.RED)
           #arcade.draw_text(f"x {self.pointer_sprite.center_x}", self.pointer_sprite.center_x, self.pointer_sprite.center_y - 100, arcade.color.RED)
           #arcade.draw_text(f"y {self.pointer_sprite.center_y}", self.pointer_sprite.center_x, self.pointer_sprite.center_y - 150, arcade.color.RED)
           pangle = self.player_sprite.physics_object.body.angle
           tangle = self.player_sprite.target_angle
           arcade.draw_text(round(pangle, 4), self.pointer_sprite.center_x, self.pointer_sprite.center_y - 100, arcade.color.RED)
           arcade.draw_text(round(tangle, 4), self.pointer_sprite.center_x, self.pointer_sprite.center_y - 150, arcade.color.RED)
           arcade.draw_line(self.player_sprite.center_x, self.player_sprite.center_y, self.player_sprite.center_x+50*math.cos(pangle), self.player_sprite.center_y+50*math.sin(pangle), arcade.color.RED)
           arcade.draw_line(self.player_sprite.center_x, self.player_sprite.center_y, self.player_sprite.center_x+200*math.cos(tangle), self.player_sprite.center_y+200*math.sin(tangle), arcade.color.RED)
           arcade.draw_line(self.player_sprite.center_x, self.player_sprite.center_y, self.player_sprite.center_x+200*math.cos(math.pi), self.player_sprite.center_y+200*math.sin(math.pi), arcade.color.RED)
           arcade.draw_text(arcade.get_fps(), self.pointer_sprite.center_x, self.pointer_sprite.center_y + 50, arcade.color.RED)

    #method invoked when mouse is moved
    #points the spaceship in the direction of the mouse cursor
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

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == 65470:
            print(self.debug)
            if self.debug:   
                self.debug = False
                arcade.clear_timings()
                arcade.disable_timings()
            else:
                arcade.enable_timings()
                self.debug = True
        return super().on_key_press(symbol, modifiers)

    

#main function, entry point
def main():
    #initialise a game window
    window = GameWindow(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    
    #run the setup
    window.setup()

    #runs the main loop
    #always initialise the window, run the setup before invoking run()
    arcade.run()