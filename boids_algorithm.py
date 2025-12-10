#!/usr/bin/env python3

from random import randint, uniform
from math import pi, atan2
import pygame

# Constants
WIDTH = 1500
HEIGHT = 900
BACKGROUND_COLOUR = (0, 0, 64)
BOID_COLOUR = (255, 255, 255)
NUM_BOIDS = 50
BOID_VIEWRANGE_PX = 75
VELOCITY = 10 # px per frame

ALIGN_WEIGHT = 0.7
COHESION_WEIGHT = 0.25
SEPARATION_WEIGHT = 0.4
SMOOTHING_WEIGHT = 0.35

RAD_TO_DEG = 180/pi
VIEWRANGE_SQ = BOID_VIEWRANGE_PX**2

boid_locations = []
boid_heading_vectors = []

class Boid(pygame.sprite.Sprite):
	def __init__(self, i):
		super().__init__()

		# Saving boid index
		self.boid_no = i

		# Generating the boid sprite's image (an arrow shape)
		self.image = pygame.Surface([10, 15], pygame.SRCALPHA)
		pygame.draw.polygon(self.image, BOID_COLOUR, [(0, 15), (5, 0), (10, 15), (5, 10)])
		self.rect = self.image.get_rect()

		# Randomising the boid's position on the screen and heading vector
		pos_vec = pygame.math.Vector2(randint(0, WIDTH), randint(0, HEIGHT))
		heading_vec = pygame.math.Vector2(uniform(-1, 1), uniform(-1, 1))
		heading_vec = self.safe_normalize(heading_vec)

		# Saving position/heading
		boid_locations.append(pos_vec)
		boid_heading_vectors.append(heading_vec)

		# Setting position/heading and original boid image
		self.rect.x = pos_vec.x
		self.rect.y = pos_vec.y
		self.original_image = self.image

		# Rotating the boid to a random heading
		self.rotate_boid(heading_vec)

	def safe_normalize(self, vector):
		"""
		Handles normalization of pygame.math.Vector2() vectors that potentially have zero length
		"""
		try:
			vector = vector.normalize()
		except ValueError:
			vector.x = 0
			vector.y = 0

		return vector

	def rotate_boid(self, headingvec):
		"""
		Rotating the boid (from the original image, to avoid distortion) to point in a certain vector
		"""
		heading = (atan2(headingvec.x, -headingvec.y)*RAD_TO_DEG)%360

		self.image = pygame.transform.rotate(self.original_image, -heading)

		# Creating the new rect with the same centre as the old rect
		old_centre = self.rect.center
		self.rect = self.image.get_rect(center=old_centre)

	def find_local_boids(self):
		"""
		Computes the distance to each boid and determines whether it's within the current boid's viewrange
		"""
		local_boids = []

		for i in range(len(boid_locations)):
			if i == self.boid_no:
				continue

			d_vector = boid_locations[i] - boid_locations[self.boid_no]

			if d_vector.magnitude_squared() < VIEWRANGE_SQ:
				local_boids.append(i)

		return local_boids

	def alignment(self, local_boids):
		"""
		Computes the average heading of the local boids
		"""
		vector = pygame.math.Vector2(0, 0)

		for i in local_boids:
			vector += boid_heading_vectors[i]

		return self.safe_normalize(vector)

	def cohesion(self, local_boids):
		"""
		Computes the centre of mass of the local boids and a vector to it from the current boid's location
		"""
		com_vector = pygame.math.Vector2(0, 0)
		my_vector = boid_locations[self.boid_no]

		# Summing up the position vectors of other local boids
		for i in local_boids:
			com_vector += boid_locations[i]

		# Calculating the mean position
		com_vector /= len(local_boids)

		# Computing the vector between me and the mean position
		d_vector = com_vector - my_vector

		return self.safe_normalize(d_vector)

	def separation(self, local_boids):
		"""
		Calculates a steering vector to avoid crashing into other local boids
		"""
		sep_vector = pygame.math.Vector2(0, 0)
		my_vector = boid_locations[self.boid_no]

		# Sums up the vector from other local boids to this boid divided by the square of the distance between them
		# Results in small vector at large distances, very large vector at small distances
		for i in local_boids:
			d_vector = my_vector - boid_locations[i]

			sep_vector += d_vector/d_vector.magnitude_squared()

		return self.safe_normalize(sep_vector)

	def bounce_at_boundary(self, vel_vector):
		"""
		Checking the boid's location won't go over the boundary of the screen, and if it does, bouncing it off the edge
		"""
		new_location = boid_locations[self.boid_no] + vel_vector

		# Reflect off the side walls of the screen
		if new_location.x < 0 or new_location.x > WIDTH - 20:
			vel_vector.x *= -1

		# Reflect off the top/bottom of the screen
		if new_location.y < 0 or new_location.y > HEIGHT - 20:
			vel_vector.y *= -1

		return vel_vector

	def smoothing(self, vector):
		"""
		Exponential smoothing of the Boid's velocity vector by looking at its previous velocity vector
		Also scales the vector to be of length VELOCITY
		"""
		vector.scale_to_length(VELOCITY)
		vector = vector*SMOOTHING_WEIGHT + (1-SMOOTHING_WEIGHT)*boid_heading_vectors[self.boid_no]
		vector.scale_to_length(VELOCITY)

		return vector

	def update(self):
		"""
		Updates the boid's position
		"""
		local_boids = self.find_local_boids()

		steering_vector = pygame.math.Vector2(0, 0)
		randomised_vector = pygame.math.Vector2(uniform(-0.2, 0.2), uniform(-0.2, 0.2))

		# If there are local boids, use them to adjust your heading vector
		if len(local_boids) != 0:
			alignment_vector = self.alignment(local_boids)
			cohesion_vector = self.cohesion(local_boids)
			separation_vector = self.separation(local_boids)

			# Combining vectors, with a small random factor as well
			steering_vector = alignment_vector*ALIGN_WEIGHT + cohesion_vector*COHESION_WEIGHT + separation_vector*SEPARATION_WEIGHT + randomised_vector

		# Else, just slightly randomise your heading vector
		else:
			steering_vector = boid_heading_vectors[self.boid_no] + randomised_vector

		# Smoothing out the steering vector, returns a vector of length VELOCITY
		steering_vector = self.smoothing(steering_vector)

		# Computing new position and checking the boid won't go over the boundary
		steering_vector = self.bounce_at_boundary(steering_vector)

		# Rotating boid to new heading
		self.rotate_boid(steering_vector)

		# Moving boid
		self.rect.x += steering_vector.x
		self.rect.y += steering_vector.y

		# Updating stored data
		boid_heading_vectors[self.boid_no] = steering_vector
		boid_locations[self.boid_no].x = self.rect.x
		boid_locations[self.boid_no].y = self.rect.y


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