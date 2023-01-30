import random
import time
from typing_extensions import Self
import arcade
import arcade.gl
import math
from array import array
from dataclasses import dataclass
from . import utilities
from arcade.pymunk_physics_engine import PymunkPhysicsEngine
from game.constants import *
from itertools import cycle

@dataclass
class ParticleBurst:
    buffer: arcade.gl.Buffer
    vao: arcade.gl.Geometry
    start_time: float

class ParticleManager:
    def __init__(self, ctx, burst_list, width, height, camera:arcade.Camera) -> None:
        self.ctx = ctx
        self.burst_list = burst_list
        self.width = width
        self.height = height
        self.camera = camera

    def partical_burst(self, x: float, y:float, angle:float):
        def _gen_initial_data(initial_x, initial_y, angle):
                    for i in range(PARTICLE_COUNT):
                        angle = random.uniform(angle-0.05, angle+0.05)
                        speed = abs(random.gauss(0, 1)) * .2
                        colordiff = random.uniform(0.6, 0.8)
                        dx = -math.cos(angle) * speed
                        dy = -math.sin(angle) * speed
                        red = colordiff
                        green = colordiff
                        blue = colordiff
                        fade_rate = random.uniform(1 / MAX_FADE_TIME, 1 / MIN_FADE_TIME)

                        yield initial_x
                        yield initial_y
                        yield dx
                        yield dy
                        yield red
                        yield green
                        yield blue
                        yield fade_rate
        # Recalculate the coordinates from pixels to the OpenGL system with
        # 0, 0 at the center.

        x -= self.camera.position[0]
        y -= self.camera.position[1]
        x2 = x  / self.width * 2. - 1.
        y2 = y  / self.height * 2. - 1.
        

        # Get initial particle data
        initial_data = _gen_initial_data(x2, y2, angle)

        # Create a buffer with that data
        buffer = self.ctx.buffer(data=array('f', initial_data))

        # Create a buffer description that says how the buffer data is formatted.
        buffer_description = arcade.gl.BufferDescription(buffer,
                                                         '2f 2f 3f f',
                                                         ['in_pos',
                                                          'in_vel',
                                                          'in_color',
                                                          'in_fade_rate'])
        # Create our Vertex Attribute Object
        vao = self.ctx.geometry([buffer_description])

        # Create the Burst object and add it to the list of bursts
        burst = ParticleBurst(buffer=buffer, vao=vao, start_time=time.time())
        self.burst_list.append(burst)
        #print(len(self.burst_list))

    def on_update(self):
        # Create a copy of our list, as we can't modify a list while iterating
        # it. Then see if any of the items have completely faded out and need
        # to be removed.
        temp_list = self.burst_list.copy()
        for burst in temp_list:
            if time.time() - burst.start_time > MAX_FADE_TIME:
               self.burst_list.remove(burst)

#player class
#inherits from arcade.Sprite parent class
class ship(arcade.Sprite):

    def __init__(self, 
                    image, 
                    scale, 
                    scene:arcade.scene, 
                    physicsEngine:PymunkPhysicsEngine, 
                    list:str, 
                    collision_type:str, 
                    max_vel, 
                    mass, 
                    moment, 
                    cooldown, 
                    partical_manager:ParticleManager,
                    health:int = 100,
                    target:arcade.Sprite = None, 
                    targetcoord:list = None):
        
        super().__init__(image, scale, flipped_diagonally=True, flipped_horizontally =True)
        self.physics_engine = physicsEngine
        self.scene = scene
        self.target = target
        self.targetcoord = targetcoord
        self.distance_to_target = 0
        self.cooldown = cooldown
        self.partical_manager = partical_manager
        self.health = health
        self.scene.add_sprite(list, self)
        self.physics_engine.add_sprite(self,
                                       collision_type=collision_type,
                                       moment=moment,
                                       mass=mass,
                                       max_velocity=max_vel)
        self.physics_object = physicsEngine.get_physics_object(self)
        self.speed = 0
        self.player_force = [0, 0]
        self.target_angle = 0
        self.bodyangle = 0 
        self.gunlist = [
            Gun("assets/images/ship_gun.png", scale, self)
            ]
        
        self.guncycle = cycle(self.gunlist)
        self.lastfire = 0
        self.pid_params = {
            "p":100,
            "i":10,
            "d":0.1
        }
        self.pid_data = {
            "errSum":0,
            "lasterr":0
        }
        self.pid_output = 0

    def on_update(self, delta_time: float = 1 / 60):
        self.lastfire -= delta_time

        #get distance to target and target angle
        if self.target is not None: 
            self.distance_to_target = arcade.get_distance_between_sprites(self, self.target)
            self.target_angle  = utilities.get_angle_to(self.position, self.target.position) % (2 * math.pi)
        elif self.targetcoord is not None:
            self.distance_to_target = arcade.get_distance(self.position[0], self.position[1], self.targetcoord[0], self.targetcoord[1])
            self.target_angle  = utilities.get_angle_to(self.position, self.targetcoord) % (2 * math.pi)

        #~~~ PID control code
        self.bodyangle = self.physics_object.body.angle % (2 * math.pi)
        error = self.bodyangle - self.target_angle 
        
        if abs(error) > math.pi:
            if self.target_angle > self.bodyangle:
                    self.bodyangle = self.bodyangle + 2*math.pi
            elif self.bodyangle > self.target_angle:
                self.target_angle = self.target_angle + 2*math.pi
        
        self.pid_output = utilities.pid(self.bodyangle, self.target_angle, delta_time, self.pid_params, self.pid_data)
        #~~~


        #rotate the ship by applying trust in 2 oppsite and offset points 
        self.physics_object.body.apply_force_at_local_point((0, -self.pid_output), (2, 0))
        self.physics_object.body.apply_force_at_local_point((0, self.pid_output), (-2, 0))
        return super().on_update(delta_time)

    def thrust(self, force:float):
        self.physics_object.body.apply_impulse_at_local_point((force, 0), (1, 0)) 
        self.partical_manager.partical_burst(self.physics_object.body.position[0], self.physics_object.body.position[1], self.physics_object.body.angle)
        

    def fire_guns(self):
        gun = next(self.guncycle)
        
        if self.lastfire <= 0:
                gun.fire()
                self.lastfire = PLAYER_GUN_COOLDOWN / len(self.gunlist) #devide the cooldown by the amount of guns attached to the ship, as each gun fires one at a time 
            
    def change_target(self, new_target):
        if type(new_target) == arcade.Sprite:
            self.target = new_target
            self.targetcoord = None
        else:
            self.targetcoord = new_target
            self.target = None

    def damage(self, amount:int, instant:bool = False):
        if instant:
            self.health = -999
        else: self.health -= amount

        #health check
        if self.health <= 0:
            for gun in self.gunlist:
                print("killed sprite", id(gun))
                gun.kill()
            self.kill()
            print("killed sprite", id(self))

class Gun(arcade.Sprite):
    def __init__(self, image, scale, parent):

        super().__init__(image, scale)
        self.parent = parent
        self.bullet = Bullet
    def fire(self):
        self.bullet(20, 5, arcade.color.WHITE_SMOKE, self.parent)
        
#bullet class
class Bullet(arcade.SpriteSolidColor):
    
    def __init__(self, width, height, color, parent:ship):
        """ Set up the player """

        # Call the parent init
        super().__init__(width, height, color)

        self.sound = arcade.Sound("assets/sfx/ship_fire_light.mp3")
        self.health:int = 50

        self.parent = parent
        self.parent.scene.add_sprite("bullet_list", self)
        self.position = parent.position

        self.size = max(parent.width, parent.height) / 2

        self.center_x += self.size * math.cos(parent.bodyangle) 
        self.center_y += self.size * math.sin(parent.bodyangle)

        self.angle = math.degrees(parent.bodyangle)

        parent.physics_engine.add_sprite(self,
            mass=BULLET_MASS,
            moment=PymunkPhysicsEngine.MOMENT_INF,
            damping=0.5,
            collision_type="bullet",
            )
        bullet_physcis_object = parent.physics_engine.get_physics_object(self)
        bullet_physcis_object.body.velocity = parent.physics_object.body.velocity
        force = (BULLET_FORCE, 0 )
        parent.physics_engine.apply_force(self, force)
        self.sound.play()

    def on_update(self, delta_time: float = 1 / 60):
        self.health -= delta_time * 25
        if self.health <= 0:
            self.kill()
        return super().on_update(delta_time)

    def damage(self, amount:int, instant:bool = False):
        if instant:
            self.health = -999
        else: self.health -= amount

#pointer class
class Pointer(arcade.Sprite):

    def __init__(self, image, scale):
        """ Set up the player """

        # Call the parent init
        super().__init__(image, scale)

    def update(self, mousepos, playerpos, camera:arcade.Camera):
        self.center_x = mousepos[0] + camera.position[0]
        self.center_y = mousepos[1] + camera.position[1] 

        return super().update()
    def update_mini(self, playerpos, playerangle, playerdistence):
        self.center_x = playerpos[0]+playerdistence*math.cos(playerangle)
        self.center_y = playerpos[1]+playerdistence*math.sin(playerangle)


"""~~~~~~~~Old stuff, use for reference~~~~~~~~"""

class CargoShip_gun(arcade.Sprite):
    def __init__(self, image:str, scale:int, scene:arcade.scene, parent:arcade.sprite):

        super().__init__(image, scale, flipped_diagonally=True, flipped_horizontally =True)
        
        scene.add_sprite("Ai_list", self)
    
    def update_child(self, parent:arcade.sprite ,delta_time: float = 1 / 60):
        self.position = parent.position 
    

class CargoShip_base(arcade.Sprite):

    def __init__(self, image:str, scale:int, scene:arcade.scene, physicsEngine:arcade.PymunkPhysicsEngine):
        
        super().__init__(image, scale, flipped_diagonally=True, flipped_horizontally =True)
        
        scene.add_sprite("Ai_list", self)
        physicsEngine.add_sprite(self,
                                       collision_type="cargoship",
                                       mass=CARGO_MASS,
                                       moment=100.0,
                                       max_velocity=CARGO_MAX_SPEED)
        self.physics_object = physicsEngine.get_physics_object(self)
        self.childgun = CargoShip_gun(image="assets\images\cargo_gun.png", scale=scale, scene=scene, parent=self)
        self.health:int = 100
        self.wonder:int = 0
        self.fear:int = 0
        self.updatetime:int = 0
        self.angle:float = 0

    def damage(self, amount:int, instant:bool = False):
        if instant:
            self.health = -999
        else: self.health -= amount

    def on_update(self, target:arcade.sprite, delta_time: float = 1 / 60):
        #health check
        if self.health <= 0:
            self.childgun.kill()
            print("killed sprite", id(self.childgun))
            self.kill()
            print("killed sprite", id(self))

        """Update Ai and Apply force"""
        
        self.wonder -= delta_time
        self.wonder = min(self.wonder, 0)
        self.fear -= delta_time
        self.fear = min(self.fear, 0)
        self.updatetime -= delta_time
        self.updatetime = min(self.updatetime, 0)
        distence = arcade.get_distance_between_sprites(self, target)
        
        if distence >= 1500:
            self.damage(0, True)
            
        if self.updatetime == 0:
            #self.physics_object.body.apply_force_at_local_point((0, 0.01), (0, 1))
            self.updatetime = 8
            #self.angle = utilities.get_angle_to(self.position, target.position)
        #angle += random.randint(-1, 1)
        
        #self.physics_object.body.angle = self.angle
        force = [math.cos(self.angle), math.sin(self.angle)]
        force[0] *= CARGO_MOVE_FORCE
        force[1] *= CARGO_MOVE_FORCE
        #self.trust(self.physics_engines[0], self.force)
        self.childgun.update_child(self, delta_time)
        return super().on_update(delta_time)


        
        

    def trust(self, physicsEngine:PymunkPhysicsEngine, force:int):
        physicsEngine.apply_force(self, force)


