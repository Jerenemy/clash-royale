import math
from game.settings import SCREEN_WIDTH, SCREEN_HEIGHT

class SymmetryUtils:
    """
    Centralized logic for handling game symmetry and coordinate mirroring.
    """
    
    @staticmethod
    def flip_x(x):
        """Flip X coordinate across the center vertical axis."""
        return SCREEN_WIDTH - x
        
    @staticmethod
    def flip_y(y):
        """Flip Y coordinate across the center horizontal axis of the GRID."""
        # Calculate grid center Y
        # Grid starts at GRID_MARGIN_Y
        # Height is GRID_HEIGHT * TILE_SIZE
        from game.settings import GRID_MARGIN_Y, GRID_HEIGHT, TILE_SIZE
        grid_center_y = GRID_MARGIN_Y + (GRID_HEIGHT * TILE_SIZE) / 2.0
        
        # Mirror around grid_center_y
        # y' = center + (center - y) = 2*center - y
        return (2 * grid_center_y) - y
        
    @staticmethod
    def flip_pos(pos):
        """Flip (x, y) position for the opponent's perspective."""
        return (SymmetryUtils.flip_x(pos[0]), SymmetryUtils.flip_y(pos[1]))
        
    @staticmethod
    def get_mirrored_angle(angle):
        """
        Get the mirrored angle for the opponent.
        Rotates by 180 degrees (PI radians).
        """
        return angle + math.pi
        
    @staticmethod
    def transform_formation_angle(base_angle, side):
        """
        Transform a formation angle based on the side.
        If side is 'enemy', rotates the formation by 180 degrees.
        """
        if side == "enemy":
            return SymmetryUtils.get_mirrored_angle(base_angle)
        return base_angle
