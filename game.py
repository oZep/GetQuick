import sys
import os
import math
import random
import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Skeleton, Spider, Boss
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark
from scripts.UI import Heart, Levelbar

class Game:
    def __init__(self):
        '''
        initializes Game
        '''
        pygame.init()

        # change the window caption
        pygame.display.set_caption("9 Levels of Hell")
        # create window
        self.screen = pygame.display.set_mode((640, 480)) # (640, 480), (960, 720), (768, 576)

        self.display_red= pygame.Surface((320, 240), pygame.SRCALPHA) # render on smaller resolution then scale it up to bigger screen

        self.display_white = pygame.Surface((320, 240), pygame.SRCALPHA) # render on smaller resolution then scale it up to bigger screen
        self.display_black = pygame.Surface((320, 240), pygame.SRCALPHA) # render on smaller resolution then scale it up to bigger screen
        self.display_none = pygame.Surface((320, 240), pygame.SRCALPHA) # render on smaller resolution then scale it up to bigger screen

        self.display_2 = pygame.Surface((320, 240))


        self.clock = pygame.time.Clock()
        
        self.movement = [False, False, False, False]

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player/player.png'),
            'background': load_image('background.png'),
            'heart': load_image('UI/health.png'),
            'sheild': load_image('UI/sheild.png'),
            'skele/idle': Animation(load_images('entities/skele/idle'), img_dur=1),
            'skele/run': Animation(load_images('entities/skele/run'), img_dur=4),
            'spid/idle': Animation(load_images('entities/spider/idle'), img_dur=1),
            'spid/run': Animation(load_images('entities/spider/run'), img_dur=4),
            'boss/idle': Animation(load_images('entities/boss/idle'), img_dur=10),
            'boss/dash': Animation(load_images('entities/boss/dash'), img_dur=1),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=1),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/runDOWN': Animation(load_images('entities/player/runDOWN'), img_dur=4),
            'player/runUP': Animation(load_images('entities/player/runUP'), img_dur=6),
            'player/slide': Animation(load_images('entities/player/slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'bow': load_image('bow.png'),
            'staff': load_image('staff.png'),
            'projectile': load_image('projectile.png'),
            'magic': load_image('magic.png'),
        }

        # adding sound
        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        }
        
        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)

        #self.clouds = Clouds(self.assets['clouds'], count=16)

        # initalizing player
        self.player = Player(self, (self.display_red.get_width()/2, self.display_red.get_height()/2), (15, 15))

        # initalizing tilemap
        self.tilemap = Tilemap(self, tile_size=16)

        # tracking level
        self.level = 0
        self.max_level = len(os.listdir('data/maps')) # max level,
        # loading the level
        self.load_level(0)  # self.load_level(self.level), hard coding to 1 atm

        # screen shake
        self.screenshake = 0

        self.cooldown = 0


    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')

        # keep track
        self.particles = []

        # creating 'camera' 
        self.scroll = [0, 0]

        self.dead = -2  # gives player 3 lives, -2, -1, 0

        self.projectiles = []
        self.sparks = []

        # transition for levels
        self.transition = -30

        # leaf particle affect
        # change this to be like embers that spawns maybe on the border of the map, or i can make a transparent spawner
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect((4 + tree['pos'][0]), (4 + tree['pos'][1]), 23, 13)) # offsetting by 4 due to tree sprite
            # Rect(x, y, width, height)
        
        # spawn the ememies
        self.spiders = []
        # spawn the ememies
        self.skeletons = []
        self.boss = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 2), ('spawners', 3)]):
            if spawner['variant'] == 0: 
                self.player.pos = spawner['pos']
            elif spawner['variant'] == 1:
                self.skeletons.append(Skeleton(self, spawner['pos'], (7, 15)))
            elif spawner['variant'] == 2:
                self.spiders.append(Spider(self, spawner['pos'], (10, 7)))
            else:
                self.boss.append(Boss(self, spawner['pos'], (21, 31)))
                # spawn the ememies

    def run(self):
        '''
        runs the Game
        '''
        #pygame.mixer.music.load('data/music.wav')
        #pygame.mixer.music.set_volume(0.5)
        #pygame.mixer.music.play(-1)

        # self.sfx['ambience'].play(-1)

        # creating an infinite game loop
        while True:
            self.display_red.fill((0, 0, 0, 0))    # red outlines
            self.display_white.fill((0, 0, 0, 0))    # white outlines
            self.display_black.fill((0, 0, 0, 0))    # black outlines
            self.display_none.fill((0,0,0,0))
            # clear the screen for new image generation in loop
            self.display_2.blit(self.assets['background'], (0,0)) # no outline

            self.screenshake = max(0, self.screenshake-1) # resets screenshake value

            # level transiition
            if not len(self.skeletons) and not len(self.spiders) and not len(self.boss): 
                self.transition += 1 # start timer, increasing value past 0
                if self.transition > 30: 
                    self.level = min(self.level + 1, self.max_level -1) # increase level
                    self.load_level(4) # self.load_level(self.level) 
            if self.transition < 0:
                self.transition += 1 # goes up automatically until 0

            if self.dead >= 1: # get hit 3 times
                self.dead += 1
                if self.dead >= 10: # to make the level transitions smoother
                    self.transition = min(self.transition + 1, 30) # go as high as it can without changing level
                if self.dead > 40: # timer that starts when you die
                    self.level = 0
                    self.load_level(0) # start at level 0 again. self.load_level(0)
            

            # scroll = current scroll + (where we want the camera to be - what we have/can see currently) 
            self.scroll[0] = self.display_red.get_width()/2 / 30 + 3 # x axis
            self.scroll[1] = self.display_red.get_height()/2/ 30 + 3

            # fix the jitter
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            # spawn particles
            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            # self.clouds.update() # updates clouds before the rest of the tiles
            # self.clouds.render(self.display_2, offset=render_scroll)

            self.tilemap.render(self.display_white, offset=render_scroll)

            # render the enemies
            for enemy in self.skeletons.copy():
                kill =  enemy.update(self.tilemap, (0,0))
                enemy.render(self.display_black, offset=render_scroll) # change outline here
                if kill: # if enemies update fn returns true [**]
                    self.skeletons.remove(enemy) 
                if abs(self.player.dashing) < 50 and not self.cooldown: # not dashing and dead cooldown for collisions is
                    if self.player.rect().colliderect(enemy): # player collides with enemy
                        self.dead += 1 # die
                        self.sfx['hit'].play()
                        self.cooldown = 150
                        self.screenshake = max(16, self.screenshake)  # apply screenshake, larger wont be overrided by a smaller screenshake
                        for i in range(30): # when projectile hits player
                            # on death sparks
                            angle = random.random() * math.pi * 2 # random angle in a circle
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random())) 
                            # on death particles
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))

            
            # render the enemies
            for enemy in self.spiders.copy():
                kill =  enemy.update(self.tilemap, (0,0))
                enemy.render(self.display_none, offset=render_scroll) # change outline here
                if kill: # if enemies update fn returns true [**]
                    self.spiders.remove(enemy) 
                if abs(self.player.dashing) < 50 and not self.cooldown: # not dashing
                    if self.player.rect().colliderect(enemy): # player collides with enemy
                        self.dead += 1 # die
                        self.sfx['hit'].play()
                        self.cooldown = 150
                        self.screenshake = max(16, self.screenshake)  # apply screenshake, larger wont be overrided by a smaller screenshake
                        for i in range(30): # when projectile hits player
                            # on death sparks
                            angle = random.random() * math.pi * 2 # random angle in a circle
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random())) 
                            # on death particles
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))

            # render the enemies
            for enemy in self.boss.copy():
                kill =  enemy.update(self.tilemap)
                enemy.render(self.display_red, offset=render_scroll) # change outline here
                if kill: # if enemies update fn returns true [**]
                    self.boss.remove(enemy) 
                if abs(self.player.dashing) < 50 and not self.cooldown: # not dashing
                    if self.player.rect().colliderect(enemy): # player collides with enemy
                        self.dead += 1 # die
                        self.sfx['hit'].play()
                        self.cooldown = 150
                        self.screenshake = max(16, self.screenshake)  # apply screenshake, larger wont be overrided by a smaller screenshake
                        for i in range(30): # when projectile hits player
                            # on death sparks
                            angle = random.random() * math.pi * 2 # random angle in a circle
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random())) 
                            # on death particles
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))

            # Reduce timer
            if self.cooldown > 0:
                    self.cooldown -= 1

            if self.dead != 1:
                # update player movement
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], self.movement[3] - self.movement[2]))
                self.player.render(self.display_white, offset=render_scroll)

            # render/spawn bullet projectiles
            # [[x, y], direction, timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1] 
                projectile[2] += 1
                img = self.assets['projectile']
                self.display_black.blit(img if projectile[1] > 0 else pygame.transform.flip(img, True, False), (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1])) # spawns it the center of the projectile
                
                # keep this but change it to the borders of the map, also might want some obsticles later
                if self.tilemap.solid_check(projectile[0]): # if location is a solid tile
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random())) # (math.pi if projectile[1] > 0 else 0), sparks bounce in oppositie direction if hit wall which depends on projectile direction
                elif projectile[2] > 360: #if timer > 6 seconds
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50: # if not in dash
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.sfx['hit'].play()
                        self.screenshake = max(16, self.screenshake)  # apply screenshake, larger wont be overrided by a smaller screenshake
                        for i in range(30): # when projectile hits player
                            # on death sparks
                            angle = random.random() * math.pi * 2 # random angle in a circle
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random())) 
                            # on death particles
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))


            # spark affect
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display_black, (255,255,255), offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

                                    
            hp_1 = Heart(self.assets['heart'].copy(), [13, 19], 15)
            hp_2 = Heart(self.assets['heart'].copy(), [30, 19], 15)
            hp_3 = Heart(self.assets['heart'].copy(), [47, 19], 15)
            if self.dead <= 0 and self.dead < 1:
                hp_1.update()
                hp_1.render(self.display_black)
            if self.dead <= -1:
                hp_2.update()
                hp_2.render(self.display_black)
            if self.dead <= -2:
                hp_3.update()
                hp_3.render(self.display_black)

            level_bar = Levelbar(self.level, pos=(self.display_red.get_width() // 2 - 25, 13))
            level_bar.render(self.display_black, 22)
            

            # black ouline based on display_black
            display_mask = pygame.mask.from_surface(self.display_black)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0)) # 180 opaque, 0 transparent
            self.display_2.blit(display_sillhouette, (0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset) # putting what we drew onframe back into display

            # red ouline based on display
            display_mask = pygame.mask.from_surface(self.display_red)
            display_sillhouette = display_mask.to_surface(setcolor=(225, 0, 0, 180), unsetcolor=(0, 0, 0, 0)) # 180 opaque, 0 transparent
            self.display_2.blit(display_sillhouette, (0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset) # putting what we drew onframe back into display
            

            # white ouline based on display_white
            display_mask = pygame.mask.from_surface(self.display_white)
            display_sillhouette = display_mask.to_surface(setcolor=(225, 225, 225, 180), unsetcolor=(0, 0, 0, 0)) # 180 opaque, 0 transparent
            self.display_2.blit(display_sillhouette, (0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset) # putting what we drew onframe back into display
            

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display_red, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3 # making the parlitcle move back and forth smooth'y
                if kill:
                    self.particles.remove(particle)


            for event in pygame.event.get():
                if event.type == pygame.QUIT: # have to code the window closing
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a: # referencing WASD
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_j:
                        self.player.dash('J')
                    if event.key == pygame.K_i:
                        self.player.dash('I')
                    if event.key == pygame.K_l:
                        self.player.dash('L')
                    if event.key == pygame.K_k:
                        self.player.dash('K')
                if event.type == pygame.KEYUP: # when key is released
                    if event.key == pygame.K_a: 
                        self.movement[0] = False
                    if event.key == pygame.K_d: 
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
            
            self.display_2.blit(self.display_white, (0, 0)) # white
            self.display_2.blit(self.display_red, (0, 0)) # red 
            self.display_2.blit(self.display_black, (0, 0)) # black 
            self.display_2.blit(self.display_none, (0,0))
            
            # implementing transition
            if self.transition:
                transition_surf = pygame.Surface(self.display_red.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display_red.get_width() // 2, self.display_red.get_height() // 2), (30 - abs(self.transition)) * 8) # display center of screen, 30 is the timer we chose, 30 * 8 = 180
                transition_surf.set_colorkey((255, 255, 255)) # making the circle transparent now
                self.display_2.blit(transition_surf, (0, 0))

            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset) # render (now scaled) display image on big screen
            pygame.display.update()
            self.clock.tick(60) # run at 60 fps, like a sleep

# returns the game then runs it
Game().run()