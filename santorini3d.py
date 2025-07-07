#!/usr/bin/python3

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from objects3d import *
import random
import sys

WIDTH, HEIGHT = 1200, 800
FIELD_SIZE = 5

class Cube:
    def __init__(self, pos, color, pick_color):
        self.pos = np.array(pos, dtype=float)
        self.color = color
        self.pick_color = pick_color  # Unique color for picking
        self.size = 1.0

    def draw(self, wireframe=False, color_override=None):
        glPushMatrix()
        glTranslatef(*self.pos)
        glScalef(self.size, self.size, self.size)
        if color_override is not None:
            glColor3fv(color_override)
        else:
            glColor3fv(self.color)
        if wireframe:
            glut_style = GL_LINE_LOOP
        else:
            glut_style = GL_QUADS
        # Draw cube faces
        vertices = [
            [1,1,1], [1,1,-1], [1,-1,-1], [1,-1,1],
            [-1,1,1], [-1,1,-1], [-1,-1,-1], [-1,-1,1]
        ]
        faces = [
            [0,1,2,3], [3,2,6,7], [7,6,5,4],
            [4,5,1,0], [5,6,2,1], [4,0,3,7]
        ]
        glBegin(glut_style)
        for face in faces:
            for vert in face:
                glVertex3fv(vertices[vert])
        glEnd()
        glPopMatrix()

def render_scene(cubes, selected_idx=None, outline=False):
    for i, cube in enumerate(cubes):
        cube.draw()
        if outline and selected_idx == i:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glLineWidth(3)
            cube.draw(wireframe=True, color_override=(1,1,0))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glLineWidth(1)

def render_for_picking(cubes):
    for cube in cubes:
        cube.draw(color_override=cube.pick_color)

def pick_object(mouse_x, mouse_y, cubes):
    # Render to back buffer with unique colors
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    render_for_picking(cubes)
    glFlush()
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    data = glReadPixels(mouse_x, HEIGHT - mouse_y, 1, 1, GL_RGB, GL_UNSIGNED_BYTE)
    picked_color = (data[0]/255.0,data[1]/255.0,data[2]/255.0)
    for idx, cube in enumerate(cubes):
        if np.allclose(picked_color, cube.pick_color, atol=1/255):
            return idx
    return None


class Field:
    def __init__(self):
        self.matrix=[[0]*5,[0]*5,[0]*5,[0]*5,[0]*5]
        self.trans_mat = [[0,0,0],[2.05,5,-2.0],[2,6,-2.0],[3.6,3,-3.4]]
    
    def build(self, i, j):
        if self.matrix[i][j]<40:
            self.matrix+=10
    
    def get(self, i, j):
        return self.matrix[i][j]
    
    def get_trans_mat(self, v):
        return self.trans_mat[v]
    
    def get_base_pos(self, i, j, v):
        return (j*29.5,v*2.0-20,i*29.5)
    
    def random(self):
        for row in self.matrix:
            for j in range(0,len(row)):
                row[j] = random.choice([0,10,20,30,40])

    def find_available(self, pos_i, pos_j):
        available = []
        for i in range(pos_i-1,pos_i+2):
            for j in range(pos_j-1,pos_j+2):
                if i>=0 and i<FIELD_SIZE and j>=0 and j<FIELD_SIZE:
                    if abs(self.matrix[i][j]-self.matrix[pos_i][pos_j]) <= 10:
                        available.append((i,j))
        return available

    def print(self):
        print(self.matrix)

    def render_field(self, obj3d):
        for i in range(0,len(self.matrix)):
            for j in range(0,len(self.matrix[i])):
                for v in range(0,self.matrix[i][j]+1,10):
                    glPushMatrix()
                    glTranslate(*self.get_base_pos(i,j,v))
                    if v==10:
                        glTranslate(*self.trans_mat[0])
                        obj3d.draw("level1_v1")
                    elif v==20:
                        glTranslate(*self.trans_mat[1])
                        obj3d.draw("level2_v1")
                    elif v==30:
                        glTranslate(*self.trans_mat[2])
                        obj3d.draw("level3")
                    elif v==40:
                        glTranslate(*self.trans_mat[3])
                        obj3d.draw("dome")
                    glPopMatrix()


class Worker:
    def __init__(self):
        self.pos = None
    
    def set_position(self, pos_ij, field: Field):
        i, j = pos_ij
        self.pos = (i, j, field.get(i,j)+10)

    def set_random_pos(self, field: Field):
        for n in range(25):
            i = random.randint(0,4)
            j = random.randint(0,4)
            if field.get(i, j) < 40:
                self.pos = (i, j, field.get(i,j)+10)
                return True
        return False
    
    def get_position(self):
        return self.pos
    
    def get_ij_position(self):
        return (self.pos[0], self.pos[1])
    
    def draw(self, obj3d, field: Field):
        if self.pos:
            glPushMatrix()
            glTranslate(*field.get_base_pos(*self.pos))
            v = self.pos[2]//10
            if v>0:
                glTranslate(*field.get_trans_mat(v-1))
            glTranslate(5,0,0)
            glScale(2,2,2)
            obj3d.draw("worker")
            glPopMatrix()


class Player:
    def __init__(self, obj3d : OBJECTS3D, field: Field):
        self.workers = [Worker(), Worker()]
        self.active_worker = None
        self.obj3d = obj3d
        self.field = field
    
    def set_active_worker(self, num):
        self.active_worker = num
    
    def move(self, pos_ij):
        if self.active_worker:
            self.workers[self.active_worker].set_position(pos_ij, self.field)

    def draw_workers(self):
        for i, elm in enumerate(self.workers):
            elm.draw(self.obj3d, self.field)


def main():
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    clock = pygame.time.Clock()

    # Camera parameters
    cam_angle = [30, 0]
    cam_radius = 200
    cam_target = np.array([0,0,0], dtype=float)

    # Scene objects
    cubes = [
        Cube([-2,0,0], (1,0,0), (1,0,0)),
        Cube([2,0,0], (0,1,0), (0,1,0)),
        Cube([0,2,0], (0,0,1), (0,0,1)),
    ]
    obj3d = OBJECTS3D()
    field = Field()
    field.random()
    field.print()
    worker = Worker()
    if not worker.set_random_pos(field):
        print("can't place worker")
        sys.exit()
    else:
        print(worker.get_position())
    print(field.find_available(*worker.get_ij_position()))
    selected_idx = None
    dragging = False
    drag_offset = np.zeros(3)
    last_mouse_pos = None

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mx, my = pygame.mouse.get_pos()
                    idx = pick_object(mx, my, cubes)
                    selected_idx = idx
                    if idx is not None:
                        dragging = True
                        last_mouse_pos = np.array(pygame.mouse.get_pos())
                elif event.button == 4:  # Wheel up
                    cam_radius = max(2, cam_radius - 1)
                elif event.button == 5:  # Wheel down
                    cam_radius += 1
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False
            elif event.type == MOUSEMOTION:
                if pygame.mouse.get_pressed()[2]:  # Right mouse for camera
                    dx, dy = event.rel
                    cam_angle[0] += dy * 0.5
                    cam_angle[1] += dx * 0.5
                    if cam_angle[0]>30:
                        cam_angle[0] = 30
                    if cam_angle[0]<5:
                        cam_angle[0] = 5
                if dragging and selected_idx is not None:
                    mx, my = pygame.mouse.get_pos()
                    dx, dy = np.array([mx, my]) - last_mouse_pos
                    dx *= -1
                    # Move in camera's right/up plane
                    right = np.array([
                        np.sin(np.radians(cam_angle[1]-90)), 0,
                        np.cos(np.radians(cam_angle[1]-90))
                    ])
                    up = np.array([0,1,0])
                    move = right * dx * 0.01 + up * -dy * 0.01
                    cubes[selected_idx].pos += move
                    last_mouse_pos = np.array([mx, my])

        # Camera setup
        glViewport(0, 0, WIDTH, HEIGHT)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glLightfv(GL_LIGHT0, GL_POSITION, (100, 200, 0, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.5, 0.5, 0.5, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (2.8, 2.8, 2.8, 1.0))
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)
        glClearColor(0.45, 0.7, 0.9, 1)  # Sky blue
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, WIDTH/HEIGHT, 0.1, 350)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        phi, theta = np.radians(cam_angle)
        cam_x = cam_radius * np.cos(phi) * np.sin(theta)
        cam_y = cam_radius * np.sin(phi)
        cam_z = cam_radius * np.cos(phi) * np.cos(theta)
        gluLookAt(cam_x, cam_y, cam_z, *cam_target, 0,1,0)
        glPushMatrix()
        glTranslate(0,-30,0)
        glPushMatrix()
        glRotate(-90,1,0,0)
        obj3d.draw("field")
        glPopMatrix()
        glPushMatrix()
        glTranslate(-70,0,-48)
        field.render_field(obj3d)
        worker.draw(obj3d, field)
        glPopMatrix()
        glPopMatrix()
        #render_scene(cubes, selected_idx, outline=True)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()

