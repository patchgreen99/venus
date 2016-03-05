import serial


class RobotProtocol:
    def __init__(self, device):
        self.ser = serial.Serial(device, 115200, timeout=0.1)
        self.seq_no = 0
        self.response = None

    def move(self, units, motor_powers, time=False, wait=False):
        # motor_powers consists of tuples (num, power)
        command = 'M' if time else 'R'
        params = [abs(units)] + list(sum(motor_powers, ()))
        self.write(command, params)
        if wait:
            self.block_until_stop()

    def block_until_stop(self, motor=None):
        if motor:
            self.write('Y', [motor], seq=False)
        else:
            self.write('I', seq=False)

    def move_forever(self, motor_powers):
        self.write('V', list(sum(motor_powers, ())))

    def stop(self, motors=None):
        if motors:
            self.write('Z', motors)
        else:
            self.write('S')

    def transfer(self, byte):
        self.write('T', [ord(byte)])

    def write(self, command, params=None, seq=True):
        self.ser.reset_input_buffer()

        tokens = [command]
        if seq:
            self.seq_no = (self.seq_no + 1) % 2
            tokens.append(self.seq_no)
        if params:
            tokens += params
        message = ' '.join(str(t) for t in tokens)
        self.ser.write(message + '\r')
        print("Message sent: %s" % message)

        print("Waiting for done")

        self.response = self.ser.read()
        while self.response != 'D':
            if self.response:
                print("Got unknown response '%s'" % self.response)
            self.ser.write(message + '\r')
            self.response = self.ser.read()

        print("Got done")

    def reset_input(self):
        self.ser.reset_input_buffer()
