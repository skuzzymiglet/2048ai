import itertools
import math
import random
import sys
import os
import colors
import pyfiglet

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def colorize_number(n):
    color_dict = {0: "#ffffff", 2: "#dcd1c8", 4: "#d8cbb6", 8: "#e4a878", 16: "#d9804f", 32: "#e3755b", 64: "#d75337",
                  128: "#d9c062", 256: "#d9ba59", 512: "#d9b74a", 1024: "#d0a916", 2048: "#d9b32e", 4096: "#e63837"}
    if n < 8:
        fg = "#000000"
    else:
        fg = "#ffffff"
    return colors.color(str(n).center(6), fg=fg, bg=color_dict[n])


class Game:
    def __init__(self):
        """ Initialize a 2048 game
            NOTE: game does not know how to "play itself". Think of "Game"
            as representing a starting board configuration with the ability
            to advance and play 2048.
        """
        b = [[0]*4 for i in range(4)]
        self.b = Game.spawn(b, 2)

    def actions(b):
        """ Generate the subsequent board after moving """

        def moved(b, t):
            return any(x != y for x, y in zip(b, t))

        for action, f in [("left", Game.left), ("down", Game.down), ("up", Game.up), ("right", Game.right)]:
            t = f(b)
            if moved(b, t):
                yield action, t

    def over(b):
        """ Return whether or not a board is playable
        """
        def inner(b):
            for row in b:
                for x, y in zip(row[:-1], row[1:]):
                    if x == y or x == 0 or y == 0:
                        return True
            return False
        return not inner(b) and not inner(zip(*b))

    def string(b):
        r = ""
        for x in b:
            for y in x:
                r += colorize_number(y)
            r += "\n"
        return r

    def spawn(b, k=1):
        """ Add k random tiles to the board.
            Chance of 2 is 90%; chance of 4 is 10% """

        rows, cols = list(range(4)), list(range(4))
        random.shuffle(rows)
        random.shuffle(cols)
        copy = [[x for x in row] for row in b]
        dist = [2]*9 + [4]
        count = 0
        for i, j in itertools.product(rows, rows):
            if copy[i][j] != 0:
                continue
            copy[i][j] = random.sample(dist, 1)[0]
            count += 1
            if count == k:
                return copy
        raise Exception("shouldn't get here")

    def left(b):
        """ Returns a left merged board
        >>> Game.left(test)
        [[2, 8, 0, 0], [2, 8, 4, 0], [4, 0, 0, 0], [4, 4, 0, 0]]
        """

        return Game.merge(b)

    def right(b):
        """ Returns a right merged board
        >>> Game.right(test)
        [[0, 0, 2, 8], [0, 2, 4, 8], [0, 0, 0, 4], [0, 0, 4, 4]]
        """

        def reverse(x):
            return list(reversed(x))

        t = map(reverse, iter(b))
        return [reverse(x) for x in Game.merge(t)]

    def up(b):
        """ Returns an upward merged board
            NOTE: zip(*t) is transpose

        >>> Game.up(test) 
        [[4, 8, 4, 8], [4, 2, 0, 2], [0, 0, 0, 4], [0, 0, 0, 0]]
        """

        t = Game.left(zip(*b))
        return [list(x) for x in zip(*t)]

    def down(b):
        """ Returns an downward merged board
            NOTE: zip(*t) is transpose
        >>> Game.down(test)
        [[0, 0, 0, 0], [0, 0, 0, 8], [4, 8, 0, 2], [4, 2, 4, 4]]
        """

        t = Game.right(zip(*b))
        return [list(x) for x in zip(*t)]


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

    def merge(b):
        """ Returns a left merged board """

        def inner(row, a):
            """
            Helper for merge. If we're finished with the list,
            nothing to do; return the accumulator. Otherwise
            if we have more than one element, combine results of first
            with right if they match; skip over right and continue merge
            """

            if not row:
                return a
            x = row[0]
            if len(row) == 1:
                return inner(row[1:], a + [x])
            return inner(row[2:], a + [2*x]) if x == row[1] else inner(row[1:], a + [x])

        ret = []
        for row in b:
            merged = inner([x for x in row if x != 0], [])
            merged = merged + [0]*(len(row)-len(merged))
            ret.append(merged)
        return ret


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def aimove(b):
    """
    Returns a list of possible moves ("left", "right", "up", "down")
    and each corresponding fitness
    """
    def fitness(b):
        """
        Returns the heuristic value of b
        Snake refers to the "snake line pattern" (http://tinyurl.com/l9bstk6)
        Here we only evaluate one direction; we award more points if high valued tiles
        occur along this path. We penalize the board for not having
        the highest valued tile in the lower left corner
        """
        if Game.over(b):
            return -float("inf")

        snake = []
        for i, col in enumerate(zip(*b)):
            snake.extend(reversed(col) if i % 2 == 0 else col)

        m = max(snake)
        return sum(x/10**n for n, x in enumerate(snake)) - \
            math.pow((b[3][0] != m)*abs(b[3][0] - m), 2)


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

    def search(b, d, move=False):
        """
        Performs expectimax search on a given configuration to
        specified depth (d).
        Algorithm details:
           - if the AI needs to move, make each child move,
             recurse, return the maximum fitness value
           - if it is not the AI's turn, form all
             possible child spawns, and return their weighted average 
             as that node's evaluation
        """
        if d == 0 or (move and Game.over(b)):
            return fitness(b)

        alpha = fitness(b)
        if move:
            for _, child in Game.actions(b):
                return max(alpha, search(child, d-1, False))
        else:
            alpha = 0
            zeros = [(i, j) for i, j in itertools.product(
                range(4), range(4)) if b[i][j] == 0]
            for i, j in zeros:
                c1 = [[x for x in row] for row in b]
                c2 = [[x for x in row] for row in b]
                c1[i][j] = 2
                c2[i][j] = 4
                alpha += .9*search(c1, d-1, True)/len(zeros) + \
                    .1*search(c2, d-1, True)/len(zeros)
        return alpha
    return [(action, search(child, 5)) for action, child in Game.actions(b)]


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def aiplay(b):
    """
    Runs the game playing the move that determined
    by aimove.
    """
    while True:
        os.system("clear || cls")
        print(Game.string(b) + "\n")
        action = max(aimove(b), key=lambda x: x[1])[0]

        if action == "left":
            b = Game.left(b)
        if action == "right":
            b = Game.right(b)
        if action == "up":
            b = Game.up(b)
        if action == "down":
            b = Game.down(b)
        b = Game.spawn(b, 1)
        if Game.over(b):
            m = max(x for row in b for x in row)
            print("game over...best was %s" % m)
            print(Game.string(b))
            break


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def menu():
    f = pyfiglet.Figlet(font="dotmatrix", justify="center")
    print("""
    ---------------------------- / 2048 \ --------------------------

    {}

    Welcome to AI 2048! Press q to quit or any other key to begin. Have fun!



    """.format(f.renderText("2048 AI")))

    q = False
    f = False

    while q == False:
        while f == False:
            a = input("""


    enter here: """)
            if a == 'q':
                sys.exit()

            else:
                b = Game().b
                aiplay(b)


#-----------------------# Main #------------------------#
menu()
