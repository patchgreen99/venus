import serial


class RobotProtocol:
    def __init__(self, device):
        self.ser = serial.Serial(device, 115200, timeout=0.1)
        self.seq_no = 2
        self.response = None

    def move(self, units, motor_powers, time=False, wait=False):
        # motor_powers consists of tuples (num, power)
        command = 'M' if time else 'R'
        params = [abs(units)] + list(sum(motor_powers, ()))
        self.write(command, params)
        if wait:
            self.block_until_stop()

    def schedule(self, target, master, motor_powers):
        params = [target, master] + list(sum(motor_powers, ()))
        self.write('J', params)

    def block_until_stop(self, motor=None):
        if motor:
            self.write('Y', [motor], error_check=False)
        else:
            self.write('I', error_check=False)

    def move_forever(self, motor_powers):
        self.write('V', list(sum(motor_powers, ())))

    def stop(self, motors=None):
        if motors:
            self.write('Z', motors)
        else:
            self.write('S')

    def transfer(self, byte):
        self.write('T', [ord(byte)])

    def write(self, command, params=None, error_check=True):
        self.ser.reset_input_buffer()

        tokens = [command]
        if error_check:
            tokens += [self.seq_no, sum(abs(x) for x in params)]
            self.seq_no = (self.seq_no + 1) % 2
        if params:
            tokens += params
        message = ' '.join(str(t) for t in tokens)
        self.ser.write(message + '\r')
        print("Message sent: %s" % message)

        self.response = self.ser.read()
        while self.response != 'D':
            if self.response:
                print("Got unknown response '%s'" % self.response)
            self.ser.write(message + '\r')
            self.response = self.ser.read()

        print("Got done")

    def reset_input(self):
        self.ser.reset_input_buffer()
