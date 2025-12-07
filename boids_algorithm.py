#!/usr/bin/env python3

from random import randint
from math import pi, atan2, sin, cos
import pygame

# Constants
WIDTH = 1024
HEIGHT = 576
BACKGROUND_COLOUR = (0, 0, 64)
BOID_COLOUR = (255, 255, 255)
NUM_BOIDS = 40
BOID_VIEWRANGE_PX = 50
VELOCITY = 10 # px per frame

ALIGN_WEIGHT = 0.5
COHESION_WEIGHT = 0.3
SEPARATION_WEIGHT = 0.4

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
		boid_locations.append([xpos, ypos])
		boid_headings.append(heading)

		# Setting position/heading and original boid image
		self.rect.x = xpos
		self.rect.y = ypos
		boid_headings[i] = heading
		self.original_image = self.image
		self.prev_vec = (0, 0)

		# Rotating the boid to a random heading
		self.rotate_boid(boid_headings[i])

	def normalize_vector(self, x, y, len_desired):
		"""
		Normalizes a 2D Vector to a vector of length velocity
		"""
		length = (x**2 + y**2)**0.5

		# Guarding against zero devision error
		if length == 0:
			return 0, 0

		return x*len_desired/length, y*len_desired/length

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
		x_sum = 0
		y_sum = 0

		for i in local_boids:
			x_sum += sin(boid_headings[i]*DEG_TO_RAD)
			y_sum += -cos(boid_headings[i]*DEG_TO_RAD)

		return self.normalize_vector(x_sum, y_sum, 1)

	def cohesion(self, local_boids):
		"""
		Computes the centre of mass of the local boids and a heading delta to it (+ CW)
		"""
		x_sum = 0
		y_sum = 0

		my_x = boid_locations[self.boid_no][0]
		my_y = boid_locations[self.boid_no][1]

		# Summing up the position vectors of other local boids
		for i in local_boids:
			x_sum += boid_locations[i][0]
			y_sum += boid_locations[i][1]

		# Calculating the mean position
		x_sum /= len(local_boids)
		y_sum /= len(local_boids)

		# Computing the vector between me and the mean position
		dx = x_sum - my_x
		dy = y_sum - my_y

		return self.normalize_vector(dx, dy, 1)

	def separation(self, local_boids):
		"""
		Calculates a steering angle to avoid crashing into other local boids
		"""
		x_sum = 0
		y_sum = 0

		my_x = boid_locations[self.boid_no][0]
		my_y = boid_locations[self.boid_no][1]

		# Sums up the vector from other local boids to this boid divided by the square of the distance between them
		# Results in small vector at large distances, very large vector at small distances
		for i in local_boids:
			dx = my_x - boid_locations[i][0]
			dy = my_y - boid_locations[i][1]

			mag_sq = dx**2 + dy**2

			if mag_sq != 0:
				x_sum += dx/mag_sq
				y_sum += dy/mag_sq

			# Protecting against zero division error (minimum distance, in theory, is 1 pixel as the coordinates are integers)
			else:
				x_sum += dx
				y_sum += dy

		return self.normalize_vector(x_sum, y_sum, 1)

	def bounce_at_boundary(self, boid_no, xvec, yvec):
		"""
		Checking the boid's location won't go over the boundary of the screen, and if it does, bouncing it off the edge
		"""
		new_x = boid_locations[boid_no][0] + xvec
		new_y = boid_locations[boid_no][1] + yvec

		# Reflect off the side walls of the screen
		if new_x < 0 or new_x > WIDTH - 20:
			xvec = -xvec

		# Reflect off the top/bottom of the screen
		if new_y < 0 or new_y > HEIGHT - 20:
			yvec = -yvec

		return (xvec, yvec)

	def smoothing(self, vecx, vecy):
		"""
		Exponential smoothing of the Boid's velocity vector by looking at its previous velocity vector
		"""
		alpha = 0.35

		vecx = vecx*alpha + (1-alpha)*self.prev_vec[0]
		vecy = vecy*alpha + (1-alpha)*self.prev_vec[1]

		return (vecx, vecy)

	def update(self):
		"""
		Updates the boid's position
		"""
		local_boids = self.find_local_boids(self.boid_no)

		# If there are local boids, use them to adjust your heading vector
		if len(local_boids) != 0:
			alignment_vector = self.alignment(local_boids)
			cohesion_vector = self.cohesion(local_boids)
			separation_vector = self.separation(local_boids)

			steering_vector = [0, 0]

			# Combining vectors, with a small random factor as well
			steering_vector[0] = alignment_vector[0]*ALIGN_WEIGHT + cohesion_vector[0]*COHESION_WEIGHT + separation_vector[0]*SEPARATION_WEIGHT + randint(-100, 100)/500
			steering_vector[1] = alignment_vector[1]*ALIGN_WEIGHT + cohesion_vector[1]*COHESION_WEIGHT + separation_vector[1]*SEPARATION_WEIGHT + randint(-100, 100)/500

		# Else, slightly randomise your heading vector
		else:
			randomized_heading = boid_headings[self.boid_no] + randint(-10, 10)

			steering_vector = [0, 0]

			steering_vector[0] = sin(randomized_heading*DEG_TO_RAD)
			steering_vector[1] = -cos(randomized_heading*DEG_TO_RAD)

		# Normalizing vector to length velocity, smoothing it, and re-normalizing it
		steering_vector = self.normalize_vector(steering_vector[0], steering_vector[1], VELOCITY)
		steering_vector = self.smoothing(steering_vector[0], steering_vector[1])
		steering_vector = self.normalize_vector(steering_vector[0], steering_vector[1], VELOCITY)

		# Computing new position and checking the boid won't go over the boundary
		steering_vector = self.bounce_at_boundary(self.boid_no, steering_vector[0], steering_vector[1])

		# Computing heading from that new vector and wrapping it into 0->360 degrees
		new_heading = (atan2(steering_vector[0], -steering_vector[1]) * RAD_TO_DEG)%360

		# Rotating boid to new heading
		self.rotate_boid(new_heading)

		# Moving boid
		self.rect.x += steering_vector[0]
		self.rect.y += steering_vector[1]

		boid_headings[self.boid_no] = new_heading
		boid_locations[self.boid_no][0] = self.rect.x
		boid_locations[self.boid_no][1] = self.rect.y
		self.prev_vec = steering_vector


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