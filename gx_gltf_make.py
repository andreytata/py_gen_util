#!/usr/bin/env python
# coding: utf-8

import sys, weakref, itertools

from gx_gltf_root import Gltf

class DagTree(object):
    def __init__(self, gltf):
        # print("++DagTree %X" % id(self))
        self.nest = {}
        self.gltf = gltf
        self.list = []                           # weak refs each dag-node in tree
        for n in gltf.scenes[gltf.scene].nodes:
            node = gltf.nodes[n]
            dag_node = DagNode(self, node, self)
            self.nest[node.name] = dag_node
            self.list.append(weakref.ref(dag_node))
    
    def __del__(self):
        pass
        # print("--DagTree 0x%X" % id(self))
        
    def get_gates(self):
        return [i().get_path() for i in self.list]
    
    def get_nodes(self):
        return [i() for i in self.list ]
    
    def get_skinned(self):
        return [i() for i in self.list if hasattr(i().node, 'skin')]
        
    def get_meshes(self):
        return [i() for i in self.list if hasattr(i().node,'mesh') and not hasattr(i().node, 'skin')]
    
    def get_transforms(self):
        return [i() for i in self.list if not hasattr(i().node,'mesh') and not hasattr(i().node, 'skin')]
    
    def pp_meshes(self):
        print("Meshes:\n  %s" % "\n  ".join([ i.get_path() for i in dag.get_meshes()]))

    def pp_skinned(self):
        print("Skinnned:\n  %s" % "\n  ".join([ i.get_path() for i in dag.get_skinned()]))
        
    def pp_transforms(self):
        print("Transforms:\n  %s" % "\n  ".join([ i.get_path() for i in dag.get_transforms()]))


class DagNode(object):
    def __init__(self, root, node, prev):
        # print("++DagNode %s %s" % (node, prev))
        self.root = weakref.ref(root)            # weakref to DAG tree root
        self.prev = weakref.ref(prev)            # weakref to parent node
        self.node = node                         # wrapped GltfNode based item
        self.nest = {}                           # dict of the DagNode instances
        setattr(self.node, 'abs_path', self.get_path())
        if hasattr(node, 'children'):
            for n in node.children:
                curr = self.root().gltf.nodes[n]
                wrapper = DagNode( self.root(), curr, self )
                self.nest[curr.name] = wrapper
                self.root().list.append(weakref.ref(wrapper))
        self.interface = ['gx_tran']             # Can be rotated and translated with all inner sub-nodes
        if hasattr(node, 'skin'):
            # so, contain mesh, skin, joints, inverse-bind-pos-matrix, WEIGHTS_* & JOINTS_* attributes, etc.
            self.interface.append('gx_skin')     # Can be used with run-time skeleton-based deformations.
            self.interface.append('gx_mesh')     # And can be used w/o any skeleton-based deformations.
            self.build_skin_interface()
        elif hasattr(node, 'mesh'):
            # so, contain mesh only, w/o skin, joints, weights, etc.
            self.interface.append('gx_mesh')     # and can be used w/o any deformations
            self.build_mesh_interface()

    def build_mesh_interface(self):
        pass

    def build_skin_interface(self):
        pass

    def __del__(self):
        pass
        # print("--DagNode %X" % id(self))
        
    def get_path(self):
        path = []
        curr = self
        while curr.__class__ != DagTree:
            path.insert(0, curr.node.name)
            curr = curr.prev()
        return str(bytearray( map(ord,"/".join(path) )))

    def pprint(self, head = ""):
        print("%s%s at %s %s" % (head, self.node.__class__.__name__, "%08X"% id(self), self.get_path()))
        print("%s%s%s" % (head, "|", self.interface))
        gltf_keys = sorted(self.node.dict.keys())
        for i in gltf_keys:
            print("%s--%-16s : %s" % (head, i, self.node.dict[i]))
        return self
    
    def get_cloned_dict(self, shared):
        u""" Цель данного обхода по графу GLTF узлов, сгенерировать JSON управляющий строительством узлов
        в графе сцены. По узлу на каждый трансформ, вне зависимости от содержимого узла. Эти узлы будут
        содержать инстанции UNIFORM аттрибутов и ссылки на разделяемые материалы и скинкластеры. Самый
        примитивный скинкластер не содержит костей, отображается только как mesh. Для сохранения данных
        о линковке между узлами, применяется внутренняя url-подобная адресация узлов, в которой атрибуты
        вершин и разделяемая информация о вершинном шейдере располагается в ветке:
        $gui/glsl/gltf/Имя_файла/Имя_Скинкластера
        
        - инстанции индивидуальных Cloned Views, будут разбросаны по веткам словарь-подобных узлов сцены
        $gui/gdom/scene/node_name/node_name/.../target_node
        
        Главное здесь разделить каждый граф GLTF на граф разделяемых ресурсов SHARED_VIEW и CLONED_VIEW
        При этом, в состав SHARED_VIEW, будет входить текст содержащий инстанцию CLONED_VIEW
        Each Clone-must have pointer to self installation node to find pointers to each self joint node.
        Each Skin-cloned collect pointers to self joints, and contain pointer to Skin-shared data.
        Each Skin-shared data contain inverse_bind_pos only shared
        VertexData vertices[] = {
            // Vertex data for face 0
            {QVector3D(-1.0f, -1.0f,  1.0f), QVector2D(0.0f, 0.0f)},  // v0
            {QVector3D( 1.0f, -1.0f,  1.0f), QVector2D(0.33f, 0.0f)}, // v1
            {QVector3D(-1.0f,  1.0f,  1.0f), QVector2D(0.0f, 0.5f)},  // v2
            {QVector3D( 1.0f,  1.0f,  1.0f), QVector2D(0.33f, 0.5f)}, // v3
    
            // Vertex data for face 1
            {QVector3D( 1.0f, -1.0f,  1.0f), QVector2D( 0.0f, 0.5f)}, // v4
            {QVector3D( 1.0f, -1.0f, -1.0f), QVector2D(0.33f, 0.5f)}, // v5
            {QVector3D( 1.0f,  1.0f,  1.0f), QVector2D(0.0f, 1.0f)},  // v6
            {QVector3D( 1.0f,  1.0f, -1.0f), QVector2D(0.33f, 1.0f)}, // v7
    
            // Vertex data for face 2
            {QVector3D( 1.0f, -1.0f, -1.0f), QVector2D(0.66f, 0.5f)}, // v8
            {QVector3D(-1.0f, -1.0f, -1.0f), QVector2D(1.0f, 0.5f)},  // v9
            {QVector3D( 1.0f,  1.0f, -1.0f), QVector2D(0.66f, 1.0f)}, // v10
            {QVector3D(-1.0f,  1.0f, -1.0f), QVector2D(1.0f, 1.0f)},  // v11
    
            // Vertex data for face 3
            {QVector3D(-1.0f, -1.0f, -1.0f), QVector2D(0.66f, 0.0f)}, // v12
            {QVector3D(-1.0f, -1.0f,  1.0f), QVector2D(1.0f, 0.0f)},  // v13
            {QVector3D(-1.0f,  1.0f, -1.0f), QVector2D(0.66f, 0.5f)}, // v14
            {QVector3D(-1.0f,  1.0f,  1.0f), QVector2D(1.0f, 0.5f)},  // v15
    
            // Vertex data for face 4
            {QVector3D(-1.0f, -1.0f, -1.0f), QVector2D(0.33f, 0.0f)}, // v16
            {QVector3D( 1.0f, -1.0f, -1.0f), QVector2D(0.66f, 0.0f)}, // v17
            {QVector3D(-1.0f, -1.0f,  1.0f), QVector2D(0.33f, 0.5f)}, // v18
            {QVector3D( 1.0f, -1.0f,  1.0f), QVector2D(0.66f, 0.5f)}, // v19
    
            // Vertex data for face 5
            {QVector3D(-1.0f,  1.0f,  1.0f), QVector2D(0.33f, 0.5f)}, // v20
            {QVector3D( 1.0f,  1.0f,  1.0f), QVector2D(0.66f, 0.5f)}, // v21
            {QVector3D(-1.0f,  1.0f, -1.0f), QVector2D(0.33f, 1.0f)}, // v22
            {QVector3D( 1.0f,  1.0f, -1.0f), QVector2D(0.66f, 1.0f)}  // v23
        """
        cloned = dict()
        if 'gx_mesh' in self.interface:
            cloned['mesh'] = u"mesh%02d" % self.node.dict['mesh']
            shared['mesh'][self.node.dict['mesh']] = dict( name = cloned['mesh'] )
            if 'gx_skin' in self.interface:                            # skin claster case:
                cloned['type'] = u"skin"
                cloned['skin'] = u"skin%02d" % self.node.dict['skin']
                shared['skin'][self.node.dict['skin']] = dict( name = cloned['skin'] )
                joints = self.node.get_skin().get_joints()
                inverse_bind_matrices_accessor = self.node.get_skin().get_inverseBindMatrices()
                inverse_bind_matrices = inverse_bind_matrices_accessor.get_components()
                shared['skin'][self.node.dict['skin']]['joints'] = inverse_bind_matrices

                cloned['joints'] = [ j.abs_path for j in joints ]
                """
                Кости - (трансформы используемые как кости) каждая инстанция использует собственную инстанцию
                матрицы ориентации/положения в пространстве. Разделяемый скинкластер содержит 
                """
            else:                                                      # mesh_only case:
                cloned['type'] = u"mesh"
                
            
        #cloned['face'] = self.interface
        for name in self.nest:
            cloned[name] = self.nest[name].get_cloned_dict(shared)
        return cloned


# NEXT TOO CLASSES - DAG_DEEP_FIST_WALKER
#
class FileLikeObject(object):
    def __init__ ( self, out ):
        self.file_like_object = out

    def __lshift__(self, obj ):
        self.file_like_object.write(str(obj))
        return self

class DagNodePrinter(FileLikeObject):
    def __init__(self, dag_node, out, head=""):
        FileLikeObject.__init__(self, out); self.node, self.head = dag_node, head
        self << "\n" << head + ', "' + dag_node.node.name + '":\n%s{' % head
        self << "\n" << head + '  "interface":' + repr(dag_node.interface)+","
        for numb, i in enumerate(dag_node.nest):
            sub = DagNodePrinter(dag_node.nest[i], out, head + "  ")
            sub.numb = numb
            sub.size = len(dag_node.nest)

    def __del__(self):
        self << " " * len(self.head) + '},\n'

class DagTreePrinter(FileLikeObject):
    def __init__(self, dag_node, out, head=""):
        FileLikeObject.__init__(self, out);  self.node, self.head = dag_node, head
        self << head << '''{ "gltf":"//gui/glsl/gltf/%s"''' % dag_node.gltf.get_gx_gltf_name()
        self << "\n" << head << ''', "doc0":"View-Shared JSON contain instructions used in each instance of the object view"'''
        self << "\n" << head << ''', "doc1":"View-Instance JSON contain instructions how to create object's view instance"'''
        for numb, i in enumerate(dag_node.nest):
            sub = DagNodePrinter(dag_node.nest[i], out, head + "  ")
            sub.numb = numb
            sub.size = len(dag_node.nest)
            
    def __del__(self):
        self << " " * len(self.head) + '}\n'

# CREATE GXJSON FORMAT FROM GLTF DAG_TREE
#
class gxDagTree(object):
    def __init__(self, dag_tree):
        self.source = dag_tree
        self.cloned = dict()
        self.shared = dict()
        self.shared['name'] = dag_tree.gltf.get_gx_gltf_name()
        self.shared['type'] = 'gltf'
        self.shared['path'] = 'gui/glsl/gltf/' + self.shared['name']
        self.shared['mesh'] = dict()
        self.shared['skin'] = dict()
        for name in dag_tree.nest:
            self.cloned[name] = dag_tree.nest[name].get_cloned_dict(self.shared)
        for mesh_key in self.shared['mesh']:
            mesh = self.shared['mesh'][mesh_key]
            prim = self.source.gltf.meshes[mesh_key].primitives[0]
            indx_acessor = self.source.gltf.accessors[prim.indices]
            mesh['indices'] = indx_acessor.get_components()
            mesh['indices_type'] = "%s_%s" % (indx_acessor.get_type() , indx_acessor.get_component_type())
            for attr_name in prim.attributes:
                # # print attr_name
                # # pdb.set_trace()
                attr_accessor = getattr(prim, "get_%s" % attr_name).__call__()
                item_type = attr_accessor.get_type()
                comp_type = attr_accessor.get_component_type()
                comp_buff = attr_accessor.get_components()
                ts = attr_accessor.get_type_size(item_type)
                #: print item_type, comp_buff[offset:offset+type_size]
                mesh[attr_name] = [comp_buff[offset*ts:offset*ts+ts] for offset in range(0, int(len(comp_buff)/ts))]
                mesh[attr_name + '_type'] = "%s_%s" % (attr_accessor.get_type() , attr_accessor.get_component_type())
            # pdb.set_trace()

    def print_mesh(self, mesh_key):
        subj.source.gltf.meshes[mesh_key].pprint()

    def get_mesh_keys(self):
        return self.shared['mesh'].keys()

    def get_skin_keys(self):
        return self.shared['skin'].keys()
    
    def get_mesh_name(self, mesh_key):
        return self.source.gltf.meshes[mesh_key].name
    
    def get_mesh_attributes(self, mesh_key):
        prim = self.source.gltf.meshes[mesh_key].primitives[0]
        return prim.attributes.keys()

    def get_mesh_indices(self, mesh_key):
        prim = self.source.gltf.meshes[mesh_key].primitives[0]
        indx = self.source.gltf.accessors[prim.indices]
        return indx.get_components()
        
    def get_mesh_components(self, mesh_key, attr_name):
        return self.shared['mesh'][mesh_key][attr_name]

    def get_export_dict(self):
        self.shared['cloned'] = self.cloned
        return self.shared
        
    def dumps(self):
        return json.dumps(self.get_export_dict())
    
    
    def pprint(self):
        pprint(self.get_export_dict(), width=1)

    def get_interleaved_PT(self, mesh_id=0):
        outp = "{\n"
        interleaved = zip(self.shared['mesh'][mesh_id]['POSITION'], self.shared['mesh'][mesh_id]['TEXCOORD_0'])
        attr = self.shared['mesh'][mesh_id]
        for e, i in enumerate(interleaved):
            args = list(itertools.chain(i[0],i[1]))
            outp += ("{ QVector3D(%s, %s, %s), QVector2D(%s, %s) } ,\n"
                     %  tuple(itertools.chain(i[0],i[1]))
                     )
        outp+= "<END>"
        return "%d" % len(interleaved), outp.replace(",\n<END>","}\n")

    def get_interleaved_P3N3T2(self, mesh_id=0):
        outp = "{\n"
        position   = self.shared['mesh'][mesh_id]['POSITION']    # self.source.gltf.meshes. shared['mesh'][mesh_id]['POSITION']
        normal     = self.shared['mesh'][mesh_id]['NORMAL']
        texcoord_0 = self.shared['mesh'][mesh_id]['TEXCOORD_0']
        interleaved = list(zip(position, normal , texcoord_0))
        attr = self.shared['mesh'][mesh_id]
        for i in interleaved:
            outp += ("{ QVector3D(%s, %s, %s), QVector3D(%s, %s, %s), QVector2D(%s, %s) } ,\n"
                     %  tuple(itertools.chain(i[0], i[1], i[2]))
                     )
        outp+= "<END>"
        return "%d" % len(interleaved), outp.replace(",\n<END>","}\n")

    def get_interleaved_P3N3W4J4T2(self, mesh_id=0):
        outp = "{\n"
        position   = self.shared['mesh'][mesh_id]['POSITION']    # self.source.gltf.meshes. shared['mesh'][mesh_id]['POSITION']
        normal     = self.shared['mesh'][mesh_id]['NORMAL']
        weights_0  = self.shared['mesh'][mesh_id]['WEIGHTS_0']
        joints_0   = self.shared['mesh'][mesh_id]['JOINTS_0']
        texcoord_0 = self.shared['mesh'][mesh_id]['TEXCOORD_0']
        interleaved = list( zip(position, normal , weights_0, joints_0, texcoord_0) )
        attr = self.shared['mesh'][mesh_id]
        for i in interleaved:
            outp += ("{ QVector3D(%s, %s, %s), QVector3D(%s, %s, %s), QVector4D(%s, %s, %s, %s), QVector4D(%s, %s, %s, %s), QVector2D(%s, %s) } ,\n"
                     %  tuple(itertools.chain(i[0], i[1], i[2], i[3], i[4]))
                     )
        outp+= "<END>"
        return "%d" % len(interleaved), outp.replace(",\n<END>","}\n")
    
    def get_indices_PP(self, mesh_id=0):
        out = str()
        out += str( self.shared['mesh'][mesh_id]['indices'] )
        out = out.replace("[", "{")
        out = out.replace("]", "}")
        return "%d" % len(self.shared['mesh'][mesh_id]['indices']), out
                

if __name__=='__main__':
    # TEST load file
    # gltf = Gltf("C:/work/EXP61/devicea/gx_fbx_test/Slava_Model_With_Bones.gltf")
    # gltf = Gltf("C:/work/EXP61/devicea/gx_fbx_test/Cube_01.gltf")
    # gltf = Gltf("C:/work/EXP61/devicea/gx_fbx_test/cube0.gltf")
    # gltf = Gltf("C:/work/EXP61/devicea/gx_fbx_test/Slava_Rig_01.gltf")
    # gltf = Gltf("C:/work/EXP61/devicea/gx_fbx_test/Slava_Rig_2014_2015_NEW.gltf")  ## CUBE PORTED GENERATOR (CHUSEN ONE)
    # gltf = Gltf("D:/BLENDER_GAME_EXPORT/Slava_RIG_02.gltf ")
    gltf = Gltf("C:/work/EXP61/devicea/gx_fbx_test/Nikita.gltf")
    # gltf = Gltf("C:/WORK/EXP61/devicea/gx_gltf_test/BoxTextured.gltf")
    dag = DagTree(gltf)
    gx_dag_tree = gxDagTree(dag)
    
    # print ("-"*40 + "shared")
    # print ( json.dumps(gx_dag_tree.shared, indent=4) )
    # # pprint(gx_dag_tree.get_export_dict(), width=1)
    
    # print ("-"*40 + "cloned")
    # print ( json.dumps(gx_dag_tree.cloned, indent=4))
    
    # TEST build DagTree from loaded gltf file
    # dag = DagTree(nikita_gltf)
    
    # TEST use DagTreePrinter on nikita_dag
    # DagTreePrinter(dag, sys.stdout)
    
    # std::size_t           vertex_size;   // each vertex size
    # std::size_t           max_indices;   // max indices count, wait all before bind VBO
    # std::size_t           max_vertices;  // max vertices count, wait all before bind VBO
    # std::size_t           joints_count;  // uniform matrices count
    # 
    # std::vector<float>    vertices;
    # std::vector<GLushort> indices;
    #
    GEOMERTYENGINE_TEMPLATE  = """#include "geometryengine.h"
#include <QVector2D>
#include <QVector3D>
#include <QVector4D>

struct VertexData { QVector3D position; QVector3D normal; QVector2D texCoord; };
struct SkinVertex { QVector3D position; QVector3D normal; QVector4D weights_0; QVector4D joints_0; QVector2D texCoord; }

GeometryEngine::GeometryEngine() : indexBuf(QOpenGLBuffer::IndexBuffer) {
    initializeOpenGLFunctions();
    arrayBuf.create();
    indexBuf.create();
    initCubeGeometry();
}

GeometryEngine::~GeometryEngine() {
    arrayBuf.destroy();
    indexBuf.destroy();
}

void GeometryEngine::initCubeGeometry() {
    VertexData vertices[] = %%VERTEX_BUFFER%%;
    // len = %%VERTEX_COUNT%%

    GLushort indices[]    = %%INDEX_BUFFER%%;
    // len = %%INDEX_COUNT%%

    // Transfer vertex data to VBO 0
    arrayBuf.bind();
    // arrayBuf.allocate(vertices, 24 * sizeof(VertexData));
    arrayBuf.allocate(vertices, %%VERTEX_COUNT%% * sizeof(VertexData));

    // Transfer index data to VBO 1
    indexBuf.bind();
    //indexBuf.allocate(indices, 34 * sizeof(GLushort));
    indexBuf.allocate(indices, %%INDEX_COUNT%% * sizeof(GLushort));
}

void GeometryEngine::drawCubeGeometry(QOpenGLShaderProgram *program)
{
    // Tell OpenGL which VBOs to use
    arrayBuf.bind();
    indexBuf.bind();

    // Offset for position
    quintptr offset = 0;

    /// POSITION
    // Tell OpenGL programmable pipeline how to locate vertex position data
    int vertexLocation = program->attributeLocation("a_position");
    program->enableAttributeArray(vertexLocation);
    program->setAttributeBuffer(vertexLocation, GL_FLOAT, offset, 3, sizeof(VertexData));

    // Offset for texture coordinate
    offset += sizeof(QVector3D);

    /// NORMAL
    // Tell OpenGL programmable pipeline how to locate vertex position data
    int normalLocation = program->attributeLocation("a_normal");
    program->enableAttributeArray(normalLocation);
    program->setAttributeBuffer(normalLocation, GL_FLOAT, offset, 3, sizeof(VertexData));

    offset += sizeof(QVector3D);

    /// TEXCOORD_0
    // Tell OpenGL programmable pipeline how to locate vertex texture coordinate data
    int texcoordLocation = program->attributeLocation("a_texcoord");
    program->enableAttributeArray(texcoordLocation);
    program->setAttributeBuffer(texcoordLocation, GL_FLOAT, offset, 2, sizeof(VertexData));

    // Draw cube geometry using indices from VBO 1
    // glDrawElements(GL_TRIANGLE_STRIP, 34, GL_UNSIGNED_SHORT, 0);
    glDrawElements(GL_TRIANGLES, %%INDEX_COUNT%%, GL_UNSIGNED_SHORT, 0);
}
"""
    import  os, sys, tempfile, socketserver, webbrowser
    gen_path = os.path.join(tempfile.gettempdir(), "gltf_gen_path")
    if not os.path.exists(gen_path):
        os.mkdir(gen_path)
    temp_path = os.path.join(gen_path,'gltf_export_temp.txt')
    print(temp_path)
    with open(temp_path, "w") as f:
        VERTEX_COUNT , VERTEX_BUFFER = gx_dag_tree.get_interleaved_P3N3T2()
        INDEX_COUNT  , INDEX_BUFFER  = gx_dag_tree.get_indices_PP()
        GEOMERTYENGINE_TEMPLATE = GEOMERTYENGINE_TEMPLATE.replace( "%%VERTEX_BUFFER%%", VERTEX_BUFFER)
        GEOMERTYENGINE_TEMPLATE = GEOMERTYENGINE_TEMPLATE.replace(  "%%VERTEX_COUNT%%", VERTEX_COUNT)
        GEOMERTYENGINE_TEMPLATE = GEOMERTYENGINE_TEMPLATE.replace(  "%%INDEX_BUFFER%%", INDEX_BUFFER)
        GEOMERTYENGINE_TEMPLATE = GEOMERTYENGINE_TEMPLATE.replace(   "%%INDEX_COUNT%%", INDEX_COUNT)
        f.write( GEOMERTYENGINE_TEMPLATE )    # bpy.data.filepath
    print("<FINISHED> %s " % temp_path )
    
    # OPEN RESULT USING WEB-BROWSER:
    # if sys.version_info[:2] > (2,7):         # Python 3
    #     import http.server as http_server
    #     from urllib.request import urlopen
    # else:                                    # Pyhton 2
    #     import SimpleHTTPServer as http_server
    #     from urllib2 import urlopen
    # os.chdir(gen_path)
    #
    # def save_attributes( path, gx_dag ):
    #     for NAME in [] get_attributes()
    #         
    #     with open(os.path.join(gen_path, "POSITION.js"), "w") as f:
    #         position   = gx_dag_tree.shared['mesh'][mesh_id]['POSITION']    # self.source.gltf.meshes. shared['mesh'][mesh_id]['POSITION']
    #         normal     = gx_dag_tree.shared['mesh'][mesh_id]['NORMAL']
    #         texcoord_0 = gx_dag_tree.shared['mesh'][mesh_id]['TEXCOORD_0']
    # 
    #         f.write("Hello POSITIONS")
    # if not True:    
    #     httpd = socketserver.TCPServer(("", 4680), http_server.SimpleHTTPRequestHandler)
    #     print("Serving At Port", 4680)
    #     webbrowser.open( "http://127.0.0.1:%s" % 4680 )
    #     httpd.serve_forever()
    # else:
    #     subj = gx_dag_tree