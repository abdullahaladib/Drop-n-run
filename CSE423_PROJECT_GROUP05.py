#Drop_n_run main .py file

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


GAME_STATE = "MENU"

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
BULLET_DAMAGE = GUN_LEVEL
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

def keyboard(key, x, y):
    global player1_x, player1_y, player1_z, is_jumping, jump_velocity, is_crouching, GAME_STATE, PLAYER_HP, PLAYER_SCORE, spawn_protection_time, GUN_LEVEL, BULLET_DAMAGE, LEVEL2_UNLOCKED, CHEAT_MODE
    key = key.decode("utf-8").lower()

    if key == '\x1b' and GAME_STATE == "PLAYING":
        GAME_STATE = "MENU"
        save_score(PLAYER_SCORE)
        print("Returned to menu!")
        return
    if key == 'm' and GAME_STATE == "GAME_OVER":
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
    elif key == 'y':
        CHEAT_MODE = not CHEAT_MODE
        print(f"Cheat mode {'enabled' if CHEAT_MODE else 'disabled'}!")
    
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
        print("Bullet fired!")

def update_bullets():
    global bullets, mobs, PLAYER_SCORE
    bullets_to_remove = []
    
    for i, bullet in enumerate(bullets):
        bullet['y'] += bullet['vy']
        
        if bullet['y'] < -650:
            bullets_to_remove.append(i)
            continue
        
        bullet_radius = 7.5 
        for mob_idx, mob in enumerate(mobs):
            mob_x_min = mob['x'] - 50
            mob_x_max = mob['x'] + 50
            mob_y_min = mob['y'] - 50
            mob_y_max = mob['y'] + 50
            mob_z_min = mob['z'] - 50
            mob_z_max = mob['z'] + 50
            
            bullet_x_min = bullet['x'] - bullet_radius
            bullet_x_max = bullet['x'] + bullet_radius
            bullet_y_min = bullet['y'] - bullet_radius
            bullet_y_max = bullet['y'] + bullet_radius
            bullet_z_min = bullet['z'] - 75
            bullet_z_max = bullet['z'] + 75
            
            if (mob_x_min < bullet_x_max and mob_x_max > bullet_x_min and
                mob_y_min < bullet_y_max and mob_y_max > bullet_y_min and
                mob_z_min < bullet_z_max and mob_z_max > bullet_z_min):
                mob['hp'] -= BULLET_DAMAGE
                bullets_to_remove.append(i)
                
                if mob['hp'] <= 0:
                    mob['x'] = random.randrange(-580, 580)
                    mob['y'] = -600
                    mob['z'] = random.choice([0, 145])
                    mob['hp'] = 5
                    mob['colliding'] = False
                    mob['delay'] = 0
                    PLAYER_SCORE += 10
                    save_score(PLAYER_SCORE)
                    print(f"Obstacle destroyed! Score: {PLAYER_SCORE}")
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
        player1_z += jump_velocity
        jump_velocity -= 1 
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
      mob['delay'] -= 1
      continue
    if mob['y'] != 575:
      mob['y'] += 10
    if mob['y'] >= 575:
      mob['y'] = -600
      mob['x'] = random.randrange(-580,580)
      mob['z'] = random.choice([0,145])
      mob['delay'] = random.randrange(60, 120)
def idle():
    global spawn_protection_time, GAME_STATE, PLAYER_SCORE, GUN_LEVEL, BULLET_DAMAGE, LEVEL2_UNLOCKED, reload_counter
    protection.update()
    reload_counter += 1
    if reload_counter >= 60:
        reload_counter = 0
        PLAYER_SCORE = load_score()
        GUN_LEVEL = load_gun_level()
        BULLET_DAMAGE = GUN_LEVEL
        LEVEL2_UNLOCKED = load_level2_unlock()
    
    if GAME_STATE == "PLAYING":
        spawn_mobs()
        check_collision()
        update_player()
        update_bullets() 
        if spawn_protection_time > 0:
            spawn_protection_time -= 1
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
glutKeyboardFunc(keyboard)
glutMouseFunc(mouse)
glutInitWindowPosition(0,0)
glutMainLoop()


#level2.py
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
CHEAT_MODE = False

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
    global player1_x, player1_y, player1_z, is_jumping, jump_velocity, is_crouching, GAME_STATE, PLAYER_HP, PLAYER_SCORE, spawn_protection_time, CHEAT_MODE
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
    elif key == 'y':
        CHEAT_MODE = not CHEAT_MODE
        print(f"Cheat mode {'enabled' if CHEAT_MODE else 'disabled'}!")
    
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
        
        # Only check collision if not in spawn protection and not in cheat mode
        if spawn_protection_time <= 0 and not CHEAT_MODE:
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
  
  if CHEAT_MODE:
    return
  
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
    gluOrtho2D(0, 1000, 800, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
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
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 800, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)
    glColor3f(0.1, 0, 0) 
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glColor3f(0.05, 0, 0) 
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
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
    gluOrtho2D(0, 1000, 800, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw background - neon black and red theme
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


#2player.py

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import sys
import os
import shapes

GAME_STATE = "MENU"

PLAYER1_HP = 3
player1_x = -200
player1_z = 0
player1_y = 575
player1_is_jumping = False
player1_jump_velocity = 0
player1_is_crouching = False
player1_spawn_protection_time = 0
PLAYER1_COLOR = (0, 1, 1)

PLAYER2_HP = 3
player2_x = 200
player2_z = 0
player2_y = 575
player2_is_jumping = False
player2_jump_velocity = 0
player2_is_crouching = False
player2_spawn_protection_time = 0
PLAYER2_COLOR = (1, 0, 1)

camera_pos = (0, 700, 400)
mobs = [{'x': 0, 'y': -600, 'z': 30, 'delay': 0, 'colliding_p1': False, 'colliding_p2': False, 'hp': 5},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 30, 'colliding_p1': False, 'colliding_p2': False, 'hp': 5},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 60, 'colliding_p1': False, 'colliding_p2': False, 'hp': 5},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 90, 'colliding_p1': False, 'colliding_p2': False, 'hp': 5},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 120, 'colliding_p1': False, 'colliding_p2': False, 'hp': 5}]
bullets = []
PITCH_HALF = 600
PLAYER_RADIUS_Y = 45
PLAYER_RADIUS_X = 30

ground_level = 0

def keyboard(key, x, y):
    global player1_x, player1_y, player1_z, player1_is_jumping, player1_jump_velocity, player1_is_crouching
    global player2_x, player2_y, player2_z, player2_is_jumping, player2_jump_velocity, player2_is_crouching
    global GAME_STATE, PLAYER1_HP, PLAYER2_HP
    key = key.decode("utf-8").lower()

    if key == '\x1b' and GAME_STATE == "PLAYING":
        GAME_STATE = "MENU"
        print("Returned to menu!")
        return

    if key == 'm' and GAME_STATE == "GAME_OVER":
        reset_game()
        GAME_STATE = "MENU"
        print("Returning to menu!")
        return

    if GAME_STATE != "PLAYING":
        return

    step = 10

    if PLAYER1_HP > 0:
        if key == 'w':
            player1_y -= step
        elif key == 's':
            player1_y += step
        elif key == 'a':
            player1_x += step
        elif key == 'd':
            player1_x -= step
        elif key == ' ' and not player1_is_jumping and not player1_is_crouching:
            player1_is_jumping = True
            player1_jump_velocity = 25
        elif key == 'c':
            player1_is_crouching = not player1_is_crouching
        elif key == 'f':
            shoot(1, player1_x, player1_y, player1_z)
        
        clamp_player_position(1)
    
    if PLAYER2_HP > 0:
        if key == 'l':
            shoot(2, player2_x, player2_y, player2_z)
        if key == ',' and not player2_is_jumping and not player2_is_crouching:
            player2_is_jumping = True
            player2_jump_velocity = 25
        if key == '.':
            player2_is_crouching = not player2_is_crouching

def special_keys(key, x, y):
    global player2_x, player2_y, player2_z, player2_is_jumping, player2_jump_velocity, player2_is_crouching
    global GAME_STATE, PLAYER2_HP
    
    if GAME_STATE != "PLAYING":
        return
    
    if PLAYER2_HP <= 0:
        return
    
    step = 10
    
    if key == GLUT_KEY_UP:
        player2_y -= step
    elif key == GLUT_KEY_DOWN:
        player2_y += step
    elif key == GLUT_KEY_LEFT:
        player2_x += step
    elif key == GLUT_KEY_RIGHT:
        player2_x -= step
    
    clamp_player_position(2)

def clamp_player_position(player_num):
    global player1_x, player1_y, player2_x, player2_y
    
    max_x = PITCH_HALF - PLAYER_RADIUS_X - 50
    min_x = -PITCH_HALF + PLAYER_RADIUS_X + 50
    max_y = PITCH_HALF - PLAYER_RADIUS_Y - 20
    min_y = -PITCH_HALF + PLAYER_RADIUS_Y + 20
    
    if player_num == 1:
        if player1_x > max_x: player1_x = max_x
        if player1_x < min_x: player1_x = min_x
        if player1_y > max_y: player1_y = max_y
        if player1_y < min_y: player1_y = min_y
    else:
        if player2_x > max_x: player2_x = max_x
        if player2_x < min_x: player2_x = min_x
        if player2_y > max_y: player2_y = max_y
        if player2_y < min_y: player2_y = min_y

def shoot(player_num, px, py, pz):
    if GAME_STATE == "PLAYING":
        bullet = {
            'x': px,
            'y': py - 50,
            'z': pz + 60,
            'vy': -15,
            'player': player_num
        }
        bullets.append(bullet)
        print(f"Player {player_num} fired!")

def update_bullets():
    global bullets, mobs
    bullets_to_remove = []
    
    for i, bullet in enumerate(bullets):
        bullet['y'] += bullet['vy']
        
        if bullet['y'] < -650:
            bullets_to_remove.append(i)
            continue
        
        bullet_radius = 7.5
        for mob in mobs:
            mob_x_min = mob['x'] - 50
            mob_x_max = mob['x'] + 50
            mob_y_min = mob['y'] - 50
            mob_y_max = mob['y'] + 50
            mob_z_min = mob['z'] - 50
            mob_z_max = mob['z'] + 50
            
            bullet_x_min = bullet['x'] - bullet_radius
            bullet_x_max = bullet['x'] + bullet_radius
            bullet_y_min = bullet['y'] - bullet_radius
            bullet_y_max = bullet['y'] + bullet_radius
            bullet_z_min = bullet['z'] - 75
            bullet_z_max = bullet['z'] + 75
            
            if (mob_x_min < bullet_x_max and mob_x_max > bullet_x_min and
                mob_y_min < bullet_y_max and mob_y_max > bullet_y_min and
                mob_z_min < bullet_z_max and mob_z_max > bullet_z_min):
                mob['hp'] -= 1
                bullets_to_remove.append(i)
                
                if mob['hp'] <= 0:
                    mob['x'] = random.randrange(-580, 580)
                    mob['y'] = -600
                    mob['z'] = random.choice([0, 145])
                    mob['hp'] = 5
                    mob['colliding_p1'] = False
                    mob['colliding_p2'] = False
                    mob['delay'] = 0
                break
    
    for i in sorted(bullets_to_remove, reverse=True):
        if i < len(bullets):
            bullets.pop(i)

def draw_bullets():
    for bullet in bullets:
        glPushMatrix()
        glTranslatef(bullet['x'], bullet['y'], bullet['z'])
        if bullet['player'] == 1:
            glColor3f(0, 1, 1)
        else:
            glColor3f(1, 0, 1)
        glScalef(15, 15, 15)
        glutSolidCube(1)
        glPopMatrix()

def update_players():
    global player1_z, player1_is_jumping, player1_jump_velocity
    global player2_z, player2_is_jumping, player2_jump_velocity
    
    if player1_is_jumping:
        player1_z += player1_jump_velocity
        player1_jump_velocity -= 1
        if player1_z < ground_level:
            player1_z = ground_level
            player1_is_jumping = False
            player1_jump_velocity = 0
    
    if player2_is_jumping:
        player2_z += player2_jump_velocity
        player2_jump_velocity -= 1
        if player2_z < ground_level:
            player2_z = ground_level
            player2_is_jumping = False
            player2_jump_velocity = 0

def draw_player(player_num, px, py, pz, is_crouching, spawn_protection_time, color):
    if spawn_protection_time > 0:
        if (spawn_protection_time // 10) % 2 == 0:
            return
    
    glPushMatrix()
    glTranslatef(px, py, pz)
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
    
    r, g, b = color
    glColor3f(r, g, b)
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
        glColor3f(1, 0, 0)
        glTranslatef(mob['x'], mob['y'], mob['z'])
        glutSolidCube(100)
        glPopMatrix()

def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(120, 1.25, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    gluLookAt(0, 800, 500,
              0, 0, 0,
              0, 0, 1)

def check_collision():
    global player1_x, player1_y, player1_z, player1_spawn_protection_time, PLAYER1_HP
    global player2_x, player2_y, player2_z, player2_spawn_protection_time, PLAYER2_HP
    global player1_is_crouching, player2_is_crouching
    
    if player1_spawn_protection_time <= 0:
        player1_x_min = player1_x - PLAYER_RADIUS_X
        player1_x_max = player1_x + PLAYER_RADIUS_X
        player1_y_min = player1_y - PLAYER_RADIUS_Y
        player1_y_max = player1_y + PLAYER_RADIUS_Y
        player1_z_min = player1_z
        player1_z_max = player1_z + (70 if player1_is_crouching else 100)
        
        for mob in mobs:
            enemy_x_min = mob['x'] - 50
            enemy_x_max = mob['x'] + 50
            enemy_y_min = mob['y'] - 50
            enemy_y_max = mob['y'] + 50
            enemy_z_min = mob['z'] - 50
            enemy_z_max = mob['z'] + 50
            
            is_colliding = (player1_x_min < enemy_x_max and player1_x_max > enemy_x_min and
                           player1_y_min < enemy_y_max and player1_y_max > enemy_y_min and
                           player1_z_min < enemy_z_max and player1_z_max > enemy_z_min)
            
            if is_colliding:
                if not mob['colliding_p1']:
                    PLAYER1_HP -= 1
                    player1_x = -200
                    player1_y = 575
                    player1_z = 0
                    player1_spawn_protection_time = 180
                    mob['colliding_p1'] = True
                mob['colliding_p1'] = True
            else:
                mob['colliding_p1'] = False
    
    if player2_spawn_protection_time <= 0:
        player2_x_min = player2_x - PLAYER_RADIUS_X
        player2_x_max = player2_x + PLAYER_RADIUS_X
        player2_y_min = player2_y - PLAYER_RADIUS_Y
        player2_y_max = player2_y + PLAYER_RADIUS_Y
        player2_z_min = player2_z
        player2_z_max = player2_z + (70 if player2_is_crouching else 100)
        
        for mob in mobs:
            enemy_x_min = mob['x'] - 50
            enemy_x_max = mob['x'] + 50
            enemy_y_min = mob['y'] - 50
            enemy_y_max = mob['y'] + 50
            enemy_z_min = mob['z'] - 50
            enemy_z_max = mob['z'] + 50
            
            is_colliding = (player2_x_min < enemy_x_max and player2_x_max > enemy_x_min and
                           player2_y_min < enemy_y_max and player2_y_max > enemy_y_min and
                           player2_z_min < enemy_z_max and player2_z_max > enemy_z_min)
            
            if is_colliding:
                if not mob['colliding_p2']:
                    PLAYER2_HP -= 1
                    player2_x = 200
                    player2_y = 575
                    player2_z = 0
                    player2_spawn_protection_time = 180
                    mob['colliding_p2'] = True
                mob['colliding_p2'] = True
            else:
                mob['colliding_p2'] = False

def spawn_mobs():
    for mob in mobs:
        if mob['delay'] > 0:
            mob['delay'] -= 1
            continue
        if mob['y'] != 575:
            mob['y'] += 10
        if mob['y'] >= 575:
            mob['y'] = -600
            mob['x'] = random.randrange(-580, 580)
            mob['z'] = random.choice([0, 145])
            mob['delay'] = random.randrange(60, 120)

def idle():
    global player1_spawn_protection_time, player2_spawn_protection_time, GAME_STATE
    
    if GAME_STATE == "PLAYING":
        spawn_mobs()
        check_collision()
        update_players()
        update_bullets()
        
        if player1_spawn_protection_time > 0:
            player1_spawn_protection_time -= 1
        if player2_spawn_protection_time > 0:
            player2_spawn_protection_time -= 1
        
        if PLAYER1_HP <= 0 and PLAYER2_HP <= 0:
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
    if PLAYER1_HP > 0:
        draw_player(1, player1_x, player1_y, player1_z, player1_is_crouching, player1_spawn_protection_time, PLAYER1_COLOR)
    if PLAYER2_HP > 0:
        draw_player(2, player2_x, player2_y, player2_z, player2_is_crouching, player2_spawn_protection_time, PLAYER2_COLOR)
    draw_enemy()
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 800, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    
    if PLAYER1_HP > 0:
        glColor3f(0, 1, 1)
    else:
        glColor3f(0.5, 0.5, 0.5)
    glRasterPos2f(20, 30)
    hp_text = f"P1 HP: {PLAYER1_HP}" if PLAYER1_HP > 0 else "P1 HP: 0 (DEAD)"
    for char in hp_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    if PLAYER2_HP > 0:
        glColor3f(1, 0, 1)
    else:
        glColor3f(0.5, 0.5, 0.5)
    glRasterPos2f(800, 30)
    hp_text = f"P2 HP: {PLAYER2_HP}" if PLAYER2_HP > 0 else "P2 HP: 0 (DEAD)"
    for char in hp_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    glEnable(GL_DEPTH_TEST)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def draw_menu():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 800, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.2, 0.3)
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
    glColor3f(1, 1, 1)
    glRasterPos2f(300, 200)
    title = "2 PLAYER MODE"
    for char in title:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    glColor3f(0, 1, 1)
    glRasterPos2f(450, 350)
    play_text = "PLAY"
    for char in play_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    glColor3f(1, 0.5, 0)
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
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 800, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.2, 0.3)
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
    glColor3f(1, 0, 0)
    glRasterPos2f(350, 300)
    game_over_text = "GAME OVER"
    for char in game_over_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
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

def reset_game():
    global PLAYER1_HP, PLAYER2_HP
    global player1_x, player1_y, player1_z, player1_is_jumping, player1_jump_velocity, player1_is_crouching, player1_spawn_protection_time
    global player2_x, player2_y, player2_z, player2_is_jumping, player2_jump_velocity, player2_is_crouching, player2_spawn_protection_time
    global bullets, mobs
    
    PLAYER1_HP = 3
    PLAYER2_HP = 3
    
    player1_x = -200
    player1_y = 575
    player1_z = 0
    player1_is_jumping = False
    player1_jump_velocity = 0
    player1_is_crouching = False
    player1_spawn_protection_time = 0
    
    player2_x = 200
    player2_y = 575
    player2_z = 0
    player2_is_jumping = False
    player2_jump_velocity = 0
    player2_is_crouching = False
    player2_spawn_protection_time = 0
    
    bullets.clear()
    
    for mob in mobs:
        mob['x'] = 0
        mob['y'] = -600
        mob['z'] = 30
        mob['delay'] = random.randrange(0, 121)
        mob['colliding_p1'] = False
        mob['colliding_p2'] = False
        mob['hp'] = 5

def mouse(button, state, x, y):
    global GAME_STATE
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if 430 < x < 530 and 335 < y < 365 and GAME_STATE == "MENU":
            reset_game()
            GAME_STATE = "PLAYING"
            print("2 Player mode started!")
        
        elif 400 < x < 600 and 435 < y < 465 and GAME_STATE == "MENU":
            print("Returning to main menu...")
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
wind = glutCreateWindow(b"Drop 'n' Run - 2 Player")
glutDisplayFunc(showScreen)
glutIdleFunc(idle)
glutKeyboardFunc(keyboard)
glutSpecialFunc(special_keys)
glutMouseFunc(mouse)
glutInitWindowPosition(0, 0)
glutMainLoop()
