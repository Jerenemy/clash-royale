import pygame
import random
import math
from game.settings import *

class Particle:
    def __init__(self, x, y, color, velocity, life, size, decay_rate=0.1, gravity=0):
        self.pos = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(velocity)
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.decay_rate = decay_rate
        self.gravity = gravity

    def update(self, dt):
        self.life -= dt
        self.velocity.y += self.gravity * dt
        self.pos += self.velocity * dt
        self.size = max(0, self.size - self.decay_rate * dt)

    def draw(self, surface):
        if self.life > 0 and self.size > 0:
            alpha = int((self.life / self.max_life) * 255)
            # Create a surface for alpha blending if needed, or just draw rect/circle
            # For performance with many particles, direct drawing is faster but no alpha
            # We'll stick to simple shapes for now.
            
            # Simulate fading by shrinking or just simple drawing
            rect = pygame.Rect(0, 0, self.size, self.size)
            rect.center = self.pos
            pygame.draw.rect(surface, self.color, rect)

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def update(self, dt):
        # Update all particles
        for p in self.particles:
            p.update(dt)
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.life > 0 and p.size > 0]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    def create_explosion(self, x, y, color, count=10):
        for _ in range(count):
            angle = random.uniform(0, 360)
            speed = random.uniform(50, 150)
            rad = math.radians(angle)
            vel_x = math.cos(rad) * speed
            vel_y = math.sin(rad) * speed
            
            life = random.uniform(0.3, 0.6)
            size = random.uniform(3, 6)
            
            p = Particle(x, y, color, (vel_x, vel_y), life, size, decay_rate=5)
            self.particles.append(p)

    def create_rubble(self, x, y):
        for _ in range(15):
            angle = random.uniform(0, 360)
            speed = random.uniform(30, 100)
            rad = math.radians(angle)
            vel_x = math.cos(rad) * speed
            vel_y = math.sin(rad) * speed
            
            life = random.uniform(0.5, 1.0)
            size = random.uniform(4, 8)
            color = (100, 100, 100) # Grey
            
            p = Particle(x, y, color, (vel_x, vel_y), life, size, decay_rate=2, gravity=200)
            self.particles.append(p)

    def create_spawn_poof(self, x, y):
        for _ in range(8):
            angle = random.uniform(0, 360)
            speed = random.uniform(20, 60)
            rad = math.radians(angle)
            vel_x = math.cos(rad) * speed
            vel_y = math.sin(rad) * speed
            
            life = random.uniform(0.2, 0.4)
            size = random.uniform(2, 5)
            color = (255, 255, 255) # White
            
            p = Particle(x, y, color, (vel_x, vel_y), life, size, decay_rate=5)
            self.particles.append(p)
            
    def create_projectile_trail(self, x, y, color):
        p = Particle(x, y, color, (0, 0), 0.2, 3, decay_rate=10)
        self.particles.append(p)

# Global instance
particle_system = ParticleSystem()
