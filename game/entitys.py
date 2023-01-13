from typing_extensions import Self
import arcade
import math
import random
from . import constants, utilities
from arcade.pymunk_physics_engine import PymunkPhysicsEngine



GameMasterSettings = constants.GameMasterSettings

#player class
#inherits from arcade.Sprite parent class
class Player(arcade.Sprite):

    def __init__(self, image, scale, scene:arcade.scene, physicsEngine:PymunkPhysicsEngine):
        
        super().__init__(image, scale, flipped_diagonally=True, flipped_horizontally =True)
        scene.add_sprite("player_list", self)
        physicsEngine.add_sprite(self,
                                       collision_type="player",
                                       moment=20.0,
                                       max_velocity=GameMasterSettings["PLAYER_MAX_SPEED"])
        self.physics_object = physicsEngine.get_physics_object(self)
        self.speed = 0
        self.player_force = [0, 0]
        self.target_angle = 0
        self.bodyangle = 0 
        self.pid_params = {
            "p":100,
            "i":10,
            "d":0.1
        }
        self.pid_data = {
            "errSum":0,
            "lasterr":0
        }

    def on_update(self, pointer:arcade.sprite, delta_time: float = 1 / 60):
        self.bodyangle = self.physics_object.body.angle % (2 * math.pi)
        self.target_angle  = utilities.get_angle_to(self.position, pointer.position) % (2 * math.pi)
        error = self.bodyangle - self.target_angle 
        
        if abs(error) > math.pi:
            if self.target_angle > self.bodyangle:
                    self.bodyangle = self.bodyangle + 2*math.pi
            elif self.bodyangle > self.target_angle:
                self.target_angle = self.target_angle + 2*math.pi
        
        pid_output = utilities.pid(self.bodyangle, self.target_angle, delta_time, self.pid_params, self.pid_data)
        

        self.physics_object.body.apply_force_at_local_point((0, -pid_output), (2, 0))
        self.physics_object.body.apply_force_at_local_point((0, pid_output), (-2, 0))
        return super().on_update(delta_time)

    def thrust(self, force:float):
        self.physics_object.body.apply_force_at_local_point((force, 0), (1, 0))
        



#pointer class
class Pointer(arcade.Sprite):

    def __init__(self, image, scale):
        """ Set up the player """

        # Call the parent init
        super().__init__(image, scale)

    def update(self, mousepos, playerpos, camera:arcade.Camera):
        self.center_x = mousepos[0] + playerpos[0] - (camera.viewport_width / 2)
        self.center_y = mousepos[1] + playerpos[1] - (camera.viewport_height / 2)

        return super().update()
    def update_mini(self, playerpos, playerangle, playerdistence):
        self.center_x = playerpos[0]+playerdistence*math.cos(playerangle)
        self.center_y = playerpos[1]+playerdistence*math.sin(playerangle)
        

#bullet class
class Bullet(arcade.SpriteSolidColor):
    
    def __init__(self, width, height, color):
        """ Set up the player """

        # Call the parent init
        super().__init__(width, height, color)

        self.sound = arcade.Sound("assets/sfx/ship_fire_light.mp3")
        self.health:int = 50

    def fire(self, physics_engine:PymunkPhysicsEngine, bullet_object:Self, parent_object:arcade.sprite, fire_angle):
        bullet_object.position = parent_object.position

        bullet_object.size = max(parent_object.width, parent_object.height) / 2

        bullet_object.center_x += bullet_object.size * math.cos(fire_angle) 
        bullet_object.center_y += bullet_object.size * math.sin(fire_angle)

        bullet_object.angle = math.degrees(fire_angle)

        physics_engine.add_sprite(bullet_object,
            mass=GameMasterSettings["BULLET_MASS"],
            moment=PymunkPhysicsEngine.MOMENT_INF,
            damping=0.5,
            collision_type="bullet",
            )
        bullet_physcis_object = physics_engine.get_physics_object(bullet_object)
        bullet_physcis_object.body.velocity = parent_object.physics_object.body.velocity
        force = (GameMasterSettings["BULLET_FORCE"] , 0 )
        physics_engine.apply_force(bullet_object, force)
        bullet_object.sound.play()

    def on_update(self, delta_time: float = 1 / 60):
        self.health -= delta_time * 25
        if self.health <= 0:
            self.kill()
        return super().on_update(delta_time)

    

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
                                       mass=GameMasterSettings["CARGO_MASS"],
                                       moment=100.0,
                                       max_velocity=GameMasterSettings["CARGO_MAX_SPEED"])
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
        force[0] *= GameMasterSettings["CARGO_MOVE_FORCE"]
        force[1] *= GameMasterSettings["CARGO_MOVE_FORCE"]
        #self.trust(self.physics_engines[0], self.force)
        self.childgun.update_child(self, delta_time)
        return super().on_update(delta_time)


        
        

    def trust(self, physicsEngine:PymunkPhysicsEngine, force:int):
        physicsEngine.apply_force(self, force)


