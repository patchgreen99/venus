from tracker import *
from camera import Camera
from algebra import *

import argparse
import time
import zmq


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t",
                        help="Our Team Colour",
                        required=True,
                        choices=["yellow", "light_blue"])
    '''parser.add_argument("-d",
                        help="Number of dots",
                        required=True,
                        choices=["1", "3"])'''
    parser.add_argument("-b",
                        help="Ball Colour",
                        required=True,
                        choices=["red", "blue"])
    #parser.add_argument("-c", help="Computer Name (useful for testing)")

    return parser.parse_args()


def main(world):


    # socket setup
    # ctx = zmq.Context()
    # socket = ctx.socket(zmq.PUB)
    # socket.bind("tcp://*:5555")

    # args = parse_args()
    c = Camera()

    frame = c.get_frame()

    colors = {}
    colors['yellow'] = (0, 255, 255)
    colors['light_blue'] = (255, 255, 0)
    colors['pink'] = (127, 0, 255)
    colors['green'] = (0, 255, 0)
    colors['red'] = (0, 0, 255)
    colors['blue'] = (255, 0, 0)
    trajectory_list = [(0, 0)] * 6

    ROBOTS = {'ally':{'green': world.venus,'pink': world.friend}, 'enemy':{'green': world.enemy1, 'pink': world.enemy2}}

    # our_team_color = args.t
    our_team_color = world.team_color
    #num_of_pink = args.d
    # ball_color = args.b
    ball_color = "red"
    #print("(%s, %s, %s)" % (our_team_color, num_of_pink, ball_color))

    # create our robot as object:
    robot_tracker = RobotTracker(our_team_color)
    ball_tracker = BallTracker(ball_color)

    # convert string colors into GBR
    '''our_circle_color = colors[our_team_color]
    if our_team_color == 'yellow':
        opponent_circle_color = colors['light_blue']
    else:
        opponent_circle_color = colors['yellow']'''

    # assign colors and names to the robots
    '''if int(num_of_pink) == 1:
        our_letters = 'GREEN'
        our_col = colors['green']
        our_robot_color = 'green_robot'
        mate_letters = 'PINK'
        mate_col = colors['pink']
        our_mate_color = 'pink_robot'
    else:
        our_letters = 'PINK'
        our_col = colors['pink']
        our_robot_color = 'pink_robot'
        mate_letters = 'GREEN'
        mate_col = colors['green']
        our_mate_color = 'green_robot'''

    # main feed controller:
    while True:
        k = cv2.waitKey(5) & 0xFF
        if k == 27:
            break
        frame = c.get_frame()

        # get robot orientations and centers, also get ball coordinates
        robots_all = None
        ball_centre = None
        try:
            ball_center = ball_tracker.getBallCoordinates(frame)
            robots_all = robot_tracker.getAllRobots(frame)
        except ValueError:
            print("Exception calculating ball")
            raise

        if ball_center is not None:
            _ball = transformCoordstoCV(ball_center)
            world.ball[0] = int(_ball[0])
            world.ball[1] = int(_ball[1])
            cv2.circle(frame, tuple(world.ball), 7,
                       colors[ball_color], 2)
            cv2.putText(frame, 'BALL',
                        (int(_ball[0]) - 15, int(_ball[1]) + 15),
                        cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.5,
                        colors[ball_color])
            
            trajectory_list.append((tuple(world.ball)))
            trajectory_list.pop(0)
            
            # Draw balls trajectory
            delta_x = trajectory_list[len(trajectory_list) - 1][0] - trajectory_list[0][0]
            delta_y = trajectory_list[len(trajectory_list) - 1][1] - trajectory_list[0][1]
            if math.sqrt(delta_x**2 + delta_y**2) > 2:
                world.ball_moving[0] = 1
                future_x = trajectory_list[len(trajectory_list) - 1][0] + delta_x
                if float(delta_x) != 0.0:
                    m = (trajectory_list[len(trajectory_list) - 1][1] - trajectory_list[0][1]) / float(delta_x)
                else:
                    m = 0
                future_y = (future_x - trajectory_list[0][0]) * m + trajectory_list[0][1]
                world.ball_velocity[0] = (future_x - world.ball[0])
                world.ball_velocity[1] = (future_y - world.ball[1])
                cv2.line(frame, (int(trajectory_list[len(trajectory_list) - 1][0]), int(trajectory_list[len(trajectory_list) - 1][1])), (int(future_x), int(future_y)), colors[ball_color], 1)
            else:
                world.ball_moving[0] = 0


        for side, side_robs in robots_all.iteritems():
            for color, robot in side_robs.iteritems():
                center = robots_all[side][color]['center']
                orientation = robots_all[side][color]['orientation']
                if (orientation is not None) and (center is not None):
                    a, v = orientation
                    x, y = center

                    # fiddle
                    x = 640+x
                    y = 512-y

                    #print(side, color, a, (x, y))

                    if v is not None:
                        draw_vector = (x + v[0], y + v[1])
                    else:
                        draw_vector = (0, 0)
                    x, y = transformCoordstoCV(draw_vector)
                    center = transformCoordstoCV(center)
                    #print(center)
                    cv2.line(frame,
                            (int(center[0]), int(center[1])),
                            (int(x), int(y)), (0, 0, 255), 2)
                    cv2.circle(frame,
                            (int(center[0]),
                                int(center[1])), 20, (0,0,255), 2)
                    cv2.putText(frame, side, (int(center[0]) - 15,
                                            int(center[1]) + 30),
                                cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.5, (0,0,255))
                    cv2.putText(frame, color, (int(center[0]) - 20,
                                                    int(center[1]) + 40),
                                cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.5, (0,0,255))


        # for side, side_robs in robots_all.iteritems():
        #     for color, robot in side_robs.iteritems():
        #         print('Center: ', robot.center)
        #         print('Orientation: ', robot.orientation)



        #tmp = robots_all.copy()
        #tmp.update({"ball_center": ball_center})
        # socket.send_pyobj(tmp)
        # print(robots_all)

        cv2.imshow('frame', frame)

    c.close()
    cv2.destroyAllWindows()


# if __name__ == "__main__":
#     main()
