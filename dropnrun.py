from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random

camera_pos = (0,500,500)

class player:
  pass

class mob:
  pass

def setup_camera():
  glMatrixMode(GL_PROJECTION)
  glLoadIdentity()
  gluPerspective(120, 1.25, 0.1, 1500)
  glMatrixMode(GL_MODELVIEW)

  x,y,z = camera_pos

  gluLookAt(x,y,z,
            0,0,0,
            0,0,1)

def idle():
  glutPostRedisplay()

