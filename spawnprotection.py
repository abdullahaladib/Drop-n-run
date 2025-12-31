import time


class SpawnProtection:
   
    def __init__(self):
        """Initialize spawn protection system."""
        self.collision_count = 0  # Track total collisions (each collision = 1 life lost)
        self.max_collisions_before_protection = 3  # 3 collisions before protection activates
        self.is_protected = False # Current protection status
        self.protection_start_time = None
        self.protection_duration = 3.0  # 3 seconds of protection
        self.collided_mobs = set()  # Track mobs already hit in current frame
        
    def reset_collision_count(self):
        """Reset collision counter to 0."""
        self.collision_count = 0
        
    def handle_collision_detected(self, mob_id):
        # Check if player is protected - if so, phase through obstacle
        if self.is_protected:
            return True  
        
        # Check if we already counted this mob collision in this update
        if mob_id in self.collided_mobs:
            return False  
        

        self.collided_mobs.add(mob_id)
        self.collision_count += 1
        print(f"Life lost! Collisions: {self.collision_count}/{self.max_collisions_before_protection}")
        
        if self.collision_count >= self.max_collisions_before_protection:
            self.collision_count = 0 
            self.activate_protection()
            print(f"Protection activated for {self.protection_duration}s")
            return True  
        
        return False  
    
    def activate_protection(self):
        """Activate spawn protection for 3 seconds."""
        self.is_protected = True
        self.protection_start_time = time.time()
        
    def deactivate_protection(self):
        """Deactivate spawn protection."""
        self.is_protected = False
        self.protection_start_time = None
        
    def update(self):

        # Clear the collided mobs list for next frame
        self.collided_mobs.clear()
        
        if not self.is_protected:
            return False
        
        elapsed_time = time.time() - self.protection_start_time
        
        if elapsed_time >= self.protection_duration:
            self.deactivate_protection()
            return True  # Protection just ended
        
        return False  # Protection is still active
    
    def get_collision_count(self):

        return self.collision_count
    
    def get_remaining_protection_time(self):
        """
        Get remaining protection time in seconds.
        
        Returns:
            float: Remaining time in seconds (0 if not protected)
        """
        if not self.is_protected or self.protection_start_time is None:
            return 0.0
        
        elapsed_time = time.time() - self.protection_start_time
        remaining_time = max(0.0, self.protection_duration - elapsed_time)
        
        return remaining_time
    
    def can_take_damage(self):
        """
        Check if player can take damage from obstacles.
        
        Returns:
            bool: False if protected (cannot take damage), True if vulnerable
        """
        return not self.is_protected
    
    def can_phase_through_obstacles(self):
        return self.is_protected
    
    def is_player_protected(self):
        return self.is_protected
    
    def reset(self):
        self.collision_count = 0
        self.is_protected = False
        self.protection_start_time = None



