#!/usr/bin/env python
# coding: utf-8

"""Generate single qmake pri project from glTF2.0 export file.
Include classes used for build one Generation GAP's component.
from gx_cpp_glsl.py import QtGltfBuiltinPri as GenPri
pri = QtGltfBuiltinPri( namespace_name
                , input_gltf_file_path
                , output_folder_path
                , output_project_file_path )
pri.generate()
"""

import sys, os, re, json, weakref
from gx_gltf_make import (Gltf, DagTree, gxDagTree)


gx_gen_pri_hpp_file_template = """#ifndef GX_GENERATED_%%get_name_upper%%_H
#define GX_GENERATED_%%get_name_upper%%_H

#include <gx_gap_interface.h>

namespace geom { namespace %%get_name_lower%% {
    GeometryComponent* get_scene_root();
%%get_class_list%%
    // GEN GAP INTERFACE'S STATIC-ALLOCATED TRANSFORM-NODE POINTER, BUT WITH GeometryEngine*
    // 
}}  //end namespace geom::%%get_name_lower%%

#endif // GX_GENERATED_%%get_name_upper%%_H
"""

gx_gen_pri_cpp_file_template = u"""// WARNING! AUTO-GENERATED AT PRE-COMPILATION STEP ( like *.MOC )
#include<%%get_hpp_file_name%%>
GeometryComponent* geom::%%get_name_lower%%::get_scene_root() { return nullptr; }

%%get_method_definitions%%
"""


geometry_methods_definitin_template = u"""
void geom::%%get_pri_namespace%%::%%get_class_name%%::initGeometry()
{
    %%get_vertex_data_class_name%% vertices[] =
        #include <%%get_vbo_file_name%%>
    ; // len = %%get_vbo_len%% ( example 8164 ) is vertices count, not floats 

    GLushort indices[]    = 
        #include <%%get_ibo_file_name%%>
    ; // len = %%get_ibo_len%% ( example 47733 )

    // Transfer vertex data to VBO 0
    arrayBuf.bind();
    arrayBuf.allocate(vertices, %%get_vbo_len%% * %%get_vertex_size%% );

    // Transfer index data to VBO 1
    indexBuf.bind();
    indexBuf.allocate(indices, %%get_ibo_len%% * sizeof(GLushort));
}
"""

geometry_methods_mesh_draw_template = u"""
int geom::%%get_pri_namespace%%::%%get_class_name%%::get_vertex_size()
{
    return sizeof(MeshVertexData);
}

void geom::%%get_pri_namespace%%::%%get_class_name%%::drawGeometry(QOpenGLShaderProgram *program)
{
    if (need_gpu_upload) {
        initGeometry();
        need_gpu_upload = false;
    }

    // Tell OpenGL which VBOs to use
    arrayBuf.bind();
    indexBuf.bind();
    /*
    %%get_joints%%
    */

    // Offset for position
    quintptr offset = 0;

    /// POSITION
    // Tell OpenGL programmable pipeline how to locate vertex position data
    int vertexLocation = program->attributeLocation("a_position");
    program->enableAttributeArray(vertexLocation);
    program->setAttributeBuffer(vertexLocation, GL_FLOAT, offset, 3, sizeof(MeshVertexData));

    // Offset for "normal" 
    offset += sizeof(QVector3D);

    /// NORMAL
    // Tell OpenGL programmable pipeline how to locate vertex position data
    int normalLocation = program->attributeLocation("a_normal");
    program->enableAttributeArray(normalLocation);
    program->setAttributeBuffer(normalLocation, GL_FLOAT, offset, 3, sizeof(MeshVertexData));

    // Offset for "texture coordinate"
    offset += sizeof(QVector3D);

    /// TEXCOORD_0
    // Tell OpenGL programmable pipeline how to locate vertex texture coordinate data
    int texcoordLocation = program->attributeLocation("a_texcoord");
    program->enableAttributeArray(texcoordLocation);
    program->setAttributeBuffer(texcoordLocation, GL_FLOAT, offset, 2, sizeof(MeshVertexData));

    // Draw cube geometry using indices(IBO) from VBO 1
    // glDrawElements(GL_TRIANGLE_STRIP, 34, GL_UNSIGNED_SHORT, 0);
    glDrawElements(GL_TRIANGLES, %%get_ibo_len%%, GL_UNSIGNED_SHORT, 0);
}
"""

geometry_methods_skin_draw_template = u"""
int geom::%%get_pri_namespace%%::%%get_class_name%%::get_vertex_size()
{
    return sizeof(SkinVertexData);
}

void geom::%%get_pri_namespace%%::%%get_class_name%%::drawGeometry(QOpenGLShaderProgram *program)
{
    if (need_gpu_upload) {
        initGeometry();
        need_gpu_upload = false;
    }

    // Tell OpenGL which VBOs to use
    arrayBuf.bind();
    indexBuf.bind();
    /*
    %%get_joints%%
    */
    // Offset for position
    quintptr offset = 0;

    /// int attribute_location, QString attribute_name location
    /// POSITION
    // Tell OpenGL programmable pipeline how to locate vertex position data
    int vertexLocation = program->attributeLocation("a_position");
    program->enableAttributeArray(vertexLocation);
    program->setAttributeBuffer(vertexLocation, GL_FLOAT, offset, 3, sizeof(SkinVertexData));

    // Offset for normal vector
    offset += sizeof(QVector3D);

    /// NORMAL
    // Tell OpenGL programmable pipeline how to locate normal vector data
    int normalLocation = program->attributeLocation("a_normal");
    program->enableAttributeArray(normalLocation);
    program->setAttributeBuffer(normalLocation, GL_FLOAT, offset, 3, sizeof(SkinVertexData));

    offset += sizeof(QVector3D);

    /// WEIGHTS_0
    // Tell OpenGL programmable pipeline how to locate joint's WEIGHTS_0 vec4 data
    int weights_0_location = program->attributeLocation("a_weights_0");
    program->enableAttributeArray(weights_0_location);
    program->setAttributeBuffer(weights_0_location, GL_FLOAT, offset, 4, sizeof(SkinVertexData));

    offset += sizeof(QVector4D);

    /// JOINTS_0
    // Tell OpenGL programmable pipeline how to locate joint's WEIGHTS_0 vec4 data
    int joints_0_location = program->attributeLocation("a_joints_0");
    program->enableAttributeArray(joints_0_location);
    program->setAttributeBuffer(joints_0_location, GL_FLOAT, offset, 4, sizeof(SkinVertexData));

    offset += sizeof(QVector4D);

    /// TEXCOORD_0
    // Tell OpenGL programmable pipeline how to locate vertex texture coordinate data
    int texcoordLocation = program->attributeLocation("a_texcoord");
    program->enableAttributeArray(texcoordLocation);
    program->setAttributeBuffer(texcoordLocation, GL_FLOAT, offset, 2, sizeof(SkinVertexData));

    // Draw cube geometry using indices from VBO 1
    // glDrawElements(GL_TRIANGLE_STRIP, 34, GL_UNSIGNED_SHORT, 0);
    glDrawElements(GL_TRIANGLES, 47733, GL_UNSIGNED_SHORT, 0);
}
"""

class QtTemplate:
    def __init__(self, self_pri, mesh_key):
        # print("++%s" % self)
        self.weak_pri = weakref.ref(self_pri)
        self.mesh_key = mesh_key
        self.slots = []
        self.variables = {}  # Individual programm variables sended before draw
                             # It is some sloned skin part, depend "gltf" scene
                             # texture, matrix, view-transformations e.t.c.
        """This kind of variables maybe connected on disconnected from self data-source.
        For example, some transformation matrix must be sended to GLSL programm before draw,
        is hardcoded in vertex shader code, but has no data source yet. In this case shared
        copy of the initial "GLTF" value must be connected to "disconnected" transformation.
        So, copy of all default values must be stored at shared side and initially connected
        to cloned variable node (animation port) as data source. Before some value sended to
        from animation data (initial position).  
        """

    # def __del__           (self):        print("--%s" % self)

    def __call__ ( self, match ): return str(getattr(self, match.groups()[0])())
    def get_name          (self): return self.weak_pri().gxt.get_mesh_name(self.mesh_key).replace(" ", "___")
    def get_name_lower    (self): return self.get_name().lower()
    def get_name_upper    (self): return self.get_name().upper()
    def get_pri_namespace (self): return self.weak_pri().get_name_lower()
    
    def gen_public_slots  (self):
        buff = "//PUBLIC SLOTS\n"
        for i in self.slots:
            buff += i.generate(self)
        return buff
    
    def get_methods_definition_template(self):
        return "/*get_methods_definition_template undefined in %s*/" % repr(self)
    
    def get_methods_body(self):
        return re.sub("%%(\\w+)%%", self, self.get_methods_definition_template())

    def gltf(self):
        return self.weak_pri().gxt.source.gltf

class QtGpuSkin(QtTemplate):
    class_template = """
    class %%get_class_name%%: public geom::QtGpuSkin
    {
    public:
        virtual void drawGeometry(QOpenGLShaderProgram *program);
        virtual void initGeometry();
        virtual int get_vertex_size();
        const char* get_vbo_signature() { return "%%gen_signature%%"; }
    };
    """
    glsl_vertex_attribute = dict(
        P3 = ( 'vec4' , 'a_position'  , 'QVector3D' ),
        N3 = ( 'vec4' , 'a_normal'    , 'QVector3D' ),
        T2 = ( 'vec2' , 'a_texCoord0' , 'QVector2D' ),
    )
    attributes = []
    slots = []
    changed = True
    def gen_signature        (self): return "".join(['P3','N3','W4','J4','T2'])
    def get_class_name       (self): return "%s_shared" % self.get_name_lower()
    def get_class_definition (self): return re.sub("%%(\\w+)%%", self, self.class_template)
    def get_vbo_file_name    (self): return "vbo_%s.inc" % self.get_name_lower()
    def get_vbo_len          (self): return "%s" % self.vertices
    def get_vbo_file_body    (self): return "%s" % self.vbo
    def get_ibo_file_name    (self): return "ibo_%s.inc" % self.get_name_lower()
    def get_ibo_len          (self): return "%s" % self.indices
    def get_ibo_file_body    (self): return "%s" % self.ibo
    def get_vertex_data_class_name(self) : return "SkinVertexData"
    def get_vertex_size      (self): return "sizeof(%s)" % self.get_vertex_data_class_name()
    def get_methods_definition_template(self):
        defs = list()
        defs.append("//%s\n"%repr(self))
        defs.append( geometry_methods_definitin_template )
        defs.append( geometry_methods_skin_draw_template )
        return "\n".join(defs)

    def get_joints(self):
        """skin has joints, but first path in jonints list is skinned mesh position in scene graph.
        Each next path, is gxt-path to joint used in this skin-claster. Joint can be placed in joint
        and all joints can be inserted in "skeleton" node (has no real examle for this case, yet) 
        skinned[n][0] - the name of the node with number 'n'
        skinned[n][1] - mesh number in meshes
        skinned[n][3] - skin number in GLTF's skins 
        """
        skinned = self.gltf_skinned()
        for n in skinned:
            if skinned[n][1] == self.mesh_key:
                break
        ## mesh = self.gltf().meshes [ skinned[n][1] ]
        ## bind-positions collect from skin's inverse bind matrices
        ## joints positions collect from skin's joints (as nodes) dyip
        skin = self.gltf().skins  [ skinned[n][2] ]
        jpl = {}
        for e, j in enumerate(skin.joints):
            jpl[e] = getattr(self.gltf().nodes[j], "abs_path")    
        path = getattr(self.gltf().nodes[n],"abs_path")
        return repr(skin) + "'%s'"%path  + repr(jpl)
    
    def gltf_skinned(self):
        if not hasattr(self, "skinned"):
            skinned = {}
            for e, node in enumerate(self.gltf().nodes):
                if hasattr(node, "skin"):
                    skinned[e] = [ node.name, node.mesh, node.skin ]  
            setattr(self, "skinned", skinned)
        return getattr(self, "skinned" )


class QtGpuMesh(QtTemplate):
    template = """
    class %%get_class_name%%: public geom::QtGpuMesh
    {
    public:
        virtual void drawGeometry(QOpenGLShaderProgram *program);
        virtual void initGeometry();
        virtual int get_vertex_size();
        const char* get_vbo_signature() { return "%%gen_signature%%"; }
//    public slots:
//        %%gen_public_slots%%
    };
    """
    glsl_vertex_attribute = dict(
        P3 = ( 'vec4' , 'a_position'  , 'QVector3D' ),
        N3 = ( 'vec4' , 'a_normal'    , 'QVector3D' ),
        T2 = ( 'vec2' , 'a_texCoord0' , 'QVector2D' ),
    )
    attributes = []
    slots = []
    changed = True
    def set_mesh_sources(self, PWD, GTX, KEY, VBO, vertices, IBO, indices ):
        self.name = GTX.source.gltf.path

    def gen_signature        (self): return "".join(['P3','N3','T2'])
    def get_class_name       (self): return "%s_shared" % self.get_name_lower()
    def get_class_definition (self): return re.sub("%%(\\w+)%%", self, self.template)
    def get_vbo_as_cpp_code  (self): return "/*get_vbo_as_cpp_code*/"
    def get_vertex_data_class_name(self) : return "MeshVertexData"
    def get_vertex_size      (self): return "sizeof(%s)" % self.get_vertex_data_class_name()

    def get_joints(self):
        """mesh has no joints, but has self set of the view transformations:
        Is only one string ( slash separated path ), where each chain is gxt - node's name
        """
        buff = {}
        nodes = self.gltf().nodes
        for e, n in enumerate(nodes):
            if hasattr(n, "mesh") and (n.mesh == self.mesh_key):
                buff[e] = (e,getattr(n,"abs_path"), self.get_name())
        return "MESH AT"+ repr(buff)

    def generate(self, context):
        if self.changed:
            context.get_name()
            self.changed = False

    def pprint(self, out = sys.stdout):
        out.write("Hello .pprint Method%s" % self)

    def get_vbo_file_name   (self): return "vbo_%s.inc" % self.get_name_lower()
    def get_vbo_len         (self): return "%s" % self.vertices
    def get_vbo_file_body   (self): return "%s" % self.vbo
    def get_ibo_file_name   (self): return "ibo_%s.inc" % self.get_name_lower()
    def get_ibo_len         (self): return "%s" % self.indices
    def get_ibo_file_body   (self): return "%s" % self.ibo

    def get_methods_definition_template(self):
        defs = list()
        defs.append("//%s\n"%repr(self))
        defs.append( geometry_methods_definitin_template )
        defs.append( geometry_methods_mesh_draw_template )
        return "\n".join(defs)

class QtGltfBuiltinPri:
    """ Single QT-PRI project from glTF2.0 Resource Generator"""
    pri_file_template = """# Auto-Generated Built-in Namespace "geom::%%get_name_lower%%::"
# Source at "%%get_src_file_path%%"
# Usage:
#   include(../gx_gen_%%get_name_lower%%/gx_gen_%%get_name_lower%%.pri)

!contains ( INCLUDEPATH, $$PWD ) {
  HEADERS     += $$PWD/%%get_hpp_file_name%%
  SOURCES     += $$PWD/%%get_cpp_file_name%%
  INCLUDEPATH += $$PWD
  include($$PWD/../gx_gap_base/gx_gap_base.pri)
}
"""
    hpp_file_template = gx_gen_pri_hpp_file_template
    cpp_file_template = gx_gen_pri_cpp_file_template

    def __init__(self, NAME, SRC, DST, PRI):
        self.class_defs = []
        self.name     = NAME
        self.src_gltf = SRC  # normal absolute path to source file
        self.out_dir  = DST  # normal absolute path to destination folder
        self.out_pri  = PRI  # normal absolute path to qt project include file
        self.out_md5  = self.out_pri + '.builtin'
        print('')

    def __call__   (self, match): return str(getattr(self, match.groups()[0])())

    def get_src_file_path (self): return self.src_gltf

    def get_name          (self): return self.name
    def get_name_lower    (self): return self.get_name().lower()
    def get_name_upper    (self): return self.get_name().upper()

    def get_hpp_file_name (self): return "gx_gen_%s.h" % self.get_name_lower()
    def get_hpp_file_path (self): return os.path.abspath(os.path.join(self.out_dir, self.get_hpp_file_name()))
    def get_hpp_file_body (self): return re.sub("%%(\\w+)%%", self, self.get_hpp_file_form())
    def get_hpp_file_form (self): return self.hpp_file_template

    def get_cpp_file_name (self): return "gx_gen_%s.cpp" % self.get_name_lower()
    def get_cpp_file_path (self): return os.path.abspath(os.path.join(self.out_dir, self.get_cpp_file_name()))
    def get_cpp_file_body (self): return re.sub("%%(\\w+)%%", self, self.get_cpp_file_form())
    def get_cpp_file_form (self): return self.cpp_file_template

    def get_pri_file_body (self): return re.sub("%%(\\w+)%%", self, self.pri_file_template)

    def get_class_list (self) :
        class_definitions = []
        for gen_class in self.class_defs:
            class_definitions.append( gen_class.get_class_definition() )
        return "".join(class_definitions)

    def generate(self):
        STORED_MD5 = {}
        try:
            with open(self.out_pri + ".builtins", "r") as f:
                STORED_MD5 = json.loads(f.read())['MD5']
        except IOError   : print("GENERATE: '.builtins' file not found")
        except KeyError  : print("GENERATE, 'md5' not stored in '.builtins' file")
        except ValueError: print("GENERATE, '.builtins' file invalid")

        #!!!TODO: if each stored-md5 equal current md5 => return, else rebuild all
        for i in STORED_MD5:
            print(i, STORED_MD5[i])
        self.rebuild_all()
    
    def rebuild_all(self):
        pri_file_body = self.get_pri_file_body()
        print(pri_file_body)
        print("GENERATE: generate %s" % self.out_dir )
        gltf = Gltf(self.src_gltf)
        dag  = DagTree(gltf)
        self.gxt = gxDagTree(dag)
        print("  skin count %d" % len(gltf.skins))
        print("  mesh count %d" % len(gltf.meshes))
        print("  mtrl count %d" % len(gltf.materials))
        mesh_keys = set(self.gxt.get_mesh_keys())
        for mesh_key in mesh_keys:
            vertex_attributes =  self.gxt.get_mesh_attributes(mesh_key)
            mode = ('mesh', 'skin') [ u'WEIGHTS_0' in vertex_attributes ]
            print("  %s[%s] %s %s" % (mode, mesh_key, self.gxt.get_mesh_name(mesh_key), vertex_attributes))
            if mode == 'skin':
                self.generate_skin_source(mesh_key)
            else:
                self.generate_mesh_source(mesh_key)
        gen_h_buff = self.get_hpp_file_body()
        print( gen_h_buff )
        ## At last all class-generators stored in self.class_defs list
        ## Re-create pri-file
        pass
        print(self.out_pri)
        print(self.out_dir)
        #import pdb
        #pdb.set_trace()
        with open(self.out_pri, "w") as pri:
            pri.write(self.get_pri_file_body())
        with open(self.get_cpp_file_path(),"w") as cpp:
            cpp.write(self.get_cpp_file_body())
        with open(self.get_hpp_file_path(),"w") as hpp:
            hpp.write(self.get_hpp_file_body())
        for surface_class in self.class_defs:
            vbo_file_path = os.path.join(self.out_dir, surface_class.get_vbo_file_name())
            with open(vbo_file_path, "w") as vbo_inl:
                vbo_inl.write(surface_class.get_vbo_file_body())
            ibo_file_path = os.path.join(self.out_dir, surface_class.get_ibo_file_name())
            with open(ibo_file_path, "w") as ibo_inl:
                ibo_inl.write(surface_class.get_ibo_file_body())
        # print(self.get_hpp_file_path())

    def get_vertex_signature(self, mesh_key):
        signature = ''
        vertex_attributes =  self.gxt.get_mesh_attributes(mesh_key)
        if u'POSITION'   in vertex_attributes: signature += 'P3'
        if u'NORMAL'     in vertex_attributes: signature += 'N3'
        if u'WEIGHTS_0'  in vertex_attributes: signature += 'W4'
        if u'JOINTS_0'   in vertex_attributes: signature += 'J4'
        if u'TEXCOORD_0' in vertex_attributes: signature += 'T2'
        return signature

    def generate_skin_source(self, mesh_key):
        print("  SKIN[%d] %s" % ( mesh_key, self.gxt.get_mesh_name(mesh_key) ) )
        skin=QtGpuSkin(self, mesh_key)
        self.class_defs.append(skin)  ## ADDING SKIN CLASS GENERATOR TO SCOPE
        method_name = 'get_interleaved_'  + self.get_vertex_signature( mesh_key )
        method = getattr( self.gxt, method_name )
        skin.vertices, skin.vbo = method( mesh_key )
        skin.indices, skin.ibo = self.gxt.get_indices_PP( mesh_key )
        print("  %s" % repr( ( skin.vertices, len(skin.vbo), skin.indices, len(skin.ibo) ) ) )

    def generate_mesh_source(self, mesh_key):
        """Generate h and cpp file additional objects:
        First method, each primitive create self own .h file for each primitive.
        Use namespac e, to separate generated geometry primitives, one from other.
        Use scene name as "namespace" for all this scene geometry, camera, e.t.c.
        """
        print("  MESH[%d] %s" % ( mesh_key, self.gxt.get_mesh_name(mesh_key) ) )
        mesh=QtGpuMesh(self, mesh_key)
        self.class_defs.append(mesh)  ## ADDING MESH CLASS GENERATOR TO SCOPE
        method_name = 'get_interleaved_'  + self.get_vertex_signature( mesh_key )
        method = getattr(self.gxt, method_name)
        mesh.vertices, mesh.vbo = method( mesh_key )
        mesh.indices, mesh.ibo = self.gxt.get_indices_PP( mesh_key )
        print("  %s" % repr( ( mesh.vertices, len(mesh.vbo), mesh.indices, len(mesh.ibo) ) ) )

    def get_method_definitions(self):
        buff = ""
        # call tree node's each sub-tree (so each sub can call own sub-tree)
        for surface_class in self.class_defs:
            buff += "%s\n" % surface_class.get_methods_body()
        return buff


if __name__ =='__main__':
    test = QtGltfBuiltinPri('slava_rig_2014_2015_new'
        , '../gx_gen_slava_rig_2014_2015_new/Slava_Rig_2014_2015_NEW.gltf'
        , '../gx_gen_slava_rig_2014_2015_new'
        , '../gx_gen_slava_rig_2014_2015_new/gx_gen_slava_rig_2014_2015_new.pri'
    )
    test.generate()
    
    for geom in test.class_defs:
        print(geom.get_joints())
    # dag = test.class_defs[0].weak_pri().gxt.source.gltf.nodes
    # print( "TYPE %s" % type( dag ) )
    # gltf = test.class_defs[0].weak_pri().gxt.source.gltf
    # print(test.class_defs[0].weak_pri().gxt.source.gltf.nodes)
    # import pdb
    # pdb.set_trace()

