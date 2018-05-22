from __future__ import division # allows floating point division from integers
import FreeCAD
import Part
from Part import Geom2d
from FreeCAD import Base



#Find the minimum distance to another shape.
#distToShape(Shape s):  Returns a list of minimum distance and solution point pairs.
#
#Returned is a tuple of three: (dist, vectors, infos).
#
#dist is the minimum distance, in mm (float value).
#
#vectors is a list of pairs of App.Vector. Each pair corresponds to solution.
#Example: [(Vector (2.0, -1.0, 2.0), Vector (2.0, 0.0, 2.0)), (Vector (2.0,
#-1.0, 2.0), Vector (2.0, -1.0, 3.0))] First vector is a point on self, second
#vector is a point on s.
#
#infos contains additional info on the solutions. It is a list of tuples:
#(topo1, index1, params1, topo2, index2, params2)
#
#    topo1, topo2 are strings identifying type of BREP element: 'Vertex',
#    'Edge', or 'Face'.
#
#    index1, index2 are indexes of the elements (zero-based).
#
#    params1, params2 are parameters of internal space of the elements. For
#    vertices, params is None. For edges, params is one float, u. For faces,
#    params is a tuple (u,v). 



class curveOnSurface:
    
    def __init__(self, edge = None, face = None):
        self.face = face
        self.edge = edge
        self.curve2D = None
        self.edgeOnFace = None
        self.firstParameter = 0.0
        self.lastParameter = 1.0
        self.reverseTangent  = False
        self.reverseNormal   = False
        self.reverseBinormal = False
        self.isValid = False
        self.validate()

    def setEdge(self, edge):
        self.edge = edge
        self.validate()

    def setFace(self, face):
        self.face = face
        self.validate()

    def validate(self):
        c2d = None
        if (not self.edge == None) and (not self.face == None):
            c2d = self.face.curveOnSurface(self.edge)
            #if not isinstance(c2d,tuple):
                #print("curveOnSurface error.")
                #try:
                    #newedge = self.face.project([self.edge]).Edges[0]
                    #success = True
                    #c2d = self.face.curveOnSurface(newedge)
                    #print("Projection successful.")
                #except Part.OCCError:
                    #newface = self.face.Surface.toShape()
                    #newedge = newface.project([self.edge]).Edges[0]
                    #success = True
                    #print("Projection failed. Fallback on surface.")
                    #c2d = self.face.curveOnSurface(newedge)
            if isinstance(c2d,tuple):
                self.curve2D = c2d[0]
                self.firstParameter = c2d[1]
                self.lastParameter  = c2d[2]
                self.edgeOnFace = self.curve2D.toShape(self.face, self.firstParameter, self.lastParameter)
                if isinstance(self.edgeOnFace, Part.Edge):
                    self.isValid = True
                else:
                    self.isValid = False
                    self.edgeOnFace = self.edge
            else:
                self.isValid = False
                self.firstParameter = self.edge.FirstParameter
                self.lastParameter  = self.edge.LastParameter
                self.edgeOnFace = self.edge
        return(self.isValid)

    def valueAt(self, t):
        if self.isValid:
            return(self.edgeOnFace.valueAt(t))
        else:
            p = self.edge.valueAt(t)
            surf = self.face.Surface
            u,v = surf.parameter(p)            
            return(self.face.Surface.value(u,v))

    def tangentAt(self, t):
        if self.isValid:
            if self.reverseTangent:
                return(self.edgeOnFace.tangentAt(t).negative().normalize())
            else:
                return(self.edgeOnFace.tangentAt(t).normalize())
        else:
            if self.reverseTangent:
                return(self.edge.tangentAt(t).negative().normalize())
            else:
                return(self.edge.tangentAt(t).normalize())

    def normalAt(self, t):
        if self.isValid:
            vec = None
            p = self.curve2D.value(t)
            vec = self.face.normalAt(p.x,p.y)
            if self.reverseNormal:
                return(vec.negative().normalize())
            else:
                return(vec.normalize())
        else:
            p = self.edge.valueAt(t)
            surf = self.face.Surface
            u,v = surf.parameter(p)
            if self.reverseNormal:
                return(self.face.Surface.normal(u,v).negative().normalize())
            else:
                return(self.face.Surface.normal(u,v).normalize())

    def binormalAt(self, t):
        ta = self.tangentAt(t)
        n = self.normalAt(t)
        if (not ta == None) and (not n == None):
            if self.reverseBinormal:
                return(ta.cross(n).negative().normalize())
            else:
                return(ta.cross(n).normalize())
        else:
            return(None)

    def tangentTo(self, t, pt):
        v = self.valueAt(t)
        n = self.normalAt(t)
        tanPlane = Part.Plane(v,n)
        line = Part.Line(pt, pt.add(n))
        ptOnPlane = tanPlane.intersect(line)
        res = []
        if isinstance(ptOnPlane,tuple):
            for el in ptOnPlane:
                if isinstance(el,(tuple,list)):
                    for e in el:
                        if isinstance(e,Part.Point):
                            res.append(FreeCAD.Vector(e.X,e.Y,e.Z).sub(v))
        return(res)

    def build_param_list(self, num):
        if num < 2:
            num = 2
        ran = self.lastParameter - self.firstParameter
        self.param_list = list()
        for i in range(num):
            self.param_list.append(self.firstParameter + float(i) * ran / (num - 1))
        return(True)

    def dot(self, v1, v2):
        v13 = FreeCAD.Vector(v1.x, v1.y, 0.0)
        v23 = FreeCAD.Vector(v2.x, v2.y, 0.0)
        return(v13.dot(v23))

    def cross(self, v1, v2):
        v13 = FreeCAD.Vector(v1.x, v1.y, 0.0)
        v23 = FreeCAD.Vector(v2.x, v2.y, 0.0)
        return(v13.cross(v23))

    def orientation(self, v1, v2):
        v13 = FreeCAD.Vector(v1.x, v1.y, 0.0)
        v23 = FreeCAD.Vector(v2.x, v2.y, 0.0)
        cross3d = v13.cross(v23)
        z = FreeCAD.Vector(0.0, 0.0, 1.0)
        dot = z.dot(cross3d)
        print(dot)
        if dot < 0:
            return(-1.0)
        else:
            return(1.0)

    def get_cross_curves(self, num, scale):
        if scale == 0:
            scale = 1.0
        self.build_param_list(num)
        curves = list()
        for p in self.param_list:
            p0 = self.curve2D.value(p)
            no = self.curve2D.normal(p)
            ta = self.curve2D.tangent(p)
            fac = scale * self.orientation(ta,no)
            p1 = Base.Vector2d(p0.x + no.x * fac, p0.y + no.y * fac)
            ls1 = Geom2d.Line2dSegment(p0, p1)
            edge1 = ls1.toShape(self.face, ls1.FirstParameter, ls1.LastParameter)
            curves.append(edge1)
        return(curves)

            
