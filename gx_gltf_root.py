#!/usr/bin/env python
# coding: utf-8

import pdb, sys, os, json, weakref, struct, gx_gltf_type as schema, inspect

from pprint import pprint


def get_schema_based(vars_dict):
    print(get_schema_based)
    res = list()
    names = vars_dict.keys()
    for n in names:
        o = vars_dict[n]
        if inspect.isclass(o) and issubclass(o, schema.Schema):
            res.append(o)
    return sorted(res)


class GltfNode(object):
    def __init__(self, d):
        # print("++", self)
        self.dict = d

    def __del__(self):
        pass
        # print("--", self)
        
    def set_gltf(self, base):
        setattr(self, 'root', weakref.ref(base, self.del_gltf))
        return self

    def del_gltf(self, base):
        pass
        # print("=>on_lost_root", self, base)  # GLTF Node's lost root object signal

    def get_gltf(self):
        return getattr(self, 'root')()       # Call weakref instance, for extract hardref to shared object

    def __getattr__(self, name):
        if hasattr(self, 'dict'):
            if not name in self.dict.keys():
                if 'name' == name:
                    self.dict['name'] = 'noname'
                if 'byteOffset' == name:
                    self.dict['byteOffset'] = 0
            return self.dict[name]
        raise AttributeError(self, name)

    def pprint(self, head = ""):
        print("%s%s at %s" % (head, self.__class__.__name__, "%08X"% id(self)) )
        gltf_keys = sorted( self.dict.keys() )
        for i in gltf_keys:
            print("%s--%-16s : %s" % (head, i, self.dict[i]))
        return self
            

class Animation(schema.Animation, GltfNode): pass

class Material(schema.Material, GltfNode): pass

class Texture(schema.Texture, GltfNode): pass

class Sampler(schema.Sampler, GltfNode): pass

class Image(schema.Image, GltfNode): pass

class Camera(schema.Camera, GltfNode): pass

class Skin(schema.Skin, GltfNode):
    def get_inverseBindMatrices(self):
        return self.get_gltf().accessors[self.inverseBindMatrices]
    
    def get_joints(self):
        """
        The 'skeleton' property (if present) points to the node that is the common root
        of a joints hierarchy or to a direct or indirect parent node of the common root.
        """
        return [ self.get_gltf().nodes[j] for j in self.joints ]
    
    def pprint(self, head):
        GltfNode.pprint(self, head)
        print("%sjoints %d" % (head, len(self.joints) ) )
        if hasattr(self, 'skeleton'):
            print("%sJ: TODO: implement skeleton node usage here!" % head)
        else:
            for j in self.get_joints():
                j.pprint("%sJ: " % head)
        self.get_inverseBindMatrices().pprint(head+"I ")
        print("%s<SkinEnd>" % head )

class Node(schema.Node, GltfNode):
    """  Attr/ Type       / Required             / Description
        ----/------------/----------------------/-------------
camera	   |integer     |No                    |The index of the camera referenced by this node.
children   |integer[1-*]|No                    |The indices of this node's children.	No
skin       |integer     |No                    |The index of the skin referenced by this node.	No
matrix     |number [16] |No, default: identity |A floating-point 4x4 transformation matrix stored in column-major order.
mesh       |integer     |No                    |The index of the mesh in this node.
rotation   |number [4]  |No, default: [0,0,0,1]|The node's unit quaternion rotation in the order (x, y, z, w), where w is the scalar.
scale      |number [3]  |No, default: [1,1,1]  |The node's non-uniform scale, given as the scaling factors along the x, y, and z axes.	
translation|number [3]  |No, default: [0,0,0]  |The node's translation along the x, y, and z axes.
weights    |number [1-*]|No                    |The weights of the instantiated Morph Target. Number of
           |            |                      |elements must match number of Morph Targets of used mesh.
name       |string      |No                    |The user-defined name of this object.
extensions |object      |No                    |Dictionary object with extension-specific objects.
extras     |any         |No                    |Application-specific data.
    """
    def has_mesh(self): return self.dict.has_key('mesh')
    def get_mesh(self): return self.get_gltf().meshes[self.mesh]
    def has_skin(self): return self.dict.has_key('skin')
    def get_skin(self): return self.get_gltf().skins[self.skin]

class Scene(schema.Scene, GltfNode): pass

class Accessor(schema.Accessor, GltfNode):
    #   bufferView     : 0      ; buffer view index in self.get_gltf().bufferViews
    #   byteOffset     : 0      ; additional offset in buffer view
    #   componentType  : 5126   ; integer enum value,  5126 => 'float', 5122 => 'short', ...
    #   count          : 459    ; items count 
    #   max            : [2.3708298206329346, 2.3708298206329346, 2.823808193206787],
    #   min            : [-2.3708298206329346, -2.3708298206329346, -2.823808193206787],
    #   type           : 'VEC3'
    __type_size = dict(SCALAR=1, VEC2=2, VEC3=3, VEC4=4, MAT2=4, MAT3=9, MAT4=16)
    
    @classmethod
    def get_type_size(cls, type_name):
        return cls.__type_size[type_name]

    def get_component_type(self):
        return Buffer.enums[self.componentType][0]
    
    def get_type(self):
        return self.type
    
    def get_buffer(self):
        """return global data positions in buffer"""
        return self.get_gltf().bufferViews[self.bufferView].get_buffer()
    
    def get_offset(self):
        """return global data offset in buffer"""
        return self.get_gltf().bufferViews[self.bufferView].get_offset() + self.byteOffset
    
    def get_stride(self):
        """return byte stride in data"""
        return self.get_gltf().bufferViews[self.bufferView].get_stride()
    
    def get_length(self):
        """return byte length of data"""
        return self.get_gltf().bufferViews[self.bufferView].get_length()
    
    def get_components(self):
        """return list of components"""
        # print self.type            # self.get_gltf().bufferViews[self.bufferView]
        form = Buffer.enums[self.componentType][1] * len(Buffer.types[self.type])
        size = Buffer.enums[self.componentType][2] * len(Buffer.types[self.type])
        stride = self.get_stride() if self.get_stride() else size
        offset = self.get_offset()
        # print offset, form, size, stride
        source = self.get_buffer().buff
        buff = list()
        for i in xrange(self.count):
            subj = struct.unpack(form, source[offset:(offset+size)])
            # subj = tuple([ round(i, 4) for i in subj ])
            for ii in subj:
                buff.append(ii)
            offset += stride
        return buff

class BufferView(schema.BufferView, GltfNode):
    #     buffer      : 0        - buffer-record index in self.get_gltf().buffers[index]
    #     byteLength  : 14688    - buffer size
    #     byteOffset  : 0        - bytes offset in target buffer object
    #     byteStride  : 12       - 0, if not exists
    #     target      : 34962
    def get_buffer(self): return self.get_gltf().buffers[self.dict['buffer']]
    def get_length(self): return self.dict['byteLength']
    def get_offset(self): return self.dict['byteOffset']
    def get_stride(self): return self.dict['byteStride'] if 'byteStride' in self.dict else 0

class Buffer(schema.Buffer, GltfNode):
    enums = {
        5120: (          "BYTE", "b", 1),
        5121: ( "UNSIGNED_BYTE", "B", 1),
        5122: (         "SHORT", "h", 2),
        5123: ("UNSIGNED_SHORT", "H", 2),
        5125: (  "UNSIGNED_INT", "L", 4),  # "L" - unsigned long
        5126: (         "FLOAT", "f", 4),
    }

    types = dict(
        SCALAR="0",
        VEC2="01",
        VEC3="012",
        VEC4="0123",
        MAT2="0123",
        MAT3="012345678",
        MAT4="0123456789012345"
    )

    def __init__(self, d):
        GltfNode.__init__(self, d)
        self.buff = bytearray()

    @staticmethod
    def get_keys():
        return sorted(['byteLength', 'uri'])

    def print_hex_dump(self):
        for ii in xrange(0, self.byteLength, 16):
            print("%08X " % ii + self.buffers[0].hex_dump(ii, 8) + " | " + self.buffers[0].hex_dump(ii + 8, 8))
            
    def hex_dump(self, offset, count):
        return " ".join(["%02X" % ord(x) for x in self.buff[offset: offset + count]])
    
    def set_gltf(self, base):               # Overloaded member
        o = GltfNode.set_gltf(self, base)   # Execute self-parent-class functionality, store return value as sret
        path = self.get_gltf().path         # Detect Self Byte Array Location uri
        path = os.path.abspath(path)
        path = os.path.normpath(path)
        path = os.path.split(path)[0]
        path = os.path.join(path, self.uri)
        self.buff = file(path, "rb").read()
        return o                            # !return stored overloaded method results

class MeshPrimitive(schema.MeshPrimitive, GltfNode ):
    def get_POSITION   (self): return self.get_gltf().accessors[self.attributes['POSITION']]
    def get_NORMAL     (self): return self.get_gltf().accessors[self.attributes['NORMAL']]
    def get_TEXCOORD_0(self): return self.get_gltf().accessors[self.attributes['TEXCOORD_0']]
    def get_JOINTS_0   (self): return self.get_gltf().accessors[self.attributes['JOINTS_0']]
    def get_WEIGHTS_0  (self): return self.get_gltf().accessors[self.attributes['WEIGHTS_0']]
    def get_material   (self): return self.get_gltf().materials[self.material]
    def get_indices    (self): return self.get_gltf().accessors[self.indices]

class Mesh(schema.Mesh, GltfNode):
    def __init__(self, d):                  # Overloaded constructor
        GltfNode.__init__(self, d)          # Call parent's constructor
        self.primitives = []
        for i in d['primitives']:
            self.primitives.append(MeshPrimitive(i))

    def set_gltf(self, base):               # Overloaded method
        o = GltfNode.set_gltf(self, base)   # Execute parent's method and store value
        for i in self.primitives:
            i.set_gltf(base)
        return o                            # return stored value, or some other value
    
    def get_attributes(self):
        return self.dict['primitives'][0]['attributes']
    
    def gen_shared_joints_0__normal__position__texcoord_0__weights_0(self):
        gltf_name  = self.get_gltf().get_gx_gltf_name()
        weights_0  = self.primitives[0].get_WEIGTHS_0()
        joints_0   = self.primitives[0].get_JOINTS_0()
        texcoord_0 = self.primitives[0].get_TEXCOORD_0()
        normal     = self.primitives[0].get_NORMAL()
        position   = self.primitives[0].get_POSITION()
    
        return { 'generator'   :'gen_shared_joints_0__normal__position__texcoord_0__weights_0'
                ,'gltf'        : gltf_name
                ,'name'        : self.dict['name']
                ,'textcoord_0' : { 'unit': Buffer.enums[texcoord_0.componentType][0], 'type': texcoord_0.type }
                ,'normal'      : { 'unit': Buffer.enums[    normal.componentType][0], 'type': normal.type }
                ,'position'    : { 'unit': Buffer.enums[  position.componentType][0], 'type': position.type }
                ,'joints_0'    : { 'unit': Buffer.enums[  joints_0.componentType][0], 'type': joints_0.type }
                ,'weights_0'   : { 'unit': Buffer.enums[ weights_0.componentType][0], 'type': weights_0.type }
                }

    def gen_cloned_joints_0__normal__position__texcoord_0__weights_0(self):
        return {'generator':'gen_cloned_joints_0__normal__position__texcoord_0__weights_0'}
    
    def gen_shared_normal__position__texcoord_0(self):
        
        gltf_name = self.get_gltf().get_gx_gltf_name()
        
        texcoord_0 = self.primitives[0].get_TEXCOORD_0()
        texcoord_0_type =  Buffer.enums[texcoord_0.componentType][0]
        texcoord_0_unit =  texcoord_0.type
        
        normal = self.primitives[0].get_NORMAL()
        normal_type =  Buffer.enums[normal.componentType][0]
        normal_unit =  normal.type

        position = self.primitives[0].get_POSITION()
        position_type =  Buffer.enums[position.componentType][0]
        position_unit =  position.type
        
        return  {'generator'   :'gen_shared_normal__position__texcoord_0',
                 'gltf'        : gltf_name,
                 'name'        : self.dict['name'],
                 'textcoord_0' : { 'type': [texcoord_0_unit, texcoord_0_type] },
                 'normal'      : { 'type': [normal_unit, normal_type] },
                 'position'    : { 'type': [position_unit, position_type] },
                 }

    def gen_cloned_normal__position__texcoord_0(self):
        gltf_name = self.get_gltf().get_gx_gltf_name()
        return  {'generator':'gen_cloned_normal__position__texcoord_0',
                 'gltf'     : gltf_name,
                 'name'     : self.dict['name'],
                }

    def gen_cpp_POSITION_TEXCOORD_0_NORMAL(self, text):
        text << "[u'POSITION', u'TEXCOORD_0', u'NORMAL']"

class Gltf(schema.Gltf):
    def __init__(self, file_path):      # print("++", self)
        self.asset       = {}
        self.meshes      = []
        self.animations  = []
        self.skins       = []
        self.materials   = []
        self.textures    = []
        self.samplers    = []
        self.cameras     = []
        self.images      = []
        self.accessors   = []
        self.buffers     = []
        self.bufferViews = []
        self.scene       = 0            # gltf scene index in self.scenes
        self.scenes      = []           # self scenes (each contain nodes list)
        self.nodes       = []           # self nodes tree
        self.path        = file_path
        self.buff        = json.loads(file(file_path, "r").read())
        for i in self.buff:
            # print(i)
            m_name = "parse_%s" % i
            if hasattr(self, m_name):
                m = getattr(self, m_name)
                if callable(m):
                    m.__call__(self.buff[i])
            else:
                if hasattr(self, "_%s" % m_name):
                    print(" - %s disabled" % i)
                else:
                    print(" ! %s UNSUPPORTED" % i)

    def __del__(self): pass # print("--", self)

    @staticmethod
    def get_gltf_keys():
        return ['asset', 'meshes', 'animations', 'skins', 'materials',
                'textures', 'samplers', 'images', 'generator', 'version',
                'accessors', 'buffers', 'bufferViews', 'scene', 'scenes',
                'nodes']

    def get_gx_gltf_name(self):
        return os.path.split(os.path.splitext(self.path)[0])[1].lower()

    def parse_asset(self, subj):
        self.asset = subj

    def parse_accessors(self, subj):
        for j in subj:
            self.accessors.append(Accessor(j).set_gltf(self))

    def parse_buffers(self, subj):
        for j in subj:
            self.buffers.append(Buffer(j).set_gltf(self))

    def parse_bufferViews(self, subj):
        for j in subj:
            self.bufferViews.append(BufferView(j).set_gltf(self))

    def parse_scene(self, subj):
        self.scene = subj
    
    def parse_scenes(self, subj):
        for j in subj:
            self.scenes.append(Scene(j).set_gltf(self))
    
    def parse_nodes(self, subj):
        for j in subj:
            self.nodes.append(Node(j).set_gltf(self))

    def parse_meshes(self, subj):
        for i in subj:
            self.meshes.append(Mesh(i).set_gltf(self))

    def parse_materials(self, subj):
        for i in subj:
            self.materials.append(Material(i).set_gltf(self))

    def parse_textures(self, subj):
        for i in subj:
            self.textures.append(Texture(i).set_gltf(self))

    def parse_animations(self, subj):
        for i in subj:
            self.animations.append(Animation(i).set_gltf(self))

    def parse_images(self, subj):
        for i in subj:
            self.images.append(Image(i).set_gltf(self))

    def parse_skins(self, subj):
        for i in subj:
            self.skins.append(Skin(i).set_gltf(self))

    def parse_samplers(self, subj):
        for i in subj:
            self.samplers.append(Sampler(i).set_gltf(self))
            
    def parse_cameras(self, subj):
        for i in subj:
            self.cameras.append(Camera(i).set_gltf(self))
        


if __name__ == '__main__':
    gltf = Gltf("C:/WORK/EXP61/devicea/gx_gltf_test/BoxTextured.gltf")
    #gltf = Gltf("C:/work/EXP61/devicea/gx_fbx_test/Nikita.gltf")
    
    for mesh in gltf.meshes:
        vertex_type = ""
        vertex_attr = mesh.get_attributes()
        sorted_attr = sorted(vertex_attr)
        gen_shared = ('gen_shared_'+'__'.join(sorted_attr)).lower()
        gen_cloned = ('gen_cloned_'+'__'.join(sorted_attr)).lower()
        gen_method = getattr(mesh, gen_shared)
        pprint( gen_method.__call__() )
        gen_method = getattr(mesh, gen_cloned)
        pprint( gen_method.__call__() )
        #pdb.set_trace()
        
    
    # # CLASSES
    # import inspect
    # 
    # export = [ locals()[i] for i in dir() if inspect.isclass(locals()[i]) and issubclass(locals()[i], schema.Schema)]
    # export = sorted(export)
    # 
    # for cls in export:
    #     print cls
    # # DEPLOY 
    # # print( dag.gltf.get_gx_gltf_name() )
