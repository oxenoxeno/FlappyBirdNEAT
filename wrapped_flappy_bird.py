# coding=utf-8

import numpy as np
import sys
import random
import pygame
import flappy_bird_utils
import pygame.surfarray as surfarray
from pygame.locals import *
from itertools import cycle
import math
import cv2

SPEED_UP = 1.0
FPS = 60.0
SCREENWIDTH = 288
SCREENHEIGHT = 512

pygame.init()
FPSCLOCK = pygame.time.Clock()
SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
pygame.display.set_caption('Flappy Bird')

IMAGES, SOUNDS, HITMASKS = flappy_bird_utils.load()
PIPEGAPSIZE = 100  # gap between upper and lower part of pipe
BASEY = SCREENHEIGHT * 0.79

PLAYER_WIDTH = IMAGES['player'][0].get_width()
PLAYER_HEIGHT = IMAGES['player'][0].get_height()
PIPE_WIDTH = IMAGES['pipe'][0].get_width()
PIPE_HEIGHT = IMAGES['pipe'][0].get_height()
BACKGROUND_WIDTH = IMAGES['background'].get_width()

PLAYER_INDEX_GEN = cycle([0, 1, 2, 1])


class GameState:
    def __init__(self):
        self.reward = 0.0
        self.score = self.playerIndex = self.loopIter = 0
        self.score_real = self.playerIndex = self.loopIter = 0
        self.playerx = int(SCREENWIDTH * 0.2)
        self.playery = int((SCREENHEIGHT - PLAYER_HEIGHT) / 2)
        self.basex = 0
        self.baseShift = IMAGES['base'].get_width() - BACKGROUND_WIDTH

        newPipe1 = getRandomPipe()
        newPipe2 = getRandomPipe()
        self.upperPipes = [
            {'x': SCREENWIDTH, 'y': newPipe1[0]['y']},
            {'x': SCREENWIDTH + (SCREENWIDTH / 2), 'y': newPipe2[0]['y']},
        ]
        self.lowerPipes = [
            {'x': SCREENWIDTH, 'y': newPipe1[1]['y']},
            {'x': SCREENWIDTH + (SCREENWIDTH / 2), 'y': newPipe2[1]['y']},
        ]

        # print([self.playerx, self.playery], [self.upperPipes, self.lowerPipes])

        # player velocity, max velocity, downward accleration, accleration on flap
        self.pipeVelX = -4 * SPEED_UP
        self.playerVelY = 0 * SPEED_UP  # player's velocity along Y, default same as playerFlapped
        self.playerMaxVelY = 10 * SPEED_UP  # max vel along Y, max descend speed
        self.playerMinVelY = -8 * SPEED_UP  # min vel along Y, max ascend speed
        self.playerAccY = 1 * SPEED_UP  # players downward accleration
        self.playerFlapAcc = -9 * SPEED_UP  # players speed on flapping
        self.playerFlapped = False  # True when player flaps

    def frame_step(self, input_actions):
        alive_reward = 0.1
        get_reward = 1.0
        dead_reward = -1.0

        pygame.event.pump()

        reward = alive_reward
        # print 'reward: %f' % self.reward
        terminal = False

        # if sum(input_actions) != 1:
        # if 0 <= input_actions <= 1:
        #     raise ValueError('Input actions ERROR!')

        # input_actions[0] == 1: do nothing
        # input_actions[1] == 1: flap the bird
        # if input_actions[1] == 1:
        #     if self.playery > -2 * PLAYER_HEIGHT:
        #         self.playerVelY = self.playerFlapAcc
        #         self.playerFlapped = True
        #         # SOUNDS['wing'].play()

        # input_actions == 0: do nothing
        # input_actions == 1: flap the bird
        if input_actions == 1:
            if self.playery > -2 * PLAYER_HEIGHT:
                self.playerVelY = self.playerFlapAcc
                self.playerFlapped = True
                # SOUNDS['wing'].play()

        # check for score
        playerMidPos = self.playerx + PLAYER_WIDTH / 2
        playerRightEdge = self.playerx + PLAYER_WIDTH
        playerBottonEdge = self.playery + PLAYER_HEIGHT
        TopEdgeBelowTopPipeBottom_Flag = False
        for pipe in self.upperPipes:
            pipeMidPos = pipe['x'] + PIPE_WIDTH / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                self.score_real += 1
                # SOUNDS['point'].play()
                print('Real Score: ', self.score_real)
                self.score += reward
                reward = get_reward
            # if playerRightEdge >= pipe['x']:
            #     self.score += 1
            #     # SOUNDS['point'].play()
            #     # print('Score: ', self.score)
            #     reward += self.score_real

            # 坐标原点在左上角
            # 鸟右边 in gap, 且鸟上边低于最近的 upperPipe 底pipe['y'] + PIPE_HEIGHT
            # if playerRightEdge >= pipe['x'] and self.playery >= pipe['y'] + PIPE_HEIGHT:
            #     TopEdgeBelowTopPipeBottom_Flag = True

        # for pipe in self.lowerPipes:
        #     # 鸟体底 高于 最近的 lowerPipes 的顶pipe['y']
        #     if playerBottonEdge <= pipe['y'] and TopEdgeBelowTopPipeBottom_Flag is True:  #
        #         self.score += 1
        #         # SOUNDS['point'].play()
        #         # print('Score: ', self.score)
        #         reward = 100 + self.score * 10

        # playerIndex basex change
        if (self.loopIter + 1) % 3 == 0:
            self.playerIndex = next(PLAYER_INDEX_GEN)
        self.loopIter = (self.loopIter + 1) % 30
        self.basex = -((-self.basex + 100) % self.baseShift)

        # player's movement
        if self.playerVelY < self.playerMaxVelY and not self.playerFlapped:
            self.playerVelY += self.playerAccY
        if self.playerFlapped:
            self.playerFlapped = False
        self.playery += min(self.playerVelY, BASEY - self.playery - PLAYER_HEIGHT)
        if self.playery < 0:
            self.playery = 0

        # move pipes to left
        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            uPipe['x'] += self.pipeVelX
            lPipe['x'] += self.pipeVelX

        """ wrap """
        upperVertical_0 = self.playery - self.upperPipes[0]['y']
        upperVertical_1 = self.playery - self.upperPipes[1]['y']
        lowerVertical_0 = self.playery - self.lowerPipes[0]['y']
        lowerVertical_1 = self.playery - self.lowerPipes[1]['y']

        upperHorizon_0 = self.playery - self.upperPipes[0]['x']
        upperHorizon_1 = self.playery - self.upperPipes[1]['x']
        lowerHorizon_0 = self.playery - self.lowerPipes[0]['x']
        lowerHorizon_1 = self.playery - self.lowerPipes[1]['x']

        upperDistance0 = pow(upperVertical_0 * upperVertical_0 + upperHorizon_0 * upperHorizon_0, 0.5)
        lowerDistance0 = pow(lowerVertical_0 * lowerVertical_0 + lowerHorizon_0 * lowerHorizon_0, 0.5)
        upperDistance1 = pow(upperVertical_1 * upperVertical_1 + upperHorizon_1 * upperHorizon_1, 0.5)
        lowerDistance1 = pow(lowerVertical_1 * lowerVertical_1 + lowerHorizon_1 * lowerHorizon_1, 0.5)



        # add new pipe when first pipe is about to touch left of screen
        if 0 < self.upperPipes[0]['x'] < 5:
            newPipe = getRandomPipe()
            self.upperPipes.append(newPipe[0])
            self.lowerPipes.append(newPipe[1])



        # remove first pipe if its out of the screen
        if self.upperPipes[0]['x'] < -PIPE_WIDTH:
            self.upperPipes.pop(0)
            self.lowerPipes.pop(0)



        # draw sprites
        SCREEN.blit(IMAGES['background'], (0, 0))




        # check if crash here
        isCrash = checkCrash({'x': self.playerx, 'y': self.playery,
                              'index': self.playerIndex},
                             self.upperPipes, self.lowerPipes)
        if isCrash == 2:
            # SOUNDS['hit'].play()
            # SOUNDS['die'].play()
            terminal = True
            self.__init__()
            reward = dead_reward
            # playerMidPos = self.playerx + PLAYER_WIDTH / 2
            # for pipe in self.upperPipes:
            #     if pipe['x'] <= playerMidPos < pipe['x'] + PIPE_WIDTH:
            #         reward = -1
        elif isCrash == 1:
            # SOUNDS['hit'].play()
            # SOUNDS['die'].play()
            terminal = True
            self.__init__()
            reward = dead_reward

        # draw sprites
        SCREEN.blit(IMAGES['background'], (0, 0))

        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        SCREEN.blit(IMAGES['base'], (self.basex, BASEY))
        # print score so player overlaps the score
        # showScore(self.score)
        SCREEN.blit(IMAGES['player'][self.playerIndex],
                    (self.playerx, self.playery))

        image_data = pygame.surfarray.array3d(pygame.display.get_surface())
        # x_t = cv2.cvtColor(cv2.resize(image_data, (80, 80)), cv2.COLOR_BGR2GRAY)
        # ret, x_t = cv2.threshold(x_t, 1, 255, cv2.THRESH_BINARY)
        # s_t = x_t.flatten()


        pygame.display.update()
        FPSCLOCK.tick(FPS)
        # print self.upperPipes[0]['y'] + PIPE_HEIGHT - int(BASEY * 0.2)
        # return image_data, reward, terminal   # origin

        # state = np.array([self.playerx, self.playery, upperDistance0, lowerDistance0, upperDistance1, lowerDistance1])
        state = np.array([self.playerx, self.playery,
                          upperVertical_0, lowerVertical_0, upperVertical_1, lowerHorizon_1,
                          upperDistance0, lowerDistance0, upperDistance1, lowerDistance1
                          ])

        # state = np.array([self.playerx,
        #                   self.playery,
        #                   self.upperPipes[-1]['x'],
        #                   self.lowerPipes[-1]['x'],
        #                   self.upperPipes[-2]['x'],
        #                   self.lowerPipes[-2]['x'],
        #                   self.upperPipes[-1]['y'],
        #                   self.lowerPipes[-1]['y'],
        #                   self.upperPipes[-2]['y'],
        #                   self.lowerPipes[-2]['y']
        #                   ])

        # print('state: ', state)
        # print('reward: ', reward)
        return state, reward, terminal


def getRandomPipe():
    """returns a randomly generated pipe"""
    # y of gap between upper and lower pipe
    gapYs = [20, 30, 40, 50, 60, 70, 80, 90]
    index = random.randint(0, len(gapYs) - 1)
    gapY = gapYs[index]

    gapY += int(BASEY * 0.2)
    pipeX = SCREENWIDTH + 10

    return [
        {'x': pipeX, 'y': gapY - PIPE_HEIGHT},  # upper pipe
        {'x': pipeX, 'y': gapY + PIPEGAPSIZE},  # lower pipe
    ]


def showScore(score):
    """displays score in center of screen"""
    scoreDigits = [int(x) for x in list(str(score))]
    totalWidth = 0  # total width of all numbers to be printed

    for digit in scoreDigits:
        totalWidth += IMAGES['numbers'][digit].get_width()

    Xoffset = (SCREENWIDTH - totalWidth) / 2

    for digit in scoreDigits:
        SCREEN.blit(IMAGES['numbers'][digit], (Xoffset, SCREENHEIGHT * 0.1))
        Xoffset += IMAGES['numbers'][digit].get_width()


def checkCrash(player, upperPipes, lowerPipes):
    """returns True if player collders with base or pipes."""
    pi = player['index']
    player['w'] = IMAGES['player'][0].get_width()
    player['h'] = IMAGES['player'][0].get_height()

    # if player crashes into ground
    if player['y'] + player['h'] >= BASEY - 1:
        return 1
    else:

        playerRect = pygame.Rect(player['x'], player['y'],
                                 player['w'], player['h'])

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            # upper and lower pipe rects
            uPipeRect = pygame.Rect(uPipe['x'], uPipe['y'], PIPE_WIDTH, PIPE_HEIGHT)
            lPipeRect = pygame.Rect(lPipe['x'], lPipe['y'], PIPE_WIDTH, PIPE_HEIGHT)

            # player and upper/lower pipe hitmasks
            pHitMask = HITMASKS['player'][pi]
            uHitmask = HITMASKS['pipe'][0]
            lHitmask = HITMASKS['pipe'][1]

            # if bird collided with upipe or lpipe
            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

            if uCollide or lCollide:
                return 2

    return 3


def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Checks if two objects collide and not just their rects"""
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y

    for x in range(rect.width):
        for y in range(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False
