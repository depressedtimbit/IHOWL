import math
def get_angle_to(startvec2, endvec2):
        # start Position
        start_x = startvec2[0]
        start_y = startvec2[1]

        # end position
        dest_x = endvec2[0]
        dest_y = endvec2[1]

        x_diff = dest_x - start_x
        y_diff = dest_y - start_y
        angle = math.atan2(y_diff, x_diff)
        return angle

def pid(input,
        setpoint,
        delta_time,
        params:dict = {"p":100, "i":10, "d":10},
        data:dict = {"errSum":0, "lasterr":0}) -> float:

        error = setpoint - input
        data["errSum"] += (error * delta_time)
        derr = (error - data["lasterr"]) / delta_time

        data["lasterr"] = error
        return -(params["p"] * error + params["i"] * data["errSum"] + params["d"] * derr)

        

def cycle(list):
        """more memory efficient cycle"""
        while list:
                for element in list:
                        yield element

                        