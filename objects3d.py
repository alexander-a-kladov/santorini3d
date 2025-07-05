#!/usr/bin/python3

import os
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

# --- OBJ and MTL Loader ---
def MTL(filename):
    contents = {}
    mtl = None
    for line in open(filename, "r"):
        if line.startswith('#'): continue
        values = line.strip().split()
        if not values: continue
        if values[0] == 'newmtl':
            mtl = contents[values[1]] = {}
        elif mtl is None:
            raise ValueError("mtl file doesn't start with newmtl stmt")
        elif values[0] == 'map_Kd':
            mtl['map_Kd'] = values[1]
            surf = pygame.image.load(mtl['map_Kd'])
            image = pygame.image.tostring(surf, 'RGBA', 1)
            ix, iy = surf.get_rect().size
            texid = mtl['texture_Kd'] = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texid)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        else:
            mtl[values[0]] = list(map(float, values[1:]))
    return contents

class OBJ:
    def __init__(self, filename, swapyz=False):
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.mtl = None
        material = None
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.strip().split()
            if not values: continue
            if values[0] == 'v':
                v = list(map(float, values[1:4]))
                if swapyz: v = [v[0], v[2], v[1]]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = list(map(float, values[1:4]))
                if swapyz: v = [v[0], v[2], v[1]]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(list(map(float, values[1:3])))
            elif values[0] in ('usemtl', 'usemat'):
                material = values[1]
            elif values[0] == 'mtllib':
                self.mtl = MTL(values[1])
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    texcoords.append(int(w[1]) if len(w) > 1 and w[1] else 0)
                    norms.append(int(w[2]) if len(w) > 2 and w[2] else 0)
                self.faces.append((face, norms, texcoords, material))
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        glEnable(GL_TEXTURE_2D)
        glFrontFace(GL_CCW)
        for face in self.faces:
            vertices, normals, texture_coords, material = face
            mtl = self.mtl[material] if self.mtl and material else None
            if mtl and 'texture_Kd' in mtl:
                glBindTexture(GL_TEXTURE_2D, mtl['texture_Kd'])
            elif mtl and 'Kd' in mtl:
                glColor(*mtl['Kd'])
            glBegin(GL_POLYGON)
            for i in range(len(vertices)):
                if normals[i] > 0:
                    glNormal3fv(self.normals[normals[i] - 1])
                if texture_coords[i] > 0:
                    glTexCoord2fv(self.texcoords[texture_coords[i] - 1])
                glVertex3fv(self.vertices[vertices[i] - 1])
            glEnd()
        glDisable(GL_TEXTURE_2D)
        glEndList()

class OBJECTS3D:
    def __init__(self):
        os.chdir("objects")
        self.objects3d = dict()
        self.objects3d["field"] = OBJ("field.obj", swapyz=True)
        for n in range(1,4):
            fname = f'level1_v{n}.obj'
            name = f'level1_v{n}'
            self.objects3d[name] = OBJ(fname)
        for n in range(1,2):
            fname = f'level2_v{n}.obj'
            name = f'level2_v{n}'
            self.objects3d[name] = OBJ(fname)
        self.objects3d['level3'] = OBJ('level3.obj')
        self.objects3d['dome'] = OBJ('dome.obj')
        self.objects3d['worker'] = OBJ('worker.obj')
        os.chdir("..")
        
    def draw(self, obj_name):
        if obj_name in self.objects3d:
            glCallList(self.objects3d[obj_name].gl_list)
        return None
    
