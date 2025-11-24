import pygame

class Scene:
    """
    Abstract base class for all game scenes.
    """
    def __init__(self, engine):
        self.engine = engine
        self.manager = engine.scene_manager

    def enter(self, params=None):
        """Called when entering the scene."""
        pass

    def exit(self):
        """Called when leaving the scene."""
        pass

    def handle_event(self, event):
        """Handle a single Pygame event."""
        pass

    def update(self, dt):
        """Update scene logic."""
        pass

    def draw(self, screen):
        """Render the scene."""
        pass

class SceneManager:
    """
    Manages the stack of scenes.
    """
    def __init__(self, engine):
        self.engine = engine
        self.stack = []

    def push(self, scene, params=None):
        """Push a new scene onto the stack."""
        if self.stack:
            self.stack[-1].exit()
        self.stack.append(scene)
        scene.enter(params)

    def pop(self):
        """Pop the current scene off the stack."""
        if self.stack:
            scene = self.stack.pop()
            scene.exit()
            if self.stack:
                self.stack[-1].enter()
            return scene
        return None

    def set(self, scene, params=None):
        """Replace the entire stack with a new scene."""
        while self.stack:
            self.stack.pop().exit()
        self.stack.append(scene)
        scene.enter(params)

    @property
    def current(self):
        """Get the current active scene."""
        return self.stack[-1] if self.stack else None

    def handle_event(self, event):
        if self.current:
            self.current.handle_event(event)

    def update(self, dt):
        if self.current:
            self.current.update(dt)

    def draw(self, screen):
        if self.current:
            self.current.draw(screen)
