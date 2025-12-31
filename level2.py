from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import sys
import os
import shapes
from spawnprotection import SpawnProtection

# Initialize spawn protection system
protection = SpawnProtection()

# Game state
GAME_STATE = "MENU"  # Can be "MENU", "PLAYING", or "GAME_OVER"

SCORE_FILE = "game_score.txt"
GUN_FILE = "gun_level.txt"

def save_score(score):
    """Save score to file"""
    try:
        with open(SCORE_FILE, 'w') as f:
            f.write(str(score))
        print(f"Score saved: {score}")  # Debug message
    except Exception as e:
        print(f"Error saving score: {e}")

def load_score():
    """Load score from file"""
    try:
        if os.path.exists(SCORE_FILE):
            with open(SCORE_FILE, 'r') as f:
                return int(f.read().strip())
    except Exception as e:
        print(f"Error loading score: {e}")
    return 0

def load_gun_level():
    """Load gun level from file"""
    try:
        if os.path.exists(GUN_FILE):
            with open(GUN_FILE, 'r') as f:
                return int(f.read().strip())
    except Exception as e:
        print(f"Error loading gun level: {e}")
    return 1

PLAYER_SCORE = load_score()
GUN_LEVEL = load_gun_level()
BULLET_DAMAGE = GUN_LEVEL
PLAYER_HP = 3
DAMAGE = 1
MOB_HP = 5
PLAYER_SKIN_COLOR = (0,1,1)

camera_pos = (0,700,400)
player1_x = 0
player1_z = 0
player1_y = 575  # start at center of pitch
mobs = [{'x': 0, 'y': -600, 'z': 30, 'delay': 0, 'colliding': False, 'hp': 5, 'shoot_timer': 180, 'bullet_count': 0, 'is_shooting': False},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 30, 'colliding': False, 'hp': 5, 'shoot_timer': 210, 'bullet_count': 0, 'is_shooting': False},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 60, 'colliding': False, 'hp': 5, 'shoot_timer': 240, 'bullet_count': 0, 'is_shooting': False},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 90, 'colliding': False, 'hp': 5, 'shoot_timer': 270, 'bullet_count': 0, 'is_shooting': False},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 120, 'colliding': False, 'hp': 5, 'shoot_timer': 300, 'bullet_count': 0, 'is_shooting': False}]
bullets = []  # List to store player bullets
enemy_bullets = []  # List to store enemy bullets
PITCH_HALF = 600
# The player model is scaled by 150. The body is a cube scaled by (0.4, 0.6, 0.2).
# This means the visual radius is different for X and Y axes.
# Y-radius = (0.6 * 150) / 2 = 45
# X-radius = (0.4 * 150) / 2 = 30
PLAYER_RADIUS_Y = 45
PLAYER_RADIUS_X = 30

is_jumping = False
jump_velocity = 0
is_crouching = False
ground_level = 0
spawn_protection_time = 0  # Timer for spawn protection blinking (in frames)

def keyboard(key, x, y):
    global player1_x, player1_y, player1_z, is_jumping, jump_velocity, is_crouching, GAME_STATE, PLAYER_HP, PLAYER_SCORE, spawn_protection_time
    key = key.decode("utf-8").lower()

    # Handle ESC key to return to menu from playing
    if key == '\x1b' and GAME_STATE == "PLAYING":
        GAME_STATE = "MENU"
        save_score(PLAYER_SCORE)
        print("Returned to menu!")
        return

    # Handle 'm' key to return to menu from game over
    if key == 'm' and GAME_STATE == "GAME_OVER":
        # Reset game (but keep PLAYER_SCORE as persistent currency)
        PLAYER_HP = 3
        spawn_protection_time = 0
        # Reset player position
        player1_x = 0
        player1_y = 575
        player1_z = 0
        # Clear bullets
        bullets.clear()
        enemy_bullets.clear()
        # Reset mobs
        for mob in mobs:
            mob['x'] = 0
            mob['y'] = -600
            mob['z'] = 20
            mob['delay'] = random.randrange(0, 121)
            mob['colliding'] = False
            mob['hp'] = 5
            mob['shoot_timer'] = random.randrange(120, 240)
            mob['bullet_count'] = 0
            mob['is_shooting'] = False
        save_score(PLAYER_SCORE)  # Save score before returning to menu
        GAME_STATE = "MENU"
        print("Returning to menu!")
        return

    # Only process game controls if playing
    if GAME_STATE != "PLAYING":
        return

    step = 10

    if key == 'w':
        player1_y -= step
    elif key == 's':
        player1_y += step
    elif key == 'a':
        player1_x += step
    elif key == 'd':
        player1_x -= step
    elif key == ' ' and not is_jumping and is_crouching == False:
        is_jumping = True
        jump_velocity = 25
    elif key == 'c':
        is_crouching = not is_crouching
    elif key == 'f':
        shoot()
    
    # Clamp using calculated constants with larger margin
    max_x = PITCH_HALF - PLAYER_RADIUS_X - 50
    min_x = -PITCH_HALF + PLAYER_RADIUS_X + 50
    max_y = PITCH_HALF - PLAYER_RADIUS_Y - 20
    min_y = -PITCH_HALF + PLAYER_RADIUS_Y + 20
    
    if player1_x > max_x:
        player1_x = max_x
    if player1_x < min_x:
        player1_x = min_x
    if player1_y > max_y:
        player1_y = max_y
    if player1_y < min_y:
        player1_y = min_y


def shoot():
    """Fire a bullet from the player's position towards the wall"""
    if GAME_STATE == "PLAYING":
        # Create bullet at player's gun position (above player, forward direction)
        bullet = {
            'x': player1_x,
            'y': player1_y - 50,  # Gun position is forward from player
            'z': player1_z + 60,  # Gun height
            'vy': -15  # Bullet velocity towards the wall (negative y direction)
        }
        bullets.append(bullet)
        print("Bullet fired!")

def enemy_shoot(mob):
    """Enemy fires 1 bullet towards the player"""
    bullet = {
        'x': mob['x'],
        'y': mob['y'],
        'z': mob['z'],
        'vy': 20  # Faster bullet velocity towards the player (positive y direction)
    }
    enemy_bullets.append(bullet)

def update_bullets():
    """Update bullet positions and check collisions"""
    global bullets, mobs, PLAYER_SCORE
    bullets_to_remove = []
    
    for i, bullet in enumerate(bullets):
        # Move bullet
        bullet['y'] += bullet['vy']
        
        # Remove bullet if it goes beyond the wall
        if bullet['y'] < -650:
            bullets_to_remove.append(i)
            continue
        
        # Check collision with mobs
        bullet_radius = 7.5  # Bullet is scaled 15x15x15, so radius is 7.5
        for mob_idx, mob in enumerate(mobs):
            # Mob collision box (cube of size 100)
            mob_x_min = mob['x'] - 50
            mob_x_max = mob['x'] + 50
            mob_y_min = mob['y'] - 50
            mob_y_max = mob['y'] + 50
            mob_z_min = mob['z'] - 50
            mob_z_max = mob['z'] + 50
            
            # Check if bullet collides with mob (accounting for bullet size)
            # Use a larger z-range for bullet to hit obstacles at different heights
            bullet_x_min = bullet['x'] - bullet_radius
            bullet_x_max = bullet['x'] + bullet_radius
            bullet_y_min = bullet['y'] - bullet_radius
            bullet_y_max = bullet['y'] + bullet_radius
            bullet_z_min = bullet['z'] - 75  # Expanded z range to hit obstacles at z=0 and z=145
            bullet_z_max = bullet['z'] + 75
            
            if (mob_x_min < bullet_x_max and mob_x_max > bullet_x_min and
                mob_y_min < bullet_y_max and mob_y_max > bullet_y_min and
                mob_z_min < bullet_z_max and mob_z_max > bullet_z_min):
                # Hit detected
                mob['hp'] -= BULLET_DAMAGE
                bullets_to_remove.append(i)
                
                if mob['hp'] <= 0:
                    # Respawn enemy at random location
                    mob['x'] = random.randrange(-580, 580)
                    mob['y'] = -600
                    mob['z'] = random.choice([0, 145])
                    mob['hp'] = 5
                    mob['colliding'] = False
                    mob['delay'] = 0
                    mob['shoot_timer'] = random.randrange(120, 240)
                    mob['bullet_count'] = 0
                    mob['is_shooting'] = False
                    PLAYER_SCORE += 10
                    save_score(PLAYER_SCORE)
                    print(f"Obstacle destroyed! Score: {PLAYER_SCORE}")
                break
    
    # Remove bullets in reverse order to maintain indices
    for i in sorted(bullets_to_remove, reverse=True):
        if i < len(bullets):
            bullets.pop(i)

def update_enemy_bullets():
    """Update enemy bullet positions and check collisions with player"""
    global enemy_bullets, PLAYER_HP, player1_x, player1_y, player1_z, spawn_protection_time
    bullets_to_remove = []
    
    for i, bullet in enumerate(enemy_bullets):
        # Move bullet towards player
        bullet['y'] += bullet['vy']
        
        # Remove bullet if it goes beyond the player
        if bullet['y'] > 650:
            bullets_to_remove.append(i)
            continue
        
        # Only check collision if not in spawn protection
        if spawn_protection_time <= 0:
            # Player collision box
            player_x_min = player1_x - PLAYER_RADIUS_X
            player_x_max = player1_x + PLAYER_RADIUS_X
            player_y_min = player1_y - PLAYER_RADIUS_Y
            player_y_max = player1_y + PLAYER_RADIUS_Y
            player_z_min = player1_z
            if is_crouching:
                player_z_max = player1_z + 70
            else:
                player_z_max = player1_z + 100
            
            # Bullet collision box
            bullet_radius = 7.5
            bullet_x_min = bullet['x'] - bullet_radius
            bullet_x_max = bullet['x'] + bullet_radius
            bullet_y_min = bullet['y'] - bullet_radius
            bullet_y_max = bullet['y'] + bullet_radius
            bullet_z_min = bullet['z'] - 75
            bullet_z_max = bullet['z'] + 75
            
            # Check collision
            if (player_x_min < bullet_x_max and player_x_max > bullet_x_min and
                player_y_min < bullet_y_max and player_y_max > bullet_y_min and
                player_z_min < bullet_z_max and player_z_max > bullet_z_min):
                # Player hit by enemy bullet
                PLAYER_HP -= 1
                # Respawn player at initial position
                player1_x = 0
                player1_y = 575
                player1_z = 0
                spawn_protection_time = 180  # 3 seconds at 60 FPS
                bullets_to_remove.append(i)
                print(f"Hit by enemy bullet! HP: {PLAYER_HP}")
    
    # Remove bullets in reverse order to maintain indices
    for i in sorted(bullets_to_remove, reverse=True):
        if i < len(enemy_bullets):
            enemy_bullets.pop(i)

def draw_bullets():
    """Draw all active player bullets"""
    for bullet in bullets:
        glPushMatrix()
        glTranslatef(bullet['x'], bullet['y'], bullet['z'])
        glColor3f(1, 0, 0)  # Red bullets
        glScalef(15, 15, 15)  # Larger cube for bullet
        glutSolidCube(1)
        glPopMatrix()

def draw_enemy_bullets():
    """Draw all active enemy bullets"""
    for bullet in enemy_bullets:
        glPushMatrix()
        glTranslatef(bullet['x'], bullet['y'], bullet['z'])
        glColor3f(0, 0, 0)  # Black bullets for enemies
        glScalef(15, 15, 15)
        glutSolidCube(1)
        glPopMatrix()

def update_player():
    global player1_z, player1_x, player1_y, is_jumping, jump_velocity
    if is_jumping:
        player1_z += jump_velocity
        jump_velocity -= 1 # Gravity
        if player1_z < ground_level:
            player1_z = ground_level
            is_jumping = False
            jump_velocity = 0
    
    # Clamp using calculated constants with larger margin
    max_x = PITCH_HALF - PLAYER_RADIUS_X - 50
    min_x = -PITCH_HALF + PLAYER_RADIUS_X + 50
    max_y = PITCH_HALF - PLAYER_RADIUS_Y - 50
    min_y = -PITCH_HALF + PLAYER_RADIUS_Y + 50
    
    if player1_x > max_x:
        player1_x = max_x
    if player1_x < min_x:
        player1_x = min_x
    if player1_y > max_y:
        player1_y = max_y
    if player1_y < min_y:
        player1_y = min_y

def draw_player():
  # Skip drawing during blink off phase of spawn protection
  if spawn_protection_time > 0:
    # Blink effect: alternate visibility every 10 frames
    if (spawn_protection_time // 10) % 2 == 0:
      return
  
  glPushMatrix()
  glTranslatef(player1_x, player1_y, player1_z)
  glRotatef(90, 1, 0, 0)
  if is_crouching:
      glScalef(150, 150 * 0.7, 150)
  else:
      glScalef(150, 150, 150)

  glColor3f(0, 0, 1)
  for i in [-0.2, 0.2]:
    glPushMatrix()
    glTranslatef(i, 0.4, 0)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 0.1, 0.05, 0.4, 10, 10)
    glPopMatrix()
  
  r,g,b = PLAYER_SKIN_COLOR
  glColor3f(r,g,b)
  glPushMatrix()
  glTranslatef(0, 1, 0)
  glScalef(0.4, 0.6, 0.2)
  glutSolidCube(1)
  glPopMatrix()

  glColor3f(0.96, 0.8, 0.69)
  for o in [-0.15, 0.15]:
    glPushMatrix()
    glTranslatef(o, 1.2, 0.1)
    gluCylinder(gluNewQuadric(), 0.1, 0.05, 0.4, 10, 10)
    glPopMatrix()

  glColor3f(0.5, 0.5, 0.5)
  glPushMatrix()
  glTranslatef(0, 1.2, 0.1)
  gluCylinder(gluNewQuadric(), 0.08, 0, 0.8, 10, 10)
  glPopMatrix()

  glColor3f(0, 0, 0)
  glPushMatrix()
  glTranslatef(0, 1.65, 0)
  gluSphere(gluNewQuadric(), 0.2, 10, 10)
  glPopMatrix()

  glPopMatrix()

def draw_enemy():
  for mob in mobs:
    glPushMatrix()
    glColor3f(1,0,0)
    glTranslatef(mob['x'],mob['y'],mob['z'])
    glutSolidCube(100)
    glPopMatrix()

def setup_camera():
  glMatrixMode(GL_PROJECTION)
  glLoadIdentity()
  gluPerspective(120, 1.25, 0.1, 1500)
  glMatrixMode(GL_MODELVIEW)
  cam_x = player1_x
  cam_y = 700
  cam_z = 400
  gluLookAt(cam_x, cam_y, cam_z,
            player1_x, 0, 0,
            0,0,1)

def check_collision():
  global player1_x, player1_y, player1_z, spawn_protection_time, PLAYER_HP
  
  # Player collision box
  player_x_min = player1_x - PLAYER_RADIUS_X
  player_x_max = player1_x + PLAYER_RADIUS_X
  player_y_min = player1_y - PLAYER_RADIUS_Y
  player_y_max = player1_y + PLAYER_RADIUS_Y
  player_z_min = player1_z
  # Reduce height when crouching
  if is_crouching:
    player_z_max = player1_z + 70
  else:
    player_z_max = player1_z + 100
  
  # Only check collisions if not in spawn protection
  if spawn_protection_time > 0:
    return
  
  # Check collision with all enemies
  for idx, mob in enumerate(mobs):
    # Enemy collision box (cube of size 100)
    enemy_x_min = mob['x'] - 50
    enemy_x_max = mob['x'] + 50
    enemy_y_min = mob['y'] - 50
    enemy_y_max = mob['y'] + 50
    enemy_z_min = mob['z'] - 50
    enemy_z_max = mob['z'] + 50
    
    # Check if currently colliding
    is_currently_colliding = (player_x_min < enemy_x_max and player_x_max > enemy_x_min and
                              player_y_min < enemy_y_max and player_y_max > enemy_y_min and
                              player_z_min < enemy_z_max and player_z_max > enemy_z_min)
    
    if is_currently_colliding:
      # Only register collision if this enemy wasn't already colliding
      if not mob['colliding']:
        # Decrement HP
        PLAYER_HP -= 1
        # Respawn player at initial position
        player1_x = 0
        player1_y = 575
        player1_z = 0
        spawn_protection_time = 180  # 3 seconds at 60 FPS
        mob['colliding'] = True
      # Keep colliding state true while touching
      mob['colliding'] = True
    else:
      # No longer colliding, reset the flag for next collision
      mob['colliding'] = False

def spawn_mobs():
  for mob in mobs:
    if mob['delay'] > 0:
      mob['delay'] -= 1
      continue
    
    # Only move if not shooting
    if not mob['is_shooting']:
      if mob['y'] != 575:
        mob['y'] += 10
      if mob['y'] >= 575:
        mob['y'] = -600
        mob['x'] = random.randrange(-580,580)
        mob['z'] = random.choice([0,145])
        mob['delay'] = random.randrange(60, 120)
    
    # Enemy shooting logic - fire 3 bullets one after another, then wait 2 seconds
    mob['shoot_timer'] -= 1
    
    # Only shoot if enemy is visible on screen (between wall and player)
    if mob['y'] > -550 and mob['y'] < 550:
      if mob['shoot_timer'] <= 0:
        # Start shooting
        mob['is_shooting'] = True
        # Fire a bullet
        enemy_shoot(mob)
        mob['bullet_count'] += 1
        
        if mob['bullet_count'] < 3:
          # Fire next bullet after 15 frames (0.25 seconds)
          mob['shoot_timer'] = 15
        else:
          # All 3 bullets fired, wait 2 seconds before next burst
          mob['shoot_timer'] = 120  # 2 seconds at 60 FPS
          mob['bullet_count'] = 0
          mob['is_shooting'] = False
    else:
      # Reset shooting state if enemy goes off screen
      mob['is_shooting'] = False

def idle():
    global spawn_protection_time, GAME_STATE
    protection.update()  # Update protection timer
    if GAME_STATE == "PLAYING":
        spawn_mobs()
        check_collision()
        update_player()
        update_bullets()  # Update player bullet positions and collisions
        update_enemy_bullets()  # Update enemy bullet positions and collisions
        # Decrement spawn protection timer
        if spawn_protection_time > 0:
            spawn_protection_time -= 1
        # Check if player is dead
        if PLAYER_HP <= 0:
            GAME_STATE = "GAME_OVER"
    glutPostRedisplay()

def game():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    setup_camera()
    
    # Custom neon black and red background for Level 2
    # Draw red-tinted pitch
    glBegin(GL_QUADS)
    glColor3f(0.3, 0, 0)  # Dark red pitch instead of white
    glVertex3f(600, 600, 0)
    glVertex3f(-600, 600, 0)
    glVertex3f(-600, -600, 0)
    glVertex3f(600, -600, 0)
    glEnd()
    
    # Draw red wall
    glBegin(GL_QUADS)
    glColor3f(0.5, 0, 0)  # Dark red wall
    glVertex3f(-10000,-600, 0)
    glVertex3f(10000,-600, 0)
    glVertex3f(10000,-600, 10000)
    glVertex3f(-10000,-600, 10000)
    glEnd()
    
    glLineWidth(40)
    glBegin(GL_LINES)
    glColor3f(1, 0, 0)  # Neon red line
    glVertex3f(-10000,-600, 0)
    glVertex3f(10000,-600,0)
    glEnd()
    
    # Draw dark red/black side backgrounds
    glBegin(GL_QUADS)
    glColor3f(0.05, 0, 0)  # Very dark red/black
    glVertex3f(-10000,600, 0)
    glVertex3f(-600,600, 0)
    glVertex3f(-600,-600, 0)
    glVertex3f(-10000,-600, 0)
    glEnd()

    glBegin(GL_QUADS)
    glColor3f(0.05, 0, 0)  # Very dark red/black
    glVertex3f(10000,600, 0)
    glVertex3f(600,600, 0)
    glVertex3f(600,-600, 0)
    glVertex3f(10000,-600, 0)
    glEnd()
    
    glLineWidth(40)
    glBegin(GL_LINES)
    glColor3f(1, 0, 0)  # Neon red lines
    glVertex3f(-600,-600, 0)
    glVertex3f(-600,600,0)
    glEnd()

    glBegin(GL_LINES)
    glColor3f(1, 0, 0)  # Neon red lines
    glVertex3f(600,-600, 0)
    glVertex3f(600,600,0)
    glEnd()
    
    draw_bullets()  # Draw player bullets
    draw_enemy_bullets()  # Draw enemy bullets
    draw_player()
    draw_enemy()
    
    # Draw HP on screen
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1000, 800, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glColor3f(1, 0, 0)  # Red color for HP
    glRasterPos2f(20, 30)
    hp_text = f"HP: {PLAYER_HP}"
    for char in hp_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw score in top-right
    glColor3f(1, 1, 0)  # Yellow color for score
    glRasterPos2f(850, 30)
    score_text = f"SCORE: {PLAYER_SCORE}"
    for char in score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    glEnable(GL_DEPTH_TEST)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def draw_text_2d(text, x, y, font=GLUT_BITMAP_HELVETICA_18):
    """Draw 2D text at screen coordinates"""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1000, 800, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))
    glEnable(GL_DEPTH_TEST)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_menu():
    """Draw the main menu screen"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    # Setup 2D projection
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1000, 800, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw background - neon black and red theme
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)
    glColor3f(0.1, 0, 0)  # Dark red at top
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glColor3f(0.05, 0, 0)  # Almost black at bottom
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
    # Draw score in top-right
    glColor3f(1, 1, 0)
    glRasterPos2f(850, 30)
    score_text = f"SCORE: {PLAYER_SCORE}"
    for char in score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw gun level
    glColor3f(0, 1, 0)
    glRasterPos2f(20, 60)
    gun_text = f"GUN LEVEL: {GUN_LEVEL}"
    for char in gun_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw title
    glColor3f(1, 0.1, 0.1)  # Neon red
    glRasterPos2f(300, 200)
    title = "DROP 'N' RUN - LEVEL 2"
    for char in title:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw PLAY button (text that can be clicked)
    glColor3f(1, 0, 0)  # Red
    glRasterPos2f(450, 350)
    play_text = "PLAY"
    for char in play_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw BACK TO MENU button
    glColor3f(1, 0.3, 0.3)  # Light neon red
    glRasterPos2f(400, 450)
    back_text = "BACK TO MENU"
    for char in back_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def draw_game_over():
    """Draw the game over screen"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    # Setup 2D projection
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1000, 800, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw background - neon black and red theme
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)
    glColor3f(0.1, 0, 0)  # Dark red at top
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glColor3f(0.05, 0, 0)  # Almost black at bottom
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
    # Draw GAME OVER text
    glColor3f(1, 0.1, 0.1)  # Brighter neon red
    glRasterPos2f(350, 300)
    game_over_text = "GAME OVER"
    for char in game_over_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw final score
    glColor3f(1, 1, 0)
    glRasterPos2f(350, 400)
    score_text = f"FINAL SCORE: {PLAYER_SCORE}"
    for char in score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw return to menu instruction
    glColor3f(1, 1, 1)
    glRasterPos2f(300, 500)
    instruction_text = "Press 'm' to return to menu"
    for char in instruction_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def mouse(button, state, x, y):
    """Handle mouse clicks"""
    global GAME_STATE
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Check if click is within PLAY button area (approximate) - only works in MENU
        if 430 < x < 530 and 335 < y < 365 and GAME_STATE == "MENU":
            GAME_STATE = "PLAYING"
            print("Level 2 started!")
        
        # Check if click is within BACK TO MENU button area
        elif 400 < x < 600 and 435 < y < 465 and GAME_STATE == "MENU":
            print("Returning to main menu...")
            save_score(PLAYER_SCORE)  # Save score before exiting
            # Force exit to return to dropnrun.py
            os._exit(0)

def showScreen():
    global GAME_STATE
    
    if GAME_STATE == "MENU":
        draw_menu()
    elif GAME_STATE == "PLAYING":
        game()
    elif GAME_STATE == "GAME_OVER":
        draw_game_over()
        
    
glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
glutInitWindowSize(1000, 800)
wind = glutCreateWindow(b"Drop 'n' Run - Level 2")
glutDisplayFunc(showScreen)
glutIdleFunc(idle)
glutKeyboardFunc(keyboard)
glutMouseFunc(mouse)
glutInitWindowPosition(0,0)
glutMainLoop()
