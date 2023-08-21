import pygame
import math

class Heart:
    def __init__(self, img, pos, speed):
        '''
        initializing the heart
        (image, position=[x,y], speed)
        '''
        self.img = img
        self.pos = pos
        self.speed = speed
        self.posy = pos[1]
        self.angle = 0
        self.count = 0.0
        self.countC = 10 # frequency
    
    def update(self):
        '''
        update fn, calculates new position on y axis
        '''
        self.count = (self.count + self.countC) % (2 * math.pi)
        bobbing_offset = math.sin(self.count) * self.speed
        self.pos[1] = self.posy + bobbing_offset

    def render(self, surf):
        '''
        renders img on screen
        '''
        surf.blit(self.img, self.pos)

class Levelbar:
    def __init__(self, level, pos=[0,0]):
        '''
        initializing the level counter
        (current level, position=[x,y])
        '''
        self.level = level
        self.pos = pos
    
    def update(self):
        '''
        updates level
        '''

    def render(self, surf):
        '''
        renders img on screen
        '''
        myfont = pygame.font.SysFont(None, 20)
        current_level = myfont.render(str(self.level), True, (255,255,0))
        surf.blit(current_level, self.pos)