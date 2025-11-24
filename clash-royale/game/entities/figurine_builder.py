import pygame
import math

class FigurineBuilder:
    """
    Helper class to construct 3D-like figurines for top-down/isometric view.
    Handles drawing primitives with perspective adjustments.
    """
    def __init__(self, surface, center_x, center_y, size, facing_angle=0, pitch=45):
        self.surface = surface
        self.center_x = center_x
        self.center_y = center_y
        self.size = size
        self.facing_angle = facing_angle # 0=Right, 90=Down, 180=Left, 270=Up
        self.pitch = pitch # Camera pitch (0=Side view, 90=Top-down)
        
        # Calculate perspective scale (Y-axis compression)
        # For 45 degrees, y is compressed by sin(45) ~= 0.7
        self.y_scale = math.sin(math.radians(pitch))
        
        # Bounds tracking (relative to center)
        self.min_x = 0
        self.max_x = 0
        self.min_y = 0
        self.max_y = 0
        
    def _transform(self, x, y, z):
        """
        Transform local coordinates to world coordinates based on facing angle.
        Local X: Right relative to unit
        Local Y: Forward relative to unit (or Backward? Standard is Y down/forward)
                 Let's say Local Y is Forward (direction of movement).
                 If Angle=0 (Right), Local Y(1) -> World X(1)?
                 No, Angle=0 usually means facing Right (Positive X).
                 So Local Y (Forward) -> World X.
                 Local X (Right) -> World Y (Down/Right)?
                 
                 Let's stick to standard math:
                 Angle 0 = Facing Positive X.
                 Local Forward (x=1, y=0) -> World (1, 0)
                 Local Right (x=0, y=1) -> World (0, 1)
                 
                 Wait, usually:
                 X is Right, Y is Down.
                 Angle 0 = Right.
                 So Forward vector is (1, 0).
                 Right vector is (0, 1) (Down).
                 
                 So:
                 World X = Local Forward * cos(a) - Local Right * sin(a)
                 World Y = Local Forward * sin(a) + Local Right * cos(a)
                 
                 Let's define inputs as (right, forward, up).
                 x: Right (relative)
                 y: Forward (relative)
                 z: Up (relative)
        """
        # Convert angle to radians
        rad = math.radians(self.facing_angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        
        # Rotate (x, y) in 2D plane
        # We want x to be "Right" and y to be "Forward" relative to unit?
        # Or x, y, z as standard 3D coords?
        # Let's use x=Right, y=Forward, z=Up for LOCAL inputs.
        
        # If facing 0 (Right):
        # Forward (y=1) -> World X=1, World Y=0
        # Right (x=1) -> World X=0, World Y=1 (Down)
        
        # World X = y * cos(a) + x * sin(a) ?
        # If a=0: World X = y. Correct.
        # World Y = y * sin(a) - x * cos(a) ?
        # If a=0: World Y = -x. (Right is Up in world Y?)
        # Screen Y is Down.
        
        # Let's simplify.
        # Local X is Right. Local Y is Forward.
        # World X is Right. World Y is Down.
        
        # Rotation matrix for 2D:
        # x' = x cos - y sin
        # y' = x sin + y cos
        
        # If we rotate by `facing_angle`:
        # We are rotating the MODEL.
        # If facing_angle = 0, model is aligned with world.
        # So Local X = World X, Local Y = World Y.
        # This means Local Y is DOWN, not Forward.
        
        # Let's assume inputs are (x, y, z) where:
        # x: Right relative to unit
        # y: Forward relative to unit (depth)
        # z: Up
        
        # If Angle=0 (Right):
        # Forward (y) should map to World X.
        # Right (x) should map to World Y.
        
        # World X = y * cos(a) - x * sin(a)
        # World Y = y * sin(a) + x * cos(a)
        
        # Let's test:
        # a=0: WX = y, WY = x. (Forward->Right, Right->Down). Correct.
        # a=90 (Down): WX = -x, WY = y. (Forward->Down, Right->Left). Correct.
        
        wx = y * cos_a - x * sin_a
        wy = y * sin_a + x * cos_a
        wz = z
        
        return wx, wy, wz

    def _project(self, x, y, z):
        """
        Project 3D coordinates to 2D screen coordinates.
        """
        # Transform first
        wx, wy, wz = self._transform(x, y, z)
        
        # Screen X = center + wx
        # Screen Y = center + wy * scale - wz
        # Calculate relative to center first
        rel_x = wx
        rel_y = wy * self.y_scale - wz
        
        # Update bounds
        self.min_x = min(self.min_x, rel_x)
        self.max_x = max(self.max_x, rel_x)
        self.min_y = min(self.min_y, rel_y)
        self.max_y = max(self.max_y, rel_y)
        
        screen_x = self.center_x + rel_x
        screen_y = self.center_y + rel_y
        return int(screen_x), int(screen_y)

    def draw_body(self, color, width, height, depth=10, offset_x=0, offset_y=0, offset_z=0):
        """Draws a body (cylinder/oval approximation)"""
        # Calculate screen position
        sx, sy = self._project(offset_x, offset_y, offset_z)
        
        # Expand bounds by radius/size
        # Approximate radius as max dimension / 2
        radius = max(width, height, depth) / 2
        # We need to expand the bounds that were just updated by _project (which was the center)
        self.min_x -= radius
        self.max_x += radius
        self.min_y -= radius
        self.max_y += radius
        
        if self.surface:
            # Draw depth (darker color)
            dark_color = tuple(max(0, c - 40) for c in color[:3]) + (color[3] if len(color) > 3 else 255,)
            
            # If we are looking from top-down, depth is mostly below
            # Draw a cylinder-like shape
            rect_depth = pygame.Rect(sx - width//2, sy - height//2, width, height)
            # We can just draw a rounded rect for the "side"
            pygame.draw.rect(self.surface, dark_color, rect_depth, border_radius=int(width/2))
            
            # Draw top (main color) - offset up slightly for "3D" pop?
            # Actually, let's keep it simple for now.
            # Just draw the main shape.
            pygame.draw.rect(self.surface, color, rect_depth, border_radius=int(width/2))
        
    def draw_head(self, color, radius, offset_x=0, offset_y=0, offset_z=0):
        """Draws a head (sphere/circle)"""
        sx, sy = self._project(offset_x, offset_y, offset_z)
        
        # Expand bounds
        self.min_x -= radius
        self.max_x += radius
        self.min_y -= radius
        self.max_y += radius
        
        if self.surface:
            pygame.draw.circle(self.surface, color, (sx, sy), radius)
        
    def draw_limb(self, color, start_pos, end_pos, width=3):
        """Draws a limb (line)"""
        sx1, sy1 = self._project(*start_pos)
        sx2, sy2 = self._project(*end_pos)
        
        # Expand bounds
        half_width = width / 2
        self.min_x -= half_width
        self.max_x += half_width
        self.min_y -= half_width
        self.max_y += half_width
        
        if self.surface:
            pygame.draw.line(self.surface, color, (sx1, sy1), (sx2, sy2), width)
        
    def draw_rect(self, color, width, height, offset_x=0, offset_y=0, offset_z=0, border_radius=0):
        sx, sy = self._project(offset_x, offset_y, offset_z)
        
        # Expand bounds
        self.min_x -= width/2
        self.max_x += width/2
        self.min_y -= height/2
        self.max_y += height/2
        
        if self.surface:
            rect = pygame.Rect(sx - width//2, sy - height//2, width, height)
            pygame.draw.rect(self.surface, color, rect, border_radius=border_radius)
        
    def draw_ellipse(self, color, width, height, offset_x=0, offset_y=0, offset_z=0):
        sx, sy = self._project(offset_x, offset_y, offset_z)
        
        # Expand bounds
        self.min_x -= width/2
        self.max_x += width/2
        self.min_y -= height/2
        self.max_y += height/2
        
        if self.surface:
            rect = pygame.Rect(sx - width//2, sy - height//2, width, height)
            pygame.draw.ellipse(self.surface, color, rect)
        
    def draw_polygon(self, color, points):
        """Points are (x, y, z) tuples"""
        projected_points = [self._project(*p) for p in points]
        if self.surface:
            pygame.draw.polygon(self.surface, color, projected_points)

    def draw_box(self, color, width, depth, height, offset_x=0, offset_y=0, offset_z=0):
        """Draws a 3D box (rectangular prism)"""
        half_w = width / 2
        half_d = depth / 2
        
        # Define the 4 corners of the base relative to center (x, y)
        # 0: Back-Left (-x, -y)
        # 1: Back-Right (+x, -y)
        # 2: Front-Right (+x, +y)
        # 3: Front-Left (-x, +y)
        corners_local = [
            (-half_w, -half_d),
            (half_w, -half_d),
            (half_w, half_d),
            (-half_w, half_d)
        ]
        
        # Project Top Face vertices (z = offset_z + height)
        top_points = []
        for cx, cy in corners_local:
            px, py = self._project(offset_x + cx, offset_y + cy, offset_z + height)
            top_points.append((px, py))
            
        # Project Bottom Face vertices (z = offset_z)
        bottom_points = []
        for cx, cy in corners_local:
            px, py = self._project(offset_x + cx, offset_y + cy, offset_z)
            bottom_points.append((px, py))
            
        if self.surface:
            # Colors for shading
            # Top: Main color
            # Side 1 (Front/Back): Darker
            # Side 2 (Left/Right): Darkest
            
            # Ensure alpha is preserved
            alpha = color[3] if len(color) > 3 else 255
            c_top = color
            c_side_1 = tuple(max(0, c - 30) for c in color[:3]) + (alpha,)
            c_side_2 = tuple(max(0, c - 60) for c in color[:3]) + (alpha,)
            
            # Draw Sides
            # We draw all 4 sides. The order matters for correct occlusion if we don't use Z-buffer.
            # However, since we draw the Top Face last, it covers the inside.
            # And for a convex box, drawing back faces then front faces works.
            # But determining which is back/front depends on rotation.
            
            # Simple Painter's Algorithm for Box:
            # 1. Draw all vertical faces.
            # 2. Draw top face.
            # This works because the top face always covers the "hole" of the box.
            # The only issue is vertical faces overlapping each other.
            # Ideally we draw "back" faces first.
            
            # Let's try drawing them in a fixed order and see if it works for standard views.
            # Or better: calculate the center Z of each face and sort?
            # But we are in 2D projection.
            
            # Let's just draw them.
            # Side 0: Back (y-d/2) - Connects 0 and 1
            # Side 1: Right (x+w/2) - Connects 1 and 2
            # Side 2: Front (y+d/2) - Connects 2 and 3
            # Side 3: Left (x-w/2) - Connects 3 and 0
            
            sides = []
            for i in range(4):
                j = (i + 1) % 4
                poly = [top_points[i], top_points[j], bottom_points[j], bottom_points[i]]
                
                # Shading: Alternate
                shade = c_side_1 if i % 2 == 0 else c_side_2
                sides.append((shade, poly))
                
            # Draw sides
            for shade, poly in sides:
                pygame.draw.polygon(self.surface, shade, poly)
                
            # Draw Top Face
            pygame.draw.polygon(self.surface, c_top, top_points)
            
            # Optional: Draw edges for definition
            # pygame.draw.lines(self.surface, c_side_2, True, top_points, 1)

    def get_hand_pos(self, side="right", offset_x=0, offset_y=0, offset_z=0):
        """
        Get the 3D position of a hand based on facing angle.
        side: "right" or "left"
        """
        # Base offset for hand from center
        shoulder_width = 8
        angle_rad = math.radians(self.facing_angle)
        
        # If facing right (0 deg):
        # Right hand is "down" in Y (positive Y) or "back" in Z?
        # In top-down 2D logic:
        # Right (0 deg): Right hand is at (0, 8) relative to center?
        
        # Let's use standard math:
        # x = cos(angle), y = sin(angle)
        
        # Right hand is +90 degrees from facing vector
        # Left hand is -90 degrees
        
        hand_angle = angle_rad + (math.pi/2 if side == "right" else -math.pi/2)
        
        hx = math.cos(hand_angle) * shoulder_width + offset_x
        hy = math.sin(hand_angle) * shoulder_width + offset_y
        hz = offset_z # Shoulder height?
        
        return (hx, hy, hz)
