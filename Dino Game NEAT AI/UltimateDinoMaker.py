import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

import pygame
import neat
import time
import random
import pickle
from pygame_widgets import Slider
pygame.font.init()
pygame.mixer.pre_init(buffer=512)
pygame.mixer.init()

WIN_WIDTH = int(600 * 2.5)
WIN_HEIGHT = int(150 * 5)
GROUND_Y = WIN_HEIGHT * 0.85
GROUND_LEVEL = GROUND_Y + 25
DINO_X = WIN_WIDTH / 15
SPAWN_MIN = 50
SPAWN_MAX = 100
BIRD_SPAWN_CHANCE = 0
SCORE_RATE = 5
FLASH_SPEED = 10

vel = 10
highscore = 0
score_colour = (83, 83, 83)
gen = 0
speed = 1

DINO_IMGS = [
    pygame.image.load(resource_path("Dino Game NEAT AI/Sprites/dino walking 1.png")),
    pygame.image.load(resource_path("Dino Game NEAT AI/Sprites/dino walking 2.png")), 
    pygame.image.load(resource_path("Dino Game NEAT AI/Sprites/dino jumping.png")),
    pygame.image.load(resource_path("Dino Game NEAT AI/Sprites/dino ducking 1.png")),
    pygame.image.load(resource_path("Dino Game NEAT AI/Sprites/dino ducking 2.png")),
]

OBSTACLE_IMGS = [
    pygame.image.load(resource_path("Dino Game NEAT AI/Sprites/small1.png")),
    pygame.image.load(resource_path("Dino Game NEAT AI/Sprites/small3.png")),
    pygame.image.load(resource_path("Dino Game NEAT AI/Sprites/large1.png")),
    pygame.image.load(resource_path("Dino Game NEAT AI/Sprites/large4.png")),
    pygame.image.load(resource_path("Dino Game NEAT AI/Sprites/bird1.png")),
    pygame.image.load(resource_path("Dino Game NEAT AI/Sprites/bird2.png")),
]

GROUND_IMG = pygame.image.load(resource_path("Dino Game NEAT AI/Sprites/ground.png"))

JUMP_SOUND = pygame.mixer.Sound(resource_path("Dino Game NEAT AI/Audio/jump.mp3"))
SCOREUP_SOUND = pygame.mixer.Sound(resource_path("Dino Game NEAT AI/Audio/jump.mp3"))
SCOREUP_SOUND.set_volume(0.2)
DEATH_SOUND = pygame.mixer.Sound(resource_path("Dino Game NEAT AI/Audio/jump.mp3"))

STAT_FONT = pygame.font.Font(resource_path("Dino Game NEAT AI/Other/PressStart2P-Regular.ttf"), 25)


class Dino:
    IMGS = DINO_IMGS
    ANIMATION_SPEED = 3
    FIRST_WALKING_FRAME_INDEX = 0
    LAST_WALKING_FRAME_INDEX = 1
    JUMPING_FRAME_INDEX = 2
    FIRST_DUCKING_FRAME_INDEX = 3
    LAST_DUCKING_FRAME_INDEX = 4
    SMALL_JUMP_FORCE = -15
    BIG_JUMP_FORCE = -20
    GRAVITY = 1

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel = 0
        self.img_index = 0
        self.animation_counter = 0
        self.img = self.IMGS[self.img_index]
        self.height = self.img.get_height()
        self.width = self.img.get_width()
        self.state = "running"
        self.bottom = self.y + self.height

    def small_jump(self):
        if self.state == "running":
            pygame.mixer.Sound.play(JUMP_SOUND)
            self.vel = self.SMALL_JUMP_FORCE
            self.state = "jumping"
    
    def big_jump(self):
        if self.state == "running":
            pygame.mixer.Sound.play(JUMP_SOUND)
            self.vel = self.BIG_JUMP_FORCE
            self.state = "jumping"

    def duck(self):
        if self.state == "running":
            self.state = "ducking"

    def do_nothing(self):
        pass

    def move(self):
        self.height = self.img.get_height()
        self.y += self.vel

        self.vel += self.GRAVITY

        if self.state == "ducking":
            self.height = self.img.get_height()
            self.y = GROUND_LEVEL - self.height

        if self.y + self.height > GROUND_LEVEL:
            self.vel = 0
            self.y = GROUND_LEVEL - self.height
            self.state = "running"

        self.bottom = self.y + self.height

    def draw(self, win):
        if self.state == "running":
            self.animation_counter += 1

            if self.animation_counter > self.ANIMATION_SPEED:
                if self.img_index < self.LAST_WALKING_FRAME_INDEX and self.img_index >= self.FIRST_WALKING_FRAME_INDEX:
                    self.img_index += 1
                elif self.img_index >= self.LAST_WALKING_FRAME_INDEX:
                    self.img_index = self.FIRST_WALKING_FRAME_INDEX
                elif self.img_index < self.FIRST_WALKING_FRAME_INDEX:
                    self.img_index = self.FIRST_WALKING_FRAME_INDEX

                self.animation_counter = 0
        elif self.state == "jumping":
            self.img_index = self.JUMPING_FRAME_INDEX
        elif self.state == "ducking":
            self.animation_counter += 1

            if self.animation_counter > self.ANIMATION_SPEED:
                if self.img_index < self.LAST_DUCKING_FRAME_INDEX and self.img_index >= self.FIRST_DUCKING_FRAME_INDEX:
                    self.img_index += 1
                elif self.img_index >= self.LAST_DUCKING_FRAME_INDEX:
                    self.img_index = self.FIRST_DUCKING_FRAME_INDEX
                elif self.img_index < self.FIRST_DUCKING_FRAME_INDEX:
                    self.img_index = self.FIRST_DUCKING_FRAME_INDEX

                self.animation_counter = 0

        self.img = self.IMGS[self.img_index]

        win.blit(self.img, (self.x, self.y))

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Obstacle:
    IMGS = OBSTACLE_IMGS
    BIRD_Y = [0, 70, 160]
    ANIMATION_SPEED = 10

    def __init__(self, species):
        self.x = WIN_WIDTH
        self.species = species

        self.top = 0
        self.bottom = 0
        self.img = self.IMGS[self.species]
        self.width = self.img.get_width()
        self.height = self.img.get_height()
        self.animation_counter = 0
        self.bird_height = 0

        self.setup()

    def setup(self):
        self.top = GROUND_LEVEL - self.height

        if self.species >= 4:
            randex = random.randint(0, 2)
            self.top -= self.BIRD_Y[randex]
            self.bird_height = self.top

        self.bottom = self.top + self.height 

    def move(self):
        self.x -= vel

    def draw(self, win):
        if self.species >= 4:
            self.animation_counter += 1

            if self.animation_counter > self.ANIMATION_SPEED:
                if self.img == self.IMGS[4]:
                    self.img = self.IMGS[5]
                elif self.img == self.IMGS[5]:
                    self.img = self.IMGS[4]

                self.animation_counter = 0
        
        win.blit(self.img, (self.x, self.top))

    def collide(self, dino):
        dino_mask = dino.get_mask()
        obstacle_mask = pygame.mask.from_surface(self.img)

        offset = (round(self.x) - round(dino.x), round(self.top) - round(dino.y))

        point = dino_mask.overlap(obstacle_mask, offset)

        if point:
            return True

        return False


class Ground:
    WIDTH = GROUND_IMG.get_width()
    IMG = GROUND_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= vel
        self.x2 -= vel

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, ground, dinos, obstacles, score, highscore, gen, slider, speed, bird_slider, bird_spawn_chance):
    win.fill([247, 247, 247])

    ground.draw(win)

    for obstacle in obstacles:
        obstacle.draw(win)
    
    for dino in dinos:
        dino.draw(win)

    score_text = STAT_FONT.render(str(score).zfill(5), 1, score_colour)
    win.blit(score_text, (WIN_WIDTH - score_text.get_width() - 10, 10))

    highscore_text = STAT_FONT.render("HI " + str(highscore).zfill(5) + " ", 1, (115, 115, 115))
    win.blit(highscore_text, (WIN_WIDTH - score_text.get_width() - highscore_text.get_width() - 10, 10))

    speed_text = STAT_FONT.render("SPEED:         x" + str(speed), 1, (83, 83, 83))
    win.blit(speed_text, (10, 10))

    bird_text = STAT_FONT.render("BIRD SPAWN CHANCE:         " + str(bird_spawn_chance) + "%", 1, (83, 83, 83))
    win.blit(bird_text, (10, speed_text.get_height() + 20))

    gen_text = STAT_FONT.render("GEN: " + str(gen), 1, (83, 83, 83))
    win.blit(gen_text, (10, speed_text.get_height()*2 + 30))

    slider.draw()

    bird_slider.draw()

    pygame.display.update()

win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
slider = Slider(
    win, 
    170, 
    10, 
    200, 
    25, 
    min=1, 
    max=10, 
    step=1, 
    initial=1, 
    handleRadius=12, 
    curved=False, 
    handleColour=(83, 83, 83)
)
bird_slider = Slider(
    win, 
    470, 
    45, 
    200, 
    25, 
    min=0, 
    max=100, 
    step=1, 
    initial=0, 
    handleRadius=12, 
    curved=False, 
    handleColour=(83, 83, 83)
)

def main(genomes, config):
    global highscore
    global vel
    global score_colour
    global gen
    global speed
    global BIRD_SPAWN_CHANCE

    vel = 10
    score_colour = (83, 83, 83)
    gen += 1

    nets = []
    ge = []
    dinos = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        dinos.append(Dino(DINO_X, GROUND_LEVEL + 94))
        g.fitness = 0
        ge.append(g)

    ground = Ground(GROUND_Y)
    obstacles = [Obstacle(0)]

    clock = pygame.time.Clock()

    spawn_counter = 0
    next_spawn = random.randrange(SPAWN_MIN, SPAWN_MAX)

    score_counter = 0
    score = 0
    flashing = False
    flash_counter = 0
    flash_num = 0
    frozen_score = 0

    run = True
    while run:
        clock.tick(60)
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        for _ in range(speed):

            slider.listen(events)
            speed = slider.getValue()

            bird_slider.listen(events)
            BIRD_SPAWN_CHANCE = bird_slider.getValue()

            obstacle_ind = 0
            if len(dinos) > 0:
                if len(obstacles) > 1 and dinos[0].x > obstacles[0].x + obstacles[0].width:
                    obstacle_ind = 1
            else:
                run = False
                break
                return

            for x, dino in enumerate(dinos):
                dino.move()
                ge[x].fitness += 0.1

                if len(obstacles) > 0:
                    output = nets[x].activate((
                        obstacles[obstacle_ind].x,
                        obstacles[obstacle_ind].top,
                        obstacles[obstacle_ind].bottom,
                        obstacles[obstacle_ind].height,
                        obstacles[obstacle_ind].width,
                        obstacles[obstacle_ind].species,
                        dino.y,
                        dino.bottom,
                        dino.vel,
                        vel
                    ))

                    dino_actions = {
                        0: dino.small_jump,
                        1: dino.big_jump,
                        2: dino.duck,
                        3: dino.do_nothing
                    }

                    dino_action = dino_actions.get(output.index(max(output)), lambda: "Invalid output")
                    dino_action()

            spawn_counter += 1
            if spawn_counter > next_spawn:
                chance = random.randint(0, 100)
                if chance < BIRD_SPAWN_CHANCE:
                    obstacles.append(Obstacle(4))
                else:
                    obstacles.append(Obstacle(random.randint(0, 3)))
                spawn_counter = 0
                next_spawn = random.randrange(SPAWN_MIN, SPAWN_MAX)

            rem = []
            for obstacle in obstacles:
                for x, dino in enumerate(dinos):
                    if obstacle.collide(dino):
                        pygame.mixer.Sound.play(DEATH_SOUND)
                        ge[x].fitness -= 1
                        dinos.pop(x)
                        nets.pop(x)
                        ge.pop(x)

                obstacle.move()

                if obstacle.x + obstacle.width < 0:
                    rem.append(obstacle)

            for r in rem:
                obstacles.remove(r)

            ground.move()

            score_counter += 1
            if score_counter > SCORE_RATE:
                score += 1
                score_counter = 0
                if score % 100 == 0 and score >= 100:
                    vel += 1
                    pygame.mixer.Sound.play(SCOREUP_SOUND)
                    flash_counter = 0
                    flash_num = 6
                    score_colour = (247, 247, 247)
                    frozen_score = score
                    flashing = True
            if score > highscore:
                highscore = score

            if flashing == True:
                if flash_counter < FLASH_SPEED:
                    flash_counter += 1
                else:
                    if score_colour == (83, 83, 83):
                        score_colour = (247, 247, 247)
                    else:
                        score_colour = (83, 83, 83)
                    flash_counter = 0
                    flash_num -= 1
                if flash_num < 0:
                    flash_counter = 0
                    flashing = False

        if flashing == True:
            draw_window(win, ground, dinos, obstacles, frozen_score, highscore, gen, slider, speed, bird_slider, BIRD_SPAWN_CHANCE)
        else: 
            draw_window(win, ground, dinos, obstacles, score, highscore, gen, slider, speed, bird_slider, BIRD_SPAWN_CHANCE)


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, float("inf"))

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = resource_path("Dino Game NEAT AI/Other/config-feedforward.txt")
    run(config_path)
