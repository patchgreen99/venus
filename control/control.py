import serial


class RobotProtocol:
    def __init__(self):
        self.ser = serial.Serial('/dev/ttyACM1', 115200)

    def stop(self):
        self.ser.write('S\r')

    def move(self, time, motor_powers):
        out = ['M', str(time), str(len(motor_powers))]
        
        # motor_powers consists of tuples (num, power)
        for motor, power in motor_powers:
            out.append(str(motor))
            out.append(str(power))

        self.ser.write(' '.join(out) + '\r')
        print ' '.join(out)
# hello world

class Milestone1:
    def __init__(self):
        self.p = RobotProtocol()

    def move_forwards(self, x):
        self.p.move(1000, [
            (1, x),
            (2, -x),
            ])

    def move_backwards(self, x):
        self.p.move(1000, [
            (1, -x),
            (2, x),
            ])

    def move_left(self, x):
        self.p.move(1000, [
            (3, x),
            (4, -x),
            ])

    def move_right(self, x):
        self.p.move(1000, [
            (3, -x),
            (4, x),
            ])

    def kick(self, x):
        self.p.move(1000, [
            (5, -x)
            ])

    def prompt(self):
        text = raw_input('> ')
        while text != 'exit':
            tokens = text.split()
            if tokens[0] == 'f':
                self.move_forwards(int(tokens[1]))
            elif tokens[0] == 'b':
                self.move_backwards(int(tokens[1]))
            elif tokens[0] == 'l':
                self.move_left(int(tokens[1]))
            elif tokens[0] == 'r':
                self.move_right(int(tokens[1]))
            elif tokens[0] == 'k':
                self.kick(int(tokens[1]))
            else:
                print("No such command")
            text = raw_input('> ')


if __name__ == '__main__':
    milestone1 = Milestone1()
    milestone1.prompt()
