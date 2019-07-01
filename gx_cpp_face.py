import os, sys, re

gx_inf_face_template = """{ "type": "%%%%"
, "name": "%%get_name%%"
, "path": "%%get_path%%"
}"""

gx_hpp_face_template = """
#ifndef %%get_name_upper%%_H
#define %%get_name_upper%%_H

#include <QOpenGLFunctions>
#include <QOpenGLShaderProgram>
#include <QOpenGLBuffer>
#include <QVector2D>
#include <QVector3D>
#include <QVector4D>
#include <QObject>

namespace geom
{
    class AbstractFactory: virtual public QObject
    {
        Q_OBJECT
    public:
        AbstractFactory(){}
        virtual ~AbstractFactory(){}
    };

    class GENERATED_FACTORY;
}

struct MeshVertexData {  // P3N3T2
    QVector3D position;
    QVector3D normal;
    QVector2D texCoord;
};

struct SkinVertexData {  // P3N3W4J4T2
    QVector3D position;
    QVector3D normal;
    QVector4D weights_0;
    QVector4D joints_0;
    QVector2D texCoord;
};

class GeometryEngine : protected QOpenGLFunctions
{
public:
    GeometryEngine();
    virtual ~GeometryEngine();
    virtual int get_indices_count();
    virtual int get_vertices_count();
    virtual int get_vertex_size();
    virtual void drawGeometry(QOpenGLShaderProgram *program);
    virtual void initGeometry();

protected:
    QOpenGLBuffer arrayBuf;
    QOpenGLBuffer indexBuf;
    bool need_gpu_upload = true;
};

namespace geom {

    class QtGpuMesh : public GeometryEngine
    {
    public:
        QtGpuMesh(){}
        virtual ~QtGpuMesh(){}
        // GeometryEngine:: : virtual void drawGeometry(QOpenGLShaderProgram *program);
        // GeometryEngine:: : virtual void initGeometry();
        // GeometryEngine:: : virtual int get_vertex_size();
    };

    class QtGpuSkin : public GeometryEngine
    {
    public:
        QtGpuSkin(){}
        virtual ~QtGpuSkin(){}
        virtual void drawGeometry(QOpenGLShaderProgram *program);
        // GeometryEngine:: : virtual void  initGeometry();
        // GeometryEngine:: : virtual int  GeometryEngine :: get_vertex_size();
    };

    class view
    {
    public:
        virtual ~view(){}
    };

    class vars: public view
    {
        std::map<QString, view*> context;
    public:
        vars(){}
        virtual ~vars(){}
    };

    class node: public view
    {
        std::map<QString, view*> context;
        //
    public:
        node(){}
        ~node(){}
    public:
        void new_node(const QString&){}
        void del_node(const QString&){}
        // void success(actor&);
    };
}

#endif  //%%get_name_upper%%_H
"""
gx_cpp_face_template = """
#include <%%get_name%%.h>

GeometryEngine::GeometryEngine()
 : indexBuf(QOpenGLBuffer::IndexBuffer)
 , need_gpu_upload(true)
{
    initializeOpenGLFunctions();
    arrayBuf.create();
    indexBuf.create();
    // initGeometry();
}

GeometryEngine::~GeometryEngine() {
    arrayBuf.destroy();
    indexBuf.destroy();
}

int GeometryEngine::get_vertices_count() { return 8164; }

int GeometryEngine::get_indices_count() { return 47733; }

int GeometryEngine::get_vertex_size() { return sizeof(MeshVertexData); }

void GeometryEngine::initGeometry() {
    MeshVertexData vertices[] = {
        #include <builtins/Nikita0.gen.txt>
    }; // len = 8164

    GLushort indices[]    = {
        #include <builtins/NikitaI.gen.txt>
    }; // len = 47733

    // Transfer vertex data to VBO 0
    arrayBuf.bind();
    arrayBuf.allocate(vertices, get_vertices_count() * get_vertex_size());

    // Transfer index data to VBO 1
    indexBuf.bind();
    indexBuf.allocate(indices, get_indices_count() * sizeof(GLushort));
}

void GeometryEngine::drawGeometry(QOpenGLShaderProgram *program)
{
    if (need_gpu_upload) {
        initGeometry();
        need_gpu_upload = false;
    }

    // Tell OpenGL which VBOs to use
    arrayBuf.bind();
    indexBuf.bind();

    // Offset for position
    quintptr offset = 0;

    /// POSITION
    // Tell OpenGL programmable pipeline how to locate vertex position data
    int vertexLocation = program->attributeLocation("a_position");
    program->enableAttributeArray(vertexLocation);
    program->setAttributeBuffer(vertexLocation, GL_FLOAT, offset, 3, sizeof(MeshVertexData));

    // Offset for texture coordinate
    offset += sizeof(QVector3D);

    /// NORMAL
    // Tell OpenGL programmable pipeline how to locate vertex position data
    int normalLocation = program->attributeLocation("a_normal");
    program->enableAttributeArray(normalLocation);
    program->setAttributeBuffer(normalLocation, GL_FLOAT, offset, 3, sizeof(MeshVertexData));

    offset += sizeof(QVector3D);

    /// TEXCOORD_0
    // Tell OpenGL programmable pipeline how to locate vertex texture coordinate data
    int texcoordLocation = program->attributeLocation("a_texcoord");
    program->enableAttributeArray(texcoordLocation);
    program->setAttributeBuffer(texcoordLocation, GL_FLOAT, offset, 2, sizeof(MeshVertexData));

    // Draw cube geometry using indices from VBO 1
    // glDrawElements(GL_TRIANGLE_STRIP, 34, GL_UNSIGNED_SHORT, 0);
    glDrawElements(GL_TRIANGLES, 47733, GL_UNSIGNED_SHORT, 0);
}

struct draw_commands : protected QOpenGLFunctions {};
struct draw_variable_buffer : public draw_commands {
    attr(const QString& name, GLenum type, int offset, int tupleSize, int stride = 0 );
};
struct draw_elements : draw_commands {
    void paint() {
        glDrawElements(GL_TRIANGLES, 47733, GL_UNSIGNED_SHORT, 0);
    }
};

void geom::QtGpuSkin::drawGeometry(QOpenGLShaderProgram *program)
{
    // Tell OpenGL which VBOs to use
    arrayBuf.bind();
    indexBuf.bind();

    // Offset for position
    quintptr offset = 0;

    /// 
    /// int attribute_location, QString attribute_name
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

gx_pri_face_template = """# autogenerated GGAP head
!contains ( INCLUDEPATH, $$PWD ) {
  HEADERS     += $$PWD/%%get_name%%.h
  SOURCES     += $$PWD/%%get_name%%.cpp
  INCLUDEPATH += $$PWD
}
"""

class gx_gap_interface(object):
    """ In GLSL shader:
    uniform float v[10];
        
        In C/CPP program:(Then you can set their values using glUniform{1,2,3,4}{f,i}v)
    
    GLfloat v[10] = {...};
    glUniform1fv(glGetUniformLocation(program, "v"), 10, v);

    !!! It is the possible problem with "glUniform" array binding
    Glint result; glGetIntegerv(GL_MAX_UNIFORM_LOCATIONS, 0, &result);
    """
    def __init__(self, path, name = ''):
        """Create or recreate QT gx_gap_interface folder at target 'path'
        overwrite gx_gap_interface.h, gx_gap_interface.cpp files and pri
        file, so be carefully all old changes in this files lost.
        """
        self.path = os.path.abspath(path)
        self.path = os.path.normpath(self.path).replace(os.path.sep, "/")
        self.name = ('gx_gap_interface', name)[bool(name)]
    
    # add some re.sub callable ability: 
    def __call__(self, match): return str(getattr(self, match.groups()[0])())

    # add re.sub variable's generators:
    def get_name       (self): return self.name 

    def get_name_upper (self): return self.get_name().upper()
    
    def get_path       (self): return self.path
    
    def get_info       (self): return re.sub( "%%(\\w+)%%", self, self.get_form())
    
    def get_form       (self): return re.sub( "%%%%", self.__class__.__name__, self.get_inf_form() )

    @staticmethod
    def get_pri_form(): return gx_pri_face_template

    @staticmethod
    def get_hpp_form(): return gx_hpp_face_template

    @staticmethod
    def get_cpp_form(): return gx_cpp_face_template

    @staticmethod
    def get_inf_form(): return gx_inf_face_template

    def get_pri_body(self): return re.sub( "%%(\\w+)%%", self, self.get_pri_form() )
    
    def get_hpp_body(self): return re.sub( "%%(\\w+)%%", self, self.get_hpp_form() )
    
    def get_cpp_body(self): return re.sub( "%%(\\w+)%%", self, self.get_cpp_form() )

    def generate(self):
        """Recreate/rewrite all gx_gap_interface qmake project files"""
        dir_path = os.path.normpath( os.path.join( self.path, self.name ) )

        if not os.path.isdir ( dir_path ):
            os.makedirs      ( dir_path )

        cpp_path = os.path.normpath( os.path.join( dir_path, "%s.cpp" % self.name ) )
        hpp_path = os.path.normpath( os.path.join( dir_path, "%s.h"   % self.name ) )
        pri_path = os.path.normpath( os.path.join( dir_path, "%s.pri" % self.name ) )

        with open( pri_path, "w" ) as f:
            f.write( self.get_pri_body() )

        with open( hpp_path, "w" ) as f:
            f.write( self.get_hpp_body() )

        with open( cpp_path, "w" ) as f:
            f.write( self.get_cpp_body() )


def generate(path):
    import json
    import pprint

    class my_gx_gap_interface(gx_gap_interface):
        pass

    face = my_gx_gap_interface(path, name="gx_gap_interface")
    info = json.loads(face.get_info())

    pprint.pprint( info, width=2 )

    face.generate()

if __name__ == '__main__':
    generate(os.path.join(os.path.split(sys.argv[0])[0],"../"))


