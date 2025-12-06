#!/usr/bin/env python3

from random import randint
from math import pi, atan2, sin, cos
import pygame

# Constants
WIDTH = 1024
HEIGHT = 576
BACKGROUND_COLOUR = (0, 0, 64)
BOID_COLOUR = (255, 255, 255)
NUM_BOIDS = 30
BOID_VIEWRANGE_PX = 100
VELOCITY = 10 # px per frame

ALIGN_WEIGHT = 0.4
COHESION_WEIGHT = 0.4
SEPARATION_WEIGHT = 0.2

RAD_TO_DEG = 180/pi
DEG_TO_RAD = pi/180

boid_locations = []
boid_headings = []

class Boid(pygame.sprite.Sprite):
	def __init__(self, i):
		super().__init__()

		# Saving boid index
		self.boid_no = i

		# Generating the boid sprite's image (an arrow shape)
		self.image = pygame.Surface([10, 15], pygame.SRCALPHA)
		pygame.draw.polygon(self.image, BOID_COLOUR, [(0, 15), (5, 0), (10, 15), (5, 10)])
		self.rect = self.image.get_rect()

		# Randomising the boid's position on the screen
		xpos = randint(0, WIDTH)
		ypos = randint(0, HEIGHT)
		heading = randint(0, 360)

		# Saving position/heading
		boid_locations.append((xpos, ypos))
		boid_headings.append(heading)

		# Setting position/heading and original boid image
		self.rect.x = xpos
		self.rect.y = ypos
		boid_headings[i] = heading
		self.original_image = self.image

		# Rotating the boid to a random heading
		self.rotate_boid(boid_headings[i])

	def rotate_boid(self, heading):
		"""
		Rotating the boid (from the original image, to avoid distortion) to a certain angle clockwise from directly up the screen
		"""
		self.image = pygame.transform.rotate(self.original_image, -heading)

		# Creating the new rect with the same centre as the old rect
		old_centre = self.rect.center
		self.rect = self.image.get_rect(center=old_centre)

	def find_local_boids(self, my_index):
		"""
		Computes the distance to each boid and determines whether it's within the current boid's viewrange
		"""
		local_boids = []

		for i in range(len(boid_locations)):
			dist_sq = (boid_locations[i][0] - boid_locations[my_index][0])**2 + (boid_locations[i][1] - boid_locations[my_index][1])**2

			if dist_sq < BOID_VIEWRANGE_PX**2 and i != self.boid_no:
				local_boids.append(i)

		return local_boids

	def alignment(self, local_boids):
		"""
		Computes the average heading of the local boids
		"""
		headings_sum = 0

		for i in local_boids:
			headings_sum += boid_headings[i]

		return headings_sum/len(local_boids)

	def cohesion(self, local_boids):
		"""
		Computes the centre of mass of the local boids and a heading delta to it (+ CW)
		"""
		x_sum = 0
		y_sum = 0

		# Summing up the positions
		for i in local_boids:
			x_sum += boid_locations[i][0]
			y_sum += boid_locations[i][1]

		# Calculating the mean position
		x_sum /= len(local_boids)
		y_sum /= len(local_boids)

		# Calculating angle to the centre of mass from the current boid's location
		angle = atan2(x_sum-boid_locations[self.boid_no][0], y_sum-boid_locations[self.boid_no][1])

		return angle*RAD_TO_DEG - boid_headings[self.boid_no]

	def separation(self, local_boids):
		"""
		Calculates a steering angle to avoid crashing into other local boids
		"""
		my_i = self.boid_no
		x_sum = 0
		y_sum = 0

		# Sums up the vector from other local boids to this boid divided by the square of the distance between them
		# Results in small vector at large distances, very large vector at small distances
		for i in local_boids:
			dx = boid_locations[my_i][0] - boid_locations[i][0]
			dy = boid_locations[my_i][1] - boid_locations[i][1]

			mag_sq = dx**2 + dy**2

			x_sum += dx/mag_sq
			y_sum += dy/mag_sq

		# Converting the vector computed above into a steering angle
		angle = atan2(x_sum, y_sum)

		return angle*RAD_TO_DEG - boid_headings[my_i]

	def bounce_at_boundary(self, new_heading, new_x, new_y):
		"""
		Checking the boid's location won't go over the boundary of the screen, and if it does, bouncing it off the edge
		"""
		# Reflect off the side walls of the screen
		if new_x < 0 or new_x > WIDTH:
			return 360 - new_heading

		# Reflect off the top/bottom of the screen
		if new_y < 0 or new_y > HEIGHT:
			return (540 - new_heading)%360

		return new_heading

	def update(self):
		"""
		Updates the boid's position
		"""
		local_boids = self.find_local_boids(self.boid_no)

		# If there are local boids, use them to adjust your heading
		if len(local_boids) != 0:
			alignment_angle = self.alignment(local_boids)
			cohesion_angle = self.cohesion(local_boids)
			separation_angle = self.separation(local_boids)

			# Combining the heading angles and weighting them, and ensuring the range is 0->360 degrees
			new_heading = alignment_angle*ALIGN_WEIGHT + cohesion_angle*COHESION_WEIGHT + separation_angle*SEPARATION_WEIGHT
			new_heading %= 360

		# Else, slightly randomise your heading
		else:
			new_heading = boid_headings[self.boid_no] + randint(-5, 5)

		# Calculating new location
		new_x = self.rect.x + VELOCITY*sin(new_heading*DEG_TO_RAD)
		new_y = self.rect.y + VELOCITY*cos(new_heading*DEG_TO_RAD)

		# Checking the boid won't go over the boundary
		new_heading = self.bounce_at_boundary(new_heading, new_x, new_y)

		# Rotating boid to new heading
		self.rotate_boid(new_heading)
		boid_headings[self.boid_no] = new_heading

		# Moving boid
		self.rect.x = new_x
		self.rect.y = new_y


if __name__ == "__main__":
	pygame.init()
	clock = pygame.time.Clock()

	# Creating the display window
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	screen.fill(BACKGROUND_COLOUR)
	pygame.display.set_caption("Boid's Algorithm")

	# Creating the sprite group
	boids = pygame.sprite.Group()

	# Creating the sprites
	for i in range(NUM_BOIDS):
		boids.add(Boid(i))

	# Running the game and updating the sprites
	run = True
	while run:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False

		# Setting max frame rate to 24fps
		clock.tick(24)

		# Clears the screen in the new frame
		screen.fill(BACKGROUND_COLOUR)

		# Runs the boid update function, draws them on the screen, and then updates the screen
		boids.update()
		boids.draw(screen)
		pygame.display.flip()

	pygame.quit()