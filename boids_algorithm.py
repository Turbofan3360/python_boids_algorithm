#!/usr/bin/env python3

from random import randint
import pygame

# Constants
WIDTH = 1024
HEIGHT = 576
BACKGROUND_COLOUR = (0, 0, 64)
BOID_COLOUR = (255, 255, 255)
NUM_BOIDS = 20

class Boid(pygame.sprite.Sprite):
	def __init__(self):
		super().__init__()

		# Generating the boid sprite's image (an arrow shape)
		self.image = pygame.Surface([10, 15], pygame.SRCALPHA)
		pygame.draw.polygon(self.image, BOID_COLOUR, [(0, 15), (5, 0), (10, 15), (5, 10)])
		self.rect = self.image.get_rect()

		# Randomising the boid's position on the screen
		self.rect.x = randint(0, WIDTH)
		self.rect.y = randint(0, HEIGHT)
		self.heading = randint(0, 360)

		# Saving the original boid image
		self.original_image = self.image

		# Rotating the boid to a random heading
		self.rotate_boid(self.heading)

	def rotate_boid(self, angle):
		# Rotating the boid (from the original image, to avoid distortion) by a certain angle from its current heading
		self.image = pygame.transform.rotate(self.original_image, -(self.heading+angle))

		# Creating the new rect with the same centre as the old rect
		old_centre = self.rect.center
		self.rect = self.image.get_rect(center=old_centre)



if __name__ == "__main__":
	pygame.init()
	clock = pygame.time.Clock()

	# Creating the display window
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	screen.fill(BACKGROUND_COLOUR)
	pygame.display.set_caption("Boid's Algorithm")

	# Setting max. frame rate to 24fps
	clock.tick(24)

	# Creating the sprite group
	boids = pygame.sprite.Group()

	# Creating the sprites
	for i in range(NUM_BOIDS):
		boids.add(Boid())

	# Running the game and updating the sprites
	run = True
	while run:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False

		boids.update()
		boids.draw(screen)

		pygame.display.flip()

	pygame.quit()