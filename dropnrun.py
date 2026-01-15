from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import shapes
import subprocess
import sys
import os
from spawnprotection import SpawnProtection

protection = SpawnProtection()

# Key state tracking for simultaneous inputs
keys_down = set()

GAME_STATE = "MENU"
TARGET_FPS = 60.0
frame_scale = 1.0
last_time = None

SCORE_FILE = "game_score.txt"
GUN_FILE = "gun_level.txt"
LEVEL2_UNLOCK_FILE = "level2_unlocked.txt"

def save_score(score):
    try:
        with open(SCORE_FILE, 'w') as f:
            f.write(str(score))
    except Exception as e:
        print(f"Error saving score: {e}")

def load_score():
    try:
        if os.path.exists(SCORE_FILE):
            with open(SCORE_FILE, 'r') as f:
                return int(f.read().strip())
    except Exception as e:
        print(f"Error loading score: {e}")
    return 0

def save_gun_level(level):
    try:
        with open(GUN_FILE, 'w') as f:
            f.write(str(level))
    except Exception as e:
        print(f"Error saving gun level: {e}")

def load_gun_level():
    try:
        if os.path.exists(GUN_FILE):
            with open(GUN_FILE, 'r') as f:
                return int(f.read().strip())
    except Exception as e:
        print(f"Error loading gun level: {e}")
    return 1

def save_level2_unlock(unlocked):
    try:
        with open(LEVEL2_UNLOCK_FILE, 'w') as f:
            f.write('1' if unlocked else '0')
    except Exception as e:
        print(f"Error saving Level 2 unlock status: {e}")

def load_level2_unlock():
    try:
        if os.path.exists(LEVEL2_UNLOCK_FILE):
            with open(LEVEL2_UNLOCK_FILE, 'r') as f:
                return f.read().strip() == '1'
    except Exception as e:
        print(f"Error loading Level 2 unlock status: {e}")
    return False

PLAYER_SCORE = load_score()
GUN_LEVEL = load_gun_level()
BULLET_DAMAGE = max(1, GUN_LEVEL)  # Ensure at least 1 damage
LEVEL2_UNLOCKED = load_level2_unlock()
PLAYER_HP = 3
DAMAGE = 1
MOB_HP = 5
PLAYER_SKIN_COLOR = (0,1,1)
reload_counter = 0 

camera_pos = (0,700,400)
player1_x = 0
player1_z = 0
player1_y = 575 
mobs = [{'x': 0, 'y': -600, 'z': 30, 'delay': 0, 'colliding': False, 'hp': 5},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 30, 'colliding': False, 'hp': 5},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 60, 'colliding': False, 'hp': 5},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 90, 'colliding': False, 'hp': 5},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 120, 'colliding': False, 'hp': 5}]
bullets = []
PITCH_HALF = 600
PLAYER_RADIUS_Y = 45
PLAYER_RADIUS_X = 30

is_jumping = False
jump_velocity = 0
is_crouching = False
ground_level = 0
spawn_protection_time = 0
CHEAT_MODE = False
shoot_cooldown = 0

def keyboardDown(key, x, y):
    global GAME_STATE, PLAYER_HP, PLAYER_SCORE, spawn_protection_time, GUN_LEVEL, BULLET_DAMAGE, LEVEL2_UNLOCKED, CHEAT_MODE
    global player1_x, player1_y, player1_z, keys_down
    
    key_char = key.decode("utf-8").lower()
    keys_down.add(key_char)
    
    if key_char == '\x1b' and GAME_STATE == "PLAYING":
        GAME_STATE = "MENU"
        save_score(PLAYER_SCORE)
        print("Returned to menu!")
        return
    if key_char == 'm' and GAME_STATE == "GAME_OVER":
        PLAYER_HP = 3
        spawn_protection_time = 0
        player1_x = 0
        player1_y = 575
        player1_z = 0
        bullets.clear()
        for mob in mobs:
            mob['x'] = 0
            mob['y'] = -600
            mob['z'] = 20
            mob['delay'] = random.randrange(0, 121)
            mob['colliding'] = False
            mob['hp'] = 5
        PLAYER_SCORE = load_score() 
        GUN_LEVEL = load_gun_level()
        BULLET_DAMAGE = GUN_LEVEL
        LEVEL2_UNLOCKED = load_level2_unlock()
        if PLAYER_SCORE >= 100 and not LEVEL2_UNLOCKED:
            LEVEL2_UNLOCKED = True
            save_level2_unlock(True)
            print("Level 2 unlocked!")
        GAME_STATE = "MENU"
        print("Returning to menu!")
        return

    if key_char == 'y' and GAME_STATE == "PLAYING":
        CHEAT_MODE = not CHEAT_MODE
        print(f"Cheat mode {'enabled' if CHEAT_MODE else 'disabled'}!")

def keyboardUp(key, x, y):
    global keys_down
    key_char = key.decode("utf-8").lower()
    keys_down.discard(key_char)

def process_input():
    global player1_x, player1_y, player1_z, is_jumping, jump_velocity, is_crouching, shoot_cooldown
    
    if GAME_STATE != "PLAYING":
        return
    
    step = 10 * frame_scale
    
    # Movement
    if 'w' in keys_down:
        player1_y -= step
    if 's' in keys_down:
        player1_y += step
    if 'a' in keys_down:
        player1_x += step
    if 'd' in keys_down:
        player1_x -= step
    
    # Jump
    if ' ' in keys_down and not is_jumping and not is_crouching:
        is_jumping = True
        jump_velocity = 25
    
    # Crouch toggle
    if 'c' in keys_down:
        is_crouching = not is_crouching
        keys_down.discard('c')
    
    # Shoot with cooldown
    if 'f' in keys_down and shoot_cooldown <= 0:
        shoot()
        shoot_cooldown = 10
    
    # Clamp position
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
    if GAME_STATE == "PLAYING":
        bullet = {
            'x': player1_x,
            'y': player1_y - 50, 
            'z': player1_z + 60, 
            'vy': -15  
        }
        bullets.append(bullet)
    

def update_bullets():
    global bullets, mobs, PLAYER_SCORE
    bullets_to_remove = []
    
    for i, bullet in enumerate(bullets):
        bullet['y'] += bullet['vy'] * frame_scale
        
        if bullet['y'] < -650:
            bullets_to_remove.append(i)
            continue
        
        hit = False
        for mob_idx, mob in enumerate(mobs):
            # MUCH larger collision boxes
            mob_x_min = mob['x'] - 80
            mob_x_max = mob['x'] + 80
            mob_y_min = mob['y'] - 80
            mob_y_max = mob['y'] + 80
            mob_z_min = mob['z'] - 80
            mob_z_max = mob['z'] + 80
            
            bullet_x_min = bullet['x'] - 20
            bullet_x_max = bullet['x'] + 20
            bullet_y_min = bullet['y'] - 20
            bullet_y_max = bullet['y'] + 20
            bullet_z_min = bullet['z'] - 80
            bullet_z_max = bullet['z'] + 80
            
             
            if (mob_x_min < bullet_x_max and mob_x_max > bullet_x_min and
                mob_y_min < bullet_y_max and mob_y_max > bullet_y_min and
                mob_z_min < bullet_z_max and mob_z_max > bullet_z_min):
                mob['hp'] -= BULLET_DAMAGE
                if i not in bullets_to_remove:
                    bullets_to_remove.append(i)
                hit = True
                
                if mob['hp'] <= 0:
                    mob['x'] = random.randrange(-580, 580)
                    mob['y'] = -600
                    mob['z'] = random.choice([0, 145])
                    mob['hp'] = 5
                    mob['colliding'] = False
                    mob['delay'] = 0
                    PLAYER_SCORE += 10
                    save_score(PLAYER_SCORE)
                break
    
    for i in sorted(bullets_to_remove, reverse=True):
        if i < len(bullets):
            bullets.pop(i)

def draw_bullets():
    for bullet in bullets:
        glPushMatrix()
        glTranslatef(bullet['x'], bullet['y'], bullet['z'])
        glColor3f(1, 0, 0) 
        glScalef(15, 15, 15)
        glutSolidCube(1)
        glPopMatrix()

def update_player():
    global player1_z, player1_x, player1_y, is_jumping, jump_velocity
    if is_jumping:
        player1_z += jump_velocity * frame_scale
        jump_velocity -= 1 * frame_scale 
        if player1_z < ground_level:
            player1_z = ground_level
            is_jumping = False
            jump_velocity = 0
    
    
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
  if spawn_protection_time > 0:
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
  
  if CHEAT_MODE:
    return
  
  player_x_min = player1_x - PLAYER_RADIUS_X
  player_x_max = player1_x + PLAYER_RADIUS_X
  player_y_min = player1_y - PLAYER_RADIUS_Y
  player_y_max = player1_y + PLAYER_RADIUS_Y
  player_z_min = player1_z
  if is_crouching:
    player_z_max = player1_z + 70
  else:
    player_z_max = player1_z + 100
  
  if spawn_protection_time > 0:
    return
  
  for idx, mob in enumerate(mobs):
    enemy_x_min = mob['x'] - 50
    enemy_x_max = mob['x'] + 50
    enemy_y_min = mob['y'] - 50
    enemy_y_max = mob['y'] + 50
    enemy_z_min = mob['z'] - 50
    enemy_z_max = mob['z'] + 50
    
    is_currently_colliding = (player_x_min < enemy_x_max and player_x_max > enemy_x_min and
                              player_y_min < enemy_y_max and player_y_max > enemy_y_min and
                              player_z_min < enemy_z_max and player_z_max > enemy_z_min)
    
    if is_currently_colliding:
      if not mob['colliding']:
        PLAYER_HP -= 1
        player1_x = 0
        player1_y = 575
        player1_z = 0
        spawn_protection_time = 180
        mob['colliding'] = True
      mob['colliding'] = True
    else:
      mob['colliding'] = False

def spawn_mobs():
  for mob in mobs:
    if mob['delay'] > 0:
            mob['delay'] -= frame_scale
            continue
    if mob['y'] != 575:
            mob['y'] += 10 * frame_scale
    if mob['y'] >= 575:
      mob['y'] = -600
      mob['x'] = random.randrange(-580,580)
      mob['z'] = random.choice([0,145])
      mob['delay'] = random.randrange(60, 120)
def idle():
    global spawn_protection_time, GAME_STATE, PLAYER_SCORE, GUN_LEVEL, BULLET_DAMAGE, LEVEL2_UNLOCKED, reload_counter, frame_scale, last_time, shoot_cooldown

    current_time = glutGet(GLUT_ELAPSED_TIME) / 1000.0
    if last_time is None:
        last_time = current_time
        delta_time = 1.0 / TARGET_FPS
    else:
        delta_time = max(0.0, current_time - last_time)
        last_time = current_time

    frame_scale = delta_time * TARGET_FPS
    protection.update()
    reload_counter += frame_scale
    
    if shoot_cooldown > 0:
        shoot_cooldown -= frame_scale
    
    if reload_counter >= 60:
        reload_counter = 0
        PLAYER_SCORE = load_score()
        GUN_LEVEL = load_gun_level()
        BULLET_DAMAGE = GUN_LEVEL
        LEVEL2_UNLOCKED = load_level2_unlock()
    
    if GAME_STATE == "PLAYING":
        process_input()
        spawn_mobs()
        check_collision()
        update_player()
        update_bullets() 
        if spawn_protection_time > 0:
            spawn_protection_time -= frame_scale
            if spawn_protection_time < 0:
                spawn_protection_time = 0
        if PLAYER_HP <= 0:
            GAME_STATE = "GAME_OVER"
    glutPostRedisplay()

def game():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    setup_camera()
    
    shapes.pitch()
    shapes.wall()
    shapes.background()
    
    draw_bullets() 
    draw_player()
    draw_enemy()
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 800, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    glColor3f(1, 0, 0) 
    glRasterPos2f(20, 30)
    hp_text = f"HP: {PLAYER_HP}"
    for char in hp_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
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
    gluOrtho2D(0, 1000, 800, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
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
    gluOrtho2D(0, 1000, 800, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw background
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.2, 0.3)
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
    # Draw score in top-right
    glColor3f(1, 1, 0)
    glRasterPos2f(850, 30)
    score_text = f"SCORE: {PLAYER_SCORE}"
    for char in score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw gun level in top-left
    glColor3f(0, 1, 0)
    glRasterPos2f(20, 30)
    gun_text = f"GUN LEVEL: {GUN_LEVEL}"
    for char in gun_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw title
    glColor3f(1, 1, 1)
    glRasterPos2f(350, 200)
    title = "DROP 'N' RUN"
    for char in title:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw PLAY button (text that can be clicked)
    glColor3f(0, 1, 1)
    glRasterPos2f(420, 350)
    play_text = "LEVEL 1 - PLAY"
    for char in play_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw Level 2 button if unlocked
    if LEVEL2_UNLOCKED:
        glColor3f(0, 1, 0)  # Green for unlocked
        glRasterPos2f(420, 450)
        level2_text = "LEVEL 2 - PLAY"
        for char in level2_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    else:
        glColor3f(0.5, 0.5, 0.5)  # Gray for locked
        glRasterPos2f(380, 450)
        level2_text = "LEVEL 2 - LOCKED (100pts)"
        for char in level2_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw 2 PLAYER MODE button
    glColor3f(1, 1, 0)  # Yellow
    glRasterPos2f(400, 550)
    twoplay_text = "2 PLAYER MODE"
    for char in twoplay_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw UPGRADE GUN button with dynamic cost (max level 4)
    if GUN_LEVEL >= 4:
        glColor3f(0.5, 0.5, 0.5)  # Gray for max level
        glRasterPos2f(360, 650)
        upgrade_text = f"UPGRADE GUN (MAX LEVEL {GUN_LEVEL})"
        for char in upgrade_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    else:
        upgrade_cost = GUN_LEVEL * 50
        if PLAYER_SCORE >= upgrade_cost:
            glColor3f(0, 1, 0)  # Green if affordable
        else:
            glColor3f(0.5, 0.5, 0.5)  # Gray if not affordable
        glRasterPos2f(360, 650)
        upgrade_text = f"UPGRADE GUN (Level {GUN_LEVEL}) - {upgrade_cost} pts"
        for char in upgrade_text:
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
    gluOrtho2D(0, 1000, 800, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw background
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.2, 0.3)
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
    # Draw GAME OVER text
    glColor3f(1, 0, 0)
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
    global GAME_STATE, PLAYER_SCORE, GUN_LEVEL, BULLET_DAMAGE, LEVEL2_UNLOCKED
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Check if click is within LEVEL 1 PLAY button area
        if 400 < x < 600 and 335 < y < 365 and GAME_STATE == "MENU":
            PLAYER_SCORE = load_score()  # Reload score in case level2 updated it
            # Check if player has reached 100 points to unlock Level 2
            if PLAYER_SCORE >= 100 and not LEVEL2_UNLOCKED:
                LEVEL2_UNLOCKED = True
                save_level2_unlock(True)
                print("Level 2 unlocked!")
            GAME_STATE = "PLAYING"
            print("Level 1 started!")
        
        # Check if click is within LEVEL 2 button area and level is unlocked
        elif 400 < x < 600 and 435 < y < 465 and GAME_STATE == "MENU" and LEVEL2_UNLOCKED:
            print("Launching Level 2...")
            save_score(PLAYER_SCORE)  # Save current score before launching level2
            # Launch level2.py as a separate process
            try:
                subprocess.Popen([sys.executable, "level2.py"])
                print("Level 2 launched! You can close this window or continue playing Level 1.")
            except Exception as e:
                print(f"Error launching Level 2: {e}")
        
        # Check if click is within 2 PLAYER MODE button area
        elif 400 < x < 600 and 535 < y < 565 and GAME_STATE == "MENU":
            print("Launching 2 Player Mode...")
            save_score(PLAYER_SCORE)  # Save current score
            try:
                subprocess.Popen([sys.executable, "2player.py"])
                print("2 Player Mode launched!")
            except Exception as e:
                print(f"Error launching 2 Player Mode: {e}")
        
        # Check if click is within UPGRADE GUN button area
        elif 360 < x < 700 and 635 < y < 665 and GAME_STATE == "MENU":
            if GUN_LEVEL >= 4:
                print("Gun is already at maximum level (4)!")
            else:
                upgrade_cost = GUN_LEVEL * 50
                if PLAYER_SCORE >= upgrade_cost:
                    PLAYER_SCORE -= upgrade_cost
                    GUN_LEVEL += 1
                    BULLET_DAMAGE = GUN_LEVEL
                    save_score(PLAYER_SCORE)
                    save_gun_level(GUN_LEVEL)
                    print(f"Gun upgraded to level {GUN_LEVEL}! Damage: {BULLET_DAMAGE}")
                    if GUN_LEVEL < 4:
                        print(f"Next upgrade cost: {GUN_LEVEL * 50} points")
                    else:
                        print("Gun has reached maximum level!")
                else:
                    print(f"Not enough points! Need {upgrade_cost} points.")

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
wind = glutCreateWindow(b"Drop 'n' Run")
glutDisplayFunc(showScreen)
glutIdleFunc(idle)
glutKeyboardFunc(keyboardDown)
glutKeyboardUpFunc(keyboardUp)
glutMouseFunc(mouse)
glutInitWindowPosition(0,0)
glutMainLoop()