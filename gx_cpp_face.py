import os, sys, re

gx_inf_face_template = """{ "type": "%%%%"
, "name": "%%get_name%%"
, "path": "%%get_path%%"
}"""

gx_hpp_face_template = """#ifndef %%get_name_upper%%_H
#define %%get_name_upper%%_H

#include <map>
#include <list>
#include <string>

#include <QOpenGLFunctions>
#include <QOpenGLShaderProgram>
#include <QOpenGLBuffer>
#include <QVector2D>
#include <QVector3D>
#include <QVector4D>
#include <QObject>

#define JSON(...) #__VA_ARGS__
/* // HOWTO use this JSON define:
const char* sample_json = JSON ( // comment
{"run_machine":"load_parallel_threads"
//,"0" : "https://godbolt.org?123&123"
,"1" : "https://godbolt.org??123&123"
,"2" : "https://god_bolt.org?123&123"
,"3" : "https://god___bolt.org??123&123"
,"4" : "https://god_____bolt.org?123&123"
,"5" : "https://godbolt.org???123&123"
,"one_success": ["stop_other","print_curr", "sw_machine"]
,"one_failure": ["print_curr","print_fail", "_continue"]
,"all_failure": ["reset_to_initial_state"]
});
*/

/* root API .h contain only abstract "vertex attribute class"
struct av4f:vtxa {
    virtual ~av4f(){}
    virtual float* get_vec4() const = 0;
    // virtual int get_size() const => derived from "vtxa"
    void on(vtxa::proc*p){p->on(this);}
};

// how to use this abstraction:
#include <gx_src_glsl.h>
...
av4f* example_get_value() {  // std::map<std::string, av4f*> position;
    static struct : av4f {
       float* get_vec4() const { static float a[] = { 1.f, 2.f, 3.f, 7.f }; return a; }
       int    get_size() const { return 1; }
    } some_buff; return &some_buff;
}
*/


namespace gx
{
    struct prog;  // glsl program state machine
    struct indx;  // draw method base class TRIANGLE_FAN, TRIANGLE_STRIP, TRIANGLES, e.t.c.
    struct vtxa;  // glsl program abstract attribute
    struct unfa;  // glsl program abstract uniform attribute
    struct surf;  // immutable surface's description base class

    struct tran {    // base class for proj/node/joint with get_mat4 pointer ability
        virtual ~tran() {}
        virtual float* get_mat4() = 0;
    };

    struct surf {    // shared surface ( exported const object )
        std::map<std::string, vtxa*> m_buff;  // exported vertex attributes                (const)
        std::map<std::string, unfa*> m_vars;  // exported dependances (uniform attributes) (const)
                                              // initial textures, weights,
                                              // ...
        std::list<indx*> m_ibo;               // index arrays with draw mode
        std::list<tran*> m_to_export_root;    // const exported scene position
        std::list<tran*> joints;              // skin's fixed exported joints in bind-pos
    };

    struct shgr   // shading group material and surface based(real-time animated view-surface)
    {
        surf* mp_surf;
        prog* mp_prog;

        std::map<std::string, unfa*> m_vars;  // changed dependances (uniform attributes)
                                              // changed textures and other uniforms
                                              // initial contain self mp_surf->m_vars;
        std::list<tran*> m_to_export_root;    // editable exported scene position
        std::list<tran*> m_to_mount_root;     // scene root scene initial - empty
        std::list<tran*> m_joints;            // animated joints, binded to other transformations
        virtual void draw() { }
    };

    // GL index array
    // Surf contain one or more named index arrays. Each faces set can be drawed
    // separately with other draw method, textures, programm, gl-option, e.t.c.
    struct indx
    {
        struct triangles;
        struct triangle_fan;
        struct triangle_strip;
        struct proc
        {   // visitor needed?
            virtual ~proc() {}
            virtual void on(gx::indx::triangles      *) = 0;
            virtual void on(gx::indx::triangle_fan   *) = 0;
            virtual void on(gx::indx::triangle_strip *) = 0;
        };
        virtual ~indx() {}
        virtual unsigned  get_size() const = 0;
        virtual unsigned* get_buff() = 0;  // is can be calculated, deprecate 'const'
        virtual void on(gx::indx*) = 0;
    };

    struct indx::triangles:indx {
        void on(indx::proc*o){o->on(this);}
        virtual ~triangles() {}
    };

    struct indx::triangle_strip:indx {
        void on(indx::proc*o){o->on(this);}
        virtual ~triangle_strip() {}
    };

    struct indx::triangle_fan:indx {
        void on(indx::proc*o){o->on(this);}
        virtual ~triangle_fan() {}
    };

    // GLES2.0 GLSL1.1 vertex attributes

    struct av1f;    struct av2f;    struct av3f;    struct av4f;
    struct av1i;    struct av2i;    struct av3i;    struct av4i;
    struct av1b;    struct av2b;    struct av3b;    struct av4b;
    struct av1u;    struct am2f;    struct am3f;    struct am4f;

    // GLSL vertex attribute abstract base class

    struct vtxa
    {
        struct proc
        {
            virtual ~proc() {}
            virtual void on(gx::av1f*) = 0;  // "float"         GL_FLOAT
            virtual void on(gx::av2f*) = 0;  // "vec2"          GL_FLOAT_VEC2
            virtual void on(gx::av3f*) = 0;  // "vec3"          GL_FLOAT_VEC3
            virtual void on(gx::av4f*) = 0;  // "vec4"          GL_FLOAT_VEC4
            virtual void on(gx::av1i*) = 0;  // "int"           GL_INT
            virtual void on(gx::av2i*) = 0;  // "ivec2"         GL_INT_VEC2
            virtual void on(gx::av3i*) = 0;  // "ivec3"         GL_INT_VEC3
            virtual void on(gx::av4i*) = 0;  // "ivec4"         GL_INT_VEC4
            virtual void on(gx::av1u*) = 0;  // "unsigned int"  GL_UNSIGNED_INT
            virtual void on(gx::av1b*) = 0;  // "bool"          GL_BOOL
            virtual void on(gx::av2b*) = 0;  // "bvec2"         GL_BOOL_VEC2
            virtual void on(gx::av3b*) = 0;  // "bvec3"         GL_BOOL_VEC3
            virtual void on(gx::av4b*) = 0;  // "bvec4"         GL_BOOL_VEC4
            virtual void on(gx::am2f*) = 0;  // "mat2"          GL_FLOAT_MAT2
            virtual void on(gx::am3f*) = 0;  // "mat3"          GL_FLOAT_MAT3
            virtual void on(gx::am4f*) = 0;  // "mat4"          GL_FLOAT_MAT4
        };

        virtual void on(vtxa::proc*) = 0;

        virtual int get_glsl_type_id() const = 0;

        virtual const char* get_glsl_type_name() const = 0;

        virtual int get_size() const = 0;

        virtual ~vtxa(){}

        static const char* get_glsl_type_name(const int& n);
    };                                                            // vtxa

    // GLES2.0 GLSL1.1 uniform attributes

    struct uv1f;    struct uv2f;    struct uv3f;    struct uv4f;  // float, vec*
    struct uv1i;    struct uv2i;    struct uv3i;    struct uv4i;  // int, ivec*
    struct uv1b;    struct uv2b;    struct uv3b;    struct uv4b;  // bool, bvec*
    struct uv1u;    struct um2f;    struct um3f;    struct um4f;  // unsigned int, mat*
    struct tx2d;  // sampler2D     GL_SAMPLER_2D
    struct txcb;  // samplerCube   GL_SAMPLER_CUBE

    struct unfa
    {
        struct prog
        {
            virtual ~prog(){}
            virtual void on(gx::uv1f*) = 0;  // float         GL_FLOAT
            virtual void on(gx::uv2f*) = 0;  // vec2          GL_FLOAT_VEC2
            virtual void on(gx::uv3f*) = 0;  // vec3          GL_FLOAT_VEC3
            virtual void on(gx::uv4f*) = 0;  // vec4          GL_FLOAT_VEC4
            virtual void on(gx::uv1i*) = 0;  // int           GL_INT
            virtual void on(gx::uv2i*) = 0;  // ivec2         GL_INT_VEC2
            virtual void on(gx::uv3i*) = 0;  // ivec3         GL_INT_VEC3
            virtual void on(gx::uv4i*) = 0;  // ivec4         GL_INT_VEC4
            virtual void on(gx::uv1u*) = 0;  // unsigned int  GL_UNSIGNED_INT
            virtual void on(gx::uv1b*) = 0;  // bool          GL_BOOL
            virtual void on(gx::uv2b*) = 0;  // bvec2         GL_BOOL_VEC2
            virtual void on(gx::uv3b*) = 0;  // bvec3         GL_BOOL_VEC3
            virtual void on(gx::uv4b*) = 0;  // bvec4         GL_BOOL_VEC4
            virtual void on(gx::um2f*) = 0;  // mat2          GL_FLOAT_MAT2
            virtual void on(gx::um3f*) = 0;  // mat3          GL_FLOAT_MAT3
            virtual void on(gx::um4f*) = 0;  // mat4          GL_FLOAT_MAT4
            virtual void on(gx::tx2d*) = 0;  // sampler2D     GL_SAMPLER_2D
            virtual void on(gx::txcb*) = 0;  // samplerCube   GL_SAMPLER_CUBE
        };

        virtual void on(unfa::prog*) = 0;

        virtual ~unfa() {}

        virtual const char* get_glsl_type_id() = 0;

        virtual const char* get_glsl_type_name() = 0;

        static const char* get_glsl_type_name(const int& n);
    };                                                            // unfa

    struct av1f : vtxa
    {
        virtual ~av1f() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT; }

        const char* get_glsl_type_name() const { return "float"; }
    };

    struct av2f : vtxa
    {
        virtual ~av2f() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT_VEC2; }

        const char* get_glsl_type_name() const { return "vec2"; }
    };

    struct av3f : vtxa
    {
        virtual ~av3f() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT_VEC3; }

        const char* get_glsl_type_name() const { return "vec3"; }
    };

    struct av4f : vtxa
    {
        virtual ~av4f() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT_VEC4; }

        const char* get_glsl_type_name() const { return "vec4"; }
    };

    struct av1i : vtxa
    {
        virtual ~av1i() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_INT; }

        const char* get_glsl_type_name() const { return "int"; }
    };

    struct av2i : vtxa
    {
        virtual ~av2i() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_INT_VEC2; }

        const char* get_glsl_type_name() const { return "ivec2"; }
    };

    struct av3i : vtxa
    {
        virtual ~av3i() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_INT_VEC3; }

        const char* get_glsl_type_name() const { return "ivec3"; }
    };

    struct av4i : vtxa
    {
        virtual ~av4i() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_INT_VEC4; }

        const char* get_glsl_type_name() const { return "ivec4"; }
    };

    struct av1u : vtxa
    {
        virtual ~av1u() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_UNSIGNED_INT; }

        const char* get_glsl_type_name() const { return "unsigned int"; }
    };

    struct av1b : vtxa
    {
        virtual ~av1b() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_BOOL; }

        const char* get_glsl_type_name() const { return "bool"; }
    };

    struct av2b : vtxa
    {
        virtual ~av2b() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_BOOL_VEC2; }

        const char* get_glsl_type_name() const { return "bvec2"; }
    };

    struct av3b : vtxa
    {
        virtual ~av3b() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_BOOL_VEC3; }

        const char* get_glsl_type_name() const { return "bvec3"; }
    };

    struct av4b : vtxa
    {
        virtual ~av4b() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_BOOL_VEC4; }

        const char* get_glsl_type_name() const { return "bvec4"; }
    };

    struct am2f : vtxa
    {
        virtual ~am2f() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT_MAT2; }

        const char* get_glsl_type_name() const { return "mat2"; }
    };

    struct am3f : vtxa
    {
        virtual ~am3f() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT_MAT3; }

        const char* get_glsl_type_name() const { return "mat3"; }
    };

    struct am4f : vtxa
    {
        virtual ~am4f() {}

        void on(vtxa::proc* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT_MAT4; }

        const char* get_glsl_type_name() const { return "mat4"; }
    };

    // GLSL uniform attributes abstract base class


    struct uv1f : unfa
    {
        virtual ~uv1f() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT; }

        const char* get_glsl_type_name() const { return "float"; }
    };

    struct uv2f : unfa
    {
        virtual ~uv2f() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT_VEC2; }

        const char* get_glsl_type_name() const { return "vec2"; }
    };

    struct uv3f : unfa
    {
        virtual ~uv3f() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT_VEC3; }

        const char* get_glsl_type_name() const { return "vec3"; }
    };

    struct uv4f : unfa
    {
        virtual ~uv4f() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT_VEC4; }

        const char* get_glsl_type_name() const { return "vec4"; }
    };

    struct uv1i : unfa
    {
        virtual ~uv1i() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_INT; }

        const char* get_glsl_type_name() const { return "int"; }
    };

    struct uv2i : unfa
    {
        virtual ~uv2i() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_INT_VEC2; }

        const char* get_glsl_type_name() const { return "ivec2"; }
    };

    struct uv3i : unfa
    {
        virtual ~uv3i() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_INT_VEC3; }

        const char* get_glsl_type_name() const { return "ivec3"; }
    };

    struct uv4i : unfa
    {
        virtual ~uv4i() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_INT_VEC4; }

        const char* get_glsl_type_name() const { return "ivec4"; }
    };

    struct uv1u : unfa
    {
        virtual ~uv1u() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_UNSIGNED_INT; }

        const char* get_glsl_type_name() const { return "unsigned int"; }
    };

    struct uv1b : unfa
    {
        virtual ~uv1b() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_BOOL; }

        const char* get_glsl_type_name() const { return "bool"; }
    };

    struct uv2b : unfa
    {
        virtual ~uv2b() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_BOOL_VEC2; }

        const char* get_glsl_type_name() const { return "bvec2"; }
    };

    struct uv3b : unfa
    {
        virtual ~uv3b() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_BOOL_VEC3; }

        const char* get_glsl_type_name() const { return "bvec3"; }
    };

    struct uv4b : unfa
    {
        virtual ~uv4b() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_BOOL_VEC4; }

        const char* get_glsl_type_name() const { return "bvec4"; }
    };

    struct um2f : unfa
    {
        virtual ~um2f() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT_MAT2; }

        const char* get_glsl_type_name() const { return "mat2"; }
    };

    struct um3f : unfa
    {
        virtual ~um3f() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT_MAT3; }

        const char* get_glsl_type_name() const { return "mat3"; }
    };

    struct um4f : unfa
    {
        virtual ~um4f() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_FLOAT_MAT4; }

        const char* get_glsl_type_name() const { return "mat4"; }
    };

    struct tx2d : unfa
    {
        virtual ~tx2d() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_SAMPLER_2D; }

        const char* get_glsl_type_name() const { return "sampler2D"; }
    };

    struct txcb : unfa
    {
        virtual ~txcb() {}

        void on(unfa::prog* o) { o->on(this); }

        int  get_glsl_type_id() const { return GL_SAMPLER_CUBE; }

        const char* get_glsl_type_name() const { return "samplerCube"; }
    };

}

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

class GeometryComponent: protected QOpenGLFunctions  // pure abstract geometry scene component
{
public:
    virtual~GeometryComponent(){}
    virtual void drawGeometry(QOpenGLShaderProgram *program) = 0;
    virtual void initGeometry() = 0;
};

class GeometryTransform: public GeometryComponent
{
    QMatrix4x4                            view_transform;
    std::map<QString, GeometryComponent*> dag_components;
public:
    virtual void drawGeometry(QOpenGLShaderProgram*){}
    virtual void initGeometry(){}
};

class GeometryEngine : public GeometryComponent
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
gx_cpp_face_template = """#include <%%get_name%%.h>

// WARNING! UNSUPPORTED UNIFORM & ATTRIBUTE TYPES:
//   { GL_DOUBLE            , "double"       },
//   { GL_DOUBLE_VEC2       , "dvec2"        },
//   { GL_DOUBLE_VEC3       , "dvec3"        },
//   { GL_DOUBLE_VEC4       , "dvec4"        },
//   { GL_UNSIGNED_INT_VEC2 , "uvec2"        },
//   { GL_UNSIGNED_INT_VEC3 , "uvec3"        },
//   { GL_UNSIGNED_INT_VEC4 , "uvec4"        },
//   { GL_FLOAT_MAT2x3      , "mat2x3"       },
//   { GL_FLOAT_MAT2x4      , "mat2x4"       },
//   { GL_FLOAT_MAT3x2      , "mat3x2"       },
//   { GL_FLOAT_MAT3x4      , "mat3x4"       },
//   { GL_FLOAT_MAT4x2      , "mat4x2"       },
//   { GL_FLOAT_MAT4x3      , "mat4x3"       },
//   { GL_DOUBLE_MAT2       , "dmat2"        },
//   { GL_DOUBLE_MAT3       , "dmat3"        },
//   { GL_DOUBLE_MAT4       , "dmat4"        },
//   { GL_DOUBLE_MAT2x3     , "dmat2x3"      },
//   { GL_DOUBLE_MAT2x4     , "dmat2x4"      },
//   { GL_DOUBLE_MAT3x2     , "dmat3x2"      },
//   { GL_DOUBLE_MAT3x4     , "dmat3x4"      },
//   { GL_DOUBLE_MAT4x2     , "dmat4x2"      },
//   { GL_DOUBLE_MAT4x3     , "dmat4x3"      },

// WARNING! UNSUPPORTED UNIFORM TYPES:
//   { GL_SAMPLER_1D                                , "sampler1D"            },
//   { GL_SAMPLER_3D                                , "sampler3D"            },
//   { GL_SAMPLER_1D_SHADOW                         , "sampler1DShadow"      },
//   { GL_SAMPLER_2D_SHADOW                         , "sampler2DShadow"      },
//   { GL_SAMPLER_1D_ARRAY                          , "sampler1DArray"       },
//   { GL_SAMPLER_2D_ARRAY                          , "sampler2DArray"       },
//   { GL_SAMPLER_1D_ARRAY_SHADOW                   , "sampler1DArrayShadow" },
//   { GL_SAMPLER_2D_ARRAY_SHADOW                   , "sampler2DArrayShadow" },
//   { GL_SAMPLER_2D_MULTISAMPLE                    , "sampler2DMS"          },
//   { GL_SAMPLER_2D_MULTISAMPLE_ARRAY              , "sampler2DMSArray"     },
//   { GL_SAMPLER_CUBE_SHADOW                       , "samplerCubeShadow"    },
//   { GL_SAMPLER_BUFFER                            , "samplerBuffer"        },
//   { GL_SAMPLER_2D_RECT                           , "sampler2DRect"        },
//   { GL_SAMPLER_2D_RECT_SHADOW                    , "sampler2DRectShadow"  },
//   { GL_INT_SAMPLER_1D                            , "isampler1D"           },
//   { GL_INT_SAMPLER_2D                            , "isampler2D"           },
//   { GL_INT_SAMPLER_3D                            , "isampler3D"           },
//   { GL_INT_SAMPLER_CUBE                          , "isamplerCube"         },
//   { GL_INT_SAMPLER_1D_ARRAY                      , "isampler1DArray"      },
//   { GL_INT_SAMPLER_2D_ARRAY                      , "isampler2DArray"      },
//   { GL_INT_SAMPLER_2D_MULTISAMPLE                , "isampler2DMS"         },
//   { GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY          , "isampler2DMSArray"    },
//   { GL_INT_SAMPLER_BUFFER                        , "isamplerBuffer"       },
//   { GL_INT_SAMPLER_2D_RECT                       , "isampler2DRect"       },
//   { GL_UNSIGNED_INT_SAMPLER_1D                   , "usampler1D"           },
//   { GL_UNSIGNED_INT_SAMPLER_2D                   , "usampler2D"           },
//   { GL_UNSIGNED_INT_SAMPLER_3D                   , "usampler3D"           },
//   { GL_UNSIGNED_INT_SAMPLER_CUBE                 , "usamplerCube"         },
//   { GL_UNSIGNED_INT_SAMPLER_1D_ARRAY             , "usampler2DArray"      },
//   { GL_UNSIGNED_INT_SAMPLER_2D_ARRAY             , "usampler2DArray"      },
//   { GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE       , "usampler2DMS"         },
//   { GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY , "usampler2DMSArray"    },
//   { GL_UNSIGNED_INT_SAMPLER_BUFFER               , "usamplerBuffer"       },
//   { GL_UNSIGNED_INT_SAMPLER_2D_RECT              , "usampler2DRect"       },
//   { GL_IMAGE_1D                                  , "image1D"              },
//   { GL_IMAGE_2D                                  , "image2D"              },
//   { GL_IMAGE_3D                                  , "image3D"              },
//   { GL_IMAGE_2D_RECT                             , "image2DRect"          },
//   { GL_IMAGE_CUBE                                , "imageCube"            },
//   { GL_IMAGE_BUFFER                              , "imageBuffer"          },
//   { GL_IMAGE_1D_ARRAY                            , "image1DArray"         },
//   { GL_IMAGE_2D_ARRAY                            , "image2DArray"         },
//   { GL_IMAGE_2D_MULTISAMPLE                      , "image2DMS"            },
//   { GL_IMAGE_2D_MULTISAMPLE_ARRAY                , "image2DMSArray"       },
//   { GL_INT_IMAGE_1D                              , "iimage1D"             },
//   { GL_INT_IMAGE_2D                              , "iimage2D"             },
//   { GL_INT_IMAGE_3D                              , "iimage3D"             },
//   { GL_INT_IMAGE_2D_RECT                         , "iimage2DRect"         },
//   { GL_INT_IMAGE_CUBE                            , "iimageCube"           },
//   { GL_INT_IMAGE_BUFFER                          , "iimageBuffer"         },
//   { GL_INT_IMAGE_1D_ARRAY                        , "iimage1DArray"        },
//   { GL_INT_IMAGE_2D_ARRAY                        , "iimage2DArray"        },
//   { GL_INT_IMAGE_2D_MULTISAMPLE                  , "iimage2DMS"           },
//   { GL_INT_IMAGE_2D_MULTISAMPLE_ARRAY            , "iimage2DMSArray"      },
//   { GL_UNSIGNED_INT_IMAGE_1D                     , "uimage1D"             },
//   { GL_UNSIGNED_INT_IMAGE_2D                     , "uimage2D"             },
//   { GL_UNSIGNED_INT_IMAGE_3D                     , "uimage3D"             },
//   { GL_UNSIGNED_INT_IMAGE_2D_RECT                , "uimage2DRect"         },
//   { GL_UNSIGNED_INT_IMAGE_CUBE                   , "uimageCube"           },
//   { GL_UNSIGNED_INT_IMAGE_BUFFER                 , "uimageBuffer"         },
//   { GL_UNSIGNED_INT_IMAGE_1D_ARRAY               , "uimage1DArray"        },
//   { GL_UNSIGNED_INT_IMAGE_2D_ARRAY               , "uimage2DArray"        },
//   { GL_UNSIGNED_INT_IMAGE_2D_MULTISAMPLE         , "uimage2DMS"           },
//   { GL_UNSIGNED_INT_IMAGE_2D_MULTISAMPLE_ARRAY   , "uimage2DMSArray"      },
//   { GL_UNSIGNED_INT_ATOMIC_COUNTER               , "atomic_uint"          },

const char* gx::vtxa::get_glsl_type_name(const int& n)
{
    static std::map<int, const char*> t_name = {
        { GL_FLOAT             , "float"        },
        { GL_FLOAT_VEC2        , "vec2"         },
        { GL_FLOAT_VEC3        , "vec3"         },
        { GL_FLOAT_VEC4        , "vec4"         },
        { GL_INT               , "int"          },
        { GL_INT_VEC2          , "ivec2"        },
        { GL_INT_VEC3          , "ivec3"        },
        { GL_INT_VEC4          , "ivec4"        },
        { GL_UNSIGNED_INT      , "unsigned int" },
        { GL_BOOL              , "bool"         },
        { GL_BOOL_VEC2         , "bvec2"        },
        { GL_BOOL_VEC3         , "bvec3"        },
        { GL_BOOL_VEC4         , "bvec4"        },
        { GL_FLOAT_MAT2        , "mat2"         },
        { GL_FLOAT_MAT3        , "mat3"         },
        { GL_FLOAT_MAT4        , "mat4"         },
    };

    auto exists = t_name.find(n);

    return t_name.end() == exists ? "UNSUPPORTED_ATTRIBUTE_TYPE" : exists->second;
}

const char* gx::unfa::get_glsl_type_name(const int& n)
{
    static std::map<int, const char*> t_name =
    {
        { GL_FLOAT                                     , "float"                },
        { GL_FLOAT_VEC2                                , "vec2"                 },
        { GL_FLOAT_VEC3                                , "vec3"                 },
        { GL_FLOAT_VEC4                                , "vec4"                 },
        { GL_INT                                       , "int"                  },
        { GL_INT_VEC2                                  , "ivec2"                },
        { GL_INT_VEC3                                  , "ivec3"                },
        { GL_INT_VEC4                                  , "ivec4"                },
        { GL_UNSIGNED_INT                              , "unsigned int"         },
        { GL_BOOL                                      , "bool"                 },
        { GL_BOOL_VEC2                                 , "bvec2"                },
        { GL_BOOL_VEC3                                 , "bvec3"                },
        { GL_BOOL_VEC4                                 , "bvec4"                },
        { GL_FLOAT_MAT2                                , "mat2"                 },
        { GL_FLOAT_MAT3                                , "mat3"                 },
        { GL_FLOAT_MAT4                                , "mat4"                 },
        { GL_SAMPLER_2D                                , "sampler2D"            },
        { GL_SAMPLER_CUBE                              , "samplerCube"          },
    };

    auto exists = t_name.find(n);

    return t_name.end() == exists ? "UNSUPPORTED_UNIFORM_TYPE" : exists->second;
}

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
    /*
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
    */
        MeshVertexData vertices[] =
        #include <vbo_pcube1.inc>
    ; // len = 459 ( example 8164 ) is vertices count, not floats

    GLushort indices[]    =
        #include <ibo_pcube1.inc>
    ; // len = 708 ( example 47733 )

    // Transfer vertex data to VBO 0
    arrayBuf.bind();
    arrayBuf.allocate(vertices, 459 * sizeof(MeshVertexData) );

    // Transfer index data to VBO 1
    indexBuf.bind();
    indexBuf.allocate(indices, 708 * sizeof(GLushort));
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
    /*
    MESH AT{0: (0, "bytearray(b'pCube1')", 'pCube1')}
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
    glDrawElements(GL_TRIANGLES, 708, GL_UNSIGNED_SHORT, 0);

    /* old nikita variant
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
    */
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


