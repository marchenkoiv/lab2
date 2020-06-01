

looks = {'0': 'right',
        '1': 'down',
        '2': 'left',
        '3': 'up',
        }





class Robot:
    def __init__(self, x, y, turn, _map):
        # turn - turning direction
        self.x = x
        self.y = y
        self.turn = turn
        self.map = _map

    def __repr__(self):
        return f'''\n x = {self.x}\n y = {self.y}\n turn: {looks[str(self.turn)]}\n '''

    def is_exit(self):
        if self.map[self.y+1][self.x] == 'E':
            return True
        else:
            return False

    def look(self):
        if self.turn == 0:
            i = 1
            while self.map[self.y+1][self.x + i] != '#':
                i = i + 1
            return i
        elif self.turn == 1:
            i = 1
            while self.map[self.y + i+1][self.x] != '#':
                i = i + 1
            return i
        elif self.turn == 2:
            i = 1
            while self.map[self.y+1][self.x - i] != '#':
                i = i + 1
            return i
        elif self.turn == 3:
            i = 1
            while self.map[self.y - i+1][self.x] != '#':
                i = i + 1
            return i

    def step(self):
        if self.turn == 0:
            if self.look() == 1:
                return False
            else:
                self.x += 1
                return True
        if self.turn == 1:
            if self.look() == 1:
                return False
            else:
                self.y += 1
                return True
        if self.turn == 2:
            if self.look() == 1:
                return False
            else:
                self.x -= 1
                return True
        if self.turn == 3:
            if self.look() == 1:
                return False
            else:
                self.y -= 1
                return True

    def right(self):
        self.turn = (self.turn + 1) % 4
        return True

    def left(self):
        self.turn = (self.turn - 1) % 4
        return True

    def back(self):
        self.turn = (self.turn - 2) % 4
        return True

