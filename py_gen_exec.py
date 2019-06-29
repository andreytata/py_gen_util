#!/usr/bin/env python
# coding: utf-8

"""Execute rebuild source for each qmake pri projects at self parent folder.
All folders named as gx_gen_NAMESPACE_NAME, with gx_gen_NAMESPACE_NAME.pri, this
script find line with source glTF2.0 file. Folder can contain more then one file
used .gltf extention, generator must use only one, defined in "py_gen_util.json:
{..., "gltf":"file_name.gltf", ... }

Все генерируемые классы интегрируются через объект генератор фабрики. Интерфейсы
генерируемой геометрии и генерируемой фабрики элемента сцены описаны в interface,
( qmake project "gx_gap_interface.pri" ). Каждый сгенерированный проект содержит
класс-потомок абстрактой фабрики, которая в конкретный узел сцены может добавлять
копию сцены и/или ссылку на сгенерированную поверхность (по имени в сцене).

Корневой интегратор является словарем абстрактных фабрик, делающим всю генеративную
часть доступной для инспекции и использования через вызов метаметода. Каждому слоту
соответствует указатель на статически размещенную сгенерированную фабрику. Смысл в
том, что ::set_geom_factory("scene_name") вызовет ::set_geom_factory_scene_name(),
который установит внутреннюю переменную mp_geom_factory. Значение которой можно
получить через вызов get_geom_factory() => gx::geom::factory*.

Результат генерации - узел (cloned_view_transform), указывающий на вершину дерева
разделяемой сцены (shared_view_transform), который в свою очередь указывает на все
все свои иммутабельные под-узлы. Причина иммутабельности - имена и bind-positions,
идентификаторы веток и начальные состояния трансформов до внесения данных в аним-
channels. Т.е. базовые состояния до внесения смещений (изменений) через средства
анимации. Т.е. все данные (значения) которые понадобятся для выполнения операции
"сброс в исходное состояние". Это накладывает жесткие ограничения на конструкцию
встроенных разделяемых данных сцены:

class static_node; class static_bind; class static_mesh; class static_skin; ...

static_node* geom::generated::%%get_gltf_name%%::get_scene()
{
    static n00 = static_node("root_node");
    static n01 = static_node("some_other_node");
    static n00_n01 = static_bind( &n00, &n01 );
    ...
    return &n00;  //
}

Что, как следствие, создает громоздкий и тяжело читаемый код начальной инициализации.
Простейший подход - функция, в теле которой все узлы типа "bind" объявлены статически,
связаны статически и всё тело такой функции создает "робот"-generator. Фабрика просто
возвращает cloned_node(const static_node&). Неизвестно как наименует этот узел участок
кода, инициировавший его создание, но указатель на матрицу с начальным положением этот
"клон" будет иметь. Этого должно быть достаточно для запуска "визитора" в разделяемое
дерево статических узлов. "визитор" - это то что рисует граф сцены, или клонирует его.

#include <stdio.h>
#include <list>
struct seed {
    struct node;  // contain "transform" QMatrix4x4) ??
    struct mesh;
    struct skin;
    struct vars;
    struct tran;  // transform ( contain both "init" node* and "curr" QMatrix4x4) ??
    struct proc{
        virtual void on(node*) = 0;
        virtual void on(mesh*) = 0;
        virtual void on(skin*) = 0;
        virtual void on(vars*) = 0;
        virtual~proc(); 
    };
    seed(const char*n):mp_name(n){}
    virtual ~seed();
    virtual void on(seed::proc*)=0;
    const char* mp_name = "undefined";
    struct bind {
        bind(node*,node*) {
            // ... how to bind
        }
    };
};

struct seed::node : seed {node(const char*p):seed(p){}
 void on(seed::proc*p) { p->on(this); } };
struct seed::mesh : seed {mesh(const char*p):seed(p){}
 void on(seed::proc*p) { p->on(this); } };
struct seed::skin : seed {skin(const char*p):seed(p){}
 void on(seed::proc*p) { p->on(this); } };

seed* gen_main() {
    static seed::node n00("scene_root_name");
    static seed::node n01("scene_root_name");
    static seed::bind b0 (&n00, &n01);
    // ...
    return &n00;
}
"""

generated_hpp_template = """// WARNING! : IS AUTO-GENERATED FILE, DO NOT EDIT
#ifndef GX_AUTOGENERATED_FACTORY
#define GX_AUTOGENERATED_FACTORY

#include <QObject>
#include <QOpenGLWidget>
#include <QOpenGLFunctions>
#include <gx_gap_interface.h>

%%get_gap_includes%%

namespace geom
{
    class GENERATED_FACTORY : public QOpenGLWidget, protected QOpenGLFunctions
    {
        Q_OBJECT
    public:
        GENERATED_FACTORY( QWidget *parent = nullptr) : QOpenGLWidget(parent) {}
        virtual ~GENERATED_FACTORY(){}
    public slots:

    };

    class generated : public QObject
    {
        Q_OBJECT
    public:
        virtual ~generated(){}
        geom::node* mp_selected = nullptr;
        geom::node* select_node(geom::node*);
    public slots:
%%get_gap_public_slots%%
    };

}  // geom::

#endif // GX_AUTOGENERATED_FACTORY
"""

generated_cpp_template = """// WARNING! : IS AUTO-GENERATED FILE, DO NOT EDIT
#include <%%get_generated_hpp_name%%>

%%get_gap_public_slots_definitions%%

"""

generated_pri_template = """# Auto-Generated Builtins Factory Class
# Usage:
#   include(../gx_gap_generated/gx_gap_generated.pri)
!contains ( INCLUDEPATH, $$PWD ) {
  HEADERS     += $$PWD/%%get_generated_hpp_name%%
  SOURCES     += $$PWD/%%get_generated_cpp_name%%
  INCLUDEPATH += $$PWD
  include($$PWD/../gx_gap_interface/gx_gap_interface.pri)
%%get_pri_gen_includes%%
}
"""

import os, sys, re, json

from gx_cpp_glsl import QtGltfBuiltinPri

gx_gen_regexp = re.compile("^gx_gen_([_a-z][_a-z0-9]*)$")

# def generate_source_from_gltf(target_dir, match):
#     print('  -o-BEGIN target_dir "%s"' % target_dir)
#     print('   | match.groups()    %s' % repr(match.groups()))
#     config = open(os.path.join(target_dir, "py_gen_util.json"), "r")
#     config = json.loads(config.read())
#     print('   | config            %s' % config )
#     gltf_file_path = os.path.join(target_dir, config['gltf'])
#     print('   | gltf_file_path    "%s"' % gltf_file_path)
    
#     if not os.path.isfile(gltf_file_path): raise IOError(gltf_file_path)
    
#     namespace = match.groups()[0]
#     target_pri = os.path.join(target_dir, "gx_gen_%s.pri" % namespace)
#                                         # EXAMLE: 
#     proj = QtGltfBuiltinPri( namespace  # Slava_Rig_2
#         , gltf_file_path                # /bla/bla/Blender_export/Slava_Rig_2014_2015_NEW.gltf
#         , target_dir                    # /bla/bla/my_qt_project/builtins/gx_gen_Slava_Rig_2
#         , target_pri                    # /bla/bla/my_qt_project/builtins/gx_gen_Slava_Rig_2/gx_gen_Slava_Rig_2.pri'
#     )
#     proj.generate()
#     print('  -o-END "%s"' % target_dir)

class gx_gap_generated(object):
    """Each gx_gen_* folder in working directory must be added to factory.
    only factory can contain all methods and appropriate methametods with
    ability to create generated item instance. Each item separate, and all
    items in scene.
    """
    generated_hpp_template = generated_hpp_template
    generated_cpp_template = generated_cpp_template
    generated_pri_template = generated_pri_template

    def __init__(self, working_directory):
        self.working_directory = working_directory
        self.generated = dict()  # all sub-folders generated in working_directory
        # After all sub-project folders are generated this class must generate 'builder' - base
        # class for application's builtins factory (scene and geometry derived). Class folder &
        # "pri"-file included to application main "pro" or for other "pri" file
        self.factory_name = "gx_gap_generated"  # 'factory' project's folder & project-file name
        self.factory_path = os.path.abspath(os.path.join(self.working_directory, self.factory_name))
        self.factory_proj = os.path.join( self.factory_path, self.factory_name+'.pri' )

    def __call__(self, match): return str(getattr(self, match.groups()[0])())

    def get_generated_path     (self): return os.path.abspath(self.factory_path)
    def get_generated_name     (self): return self.factory_name

    def get_generated_dir_name (self): return self.factory_name
    def get_generated_cpp_name (self): return self.get_generated_name() + '.cpp'
    def get_generated_hpp_name (self): return self.get_generated_name() + '.h'
    def get_generated_pri_name (self): return self.get_generated_name() + '.pri'

    def get_generated_pri_path (self): return os.path.join(self.get_generated_path(), self.get_generated_pri_name())
    def get_generated_cpp_path (self): return os.path.join(self.get_generated_path(), self.get_generated_cpp_name())
    def get_generated_hpp_path (self): return os.path.join(self.get_generated_path(), self.get_generated_hpp_name())

    def get_hpp_template     (self): return self.generated_hpp_template
    def get_cpp_template     (self): return self.generated_cpp_template
    def get_pri_template     (self): return self.generated_pri_template

    def get_factory_pri_body (self): return re.sub("%%(\\w+)%%", self, self.get_pri_template())
    def get_factory_hpp_body (self): return re.sub("%%(\\w+)%%", self, self.get_hpp_template())
    def get_factory_cpp_body (self): return re.sub("%%(\\w+)%%", self, self.get_cpp_template())

    def generate(self):
        print( "PROJECT path '%s'" % self.working_directory )
        for name in os.listdir(self.working_directory):
            print("  ?%s" % os.path.join(parsed_dir, name))
            match = gx_gen_regexp.match(name)
            if match:
                target_dir = os.path.join(parsed_dir, name)
                print('  -o-BEGIN target_dir "%s"' % target_dir)
                print('   | match.groups()    %s' % repr(match.groups()))
                config = open(os.path.join(target_dir, "py_gen_util.json"), "r")
                config = json.loads(config.read())
                print('   | config            %s' % config )
                gltf_file_path = os.path.join(target_dir, config['gltf'])
                print('   | gltf_file_path    "%s"' % gltf_file_path)
                
                if not os.path.isfile(gltf_file_path): raise IOError(gltf_file_path)

                namespace = match.groups()[0]
                target_pri = os.path.join(target_dir, "gx_gen_%s.pri" % namespace)
                proj = QtGltfBuiltinPri( namespace  # 'Slava_Rig_2'
                    , gltf_file_path                # '/bla/bla/Blender_export/Slava_Rig_2014_2015_NEW.gltf'
                    , target_dir                    # '/bla/bla/my_qt_project/builtins/gx_gen_Slava_Rig_2'
                    , target_pri                    # '/bla/bla/my_qt_project/builtins/gx_gen_Slava_Rig_2/gx_gen_Slava_Rig_2.pri'
                )
                self.generated[name]=proj
                proj.generate()
                print('  -o-END "%s"' % target_dir)
        print( "PROJECT dict '%s'" % self.generated )
        print( "        path '%s'" % self.factory_path)
        
        if not os.path.isdir(self.factory_path):
            os.makedirs(self.factory_path)
        
        with open(self.get_generated_pri_path(), "w") as f:
            f.write(self.get_factory_pri_body())

        with open(self.get_generated_hpp_path(), "w") as f:
            f.write(self.get_factory_hpp_body())

        with open(self.get_generated_cpp_path(), "w") as f:
            f.write(self.get_factory_cpp_body())

        print(self.get_factory_pri_body())

    def get_gap_includes(self):
        includes = list()
        for i in self.generated:
            includes.append("#include <%s.h>" % i)
        return "\n".join(includes)

    def get_gap_public_slots(self):
        slots = list()
        for gen_pri_name in self.generated:
            slots.append("        void set_factory_%s();" % gen_pri_name)
        return "\n".join(slots)

    def get_gap_public_slots_definitions(self):
        slots = list()
        for gen_pri_name in self.generated:
            slots.append("void geom::generated::set_factory_%s(){}" % gen_pri_name)
        return "\n".join(slots)

    def get_pri_gen_includes(self):
        includes = list()
        for proj_name in self.generated:
            includes.append("  include($$PWD/../%s/%s.pri)" % (proj_name, proj_name))
        return "\n".join(includes)

if __name__=='__main__':
    print('''Python %s''' % sys.version)
    print('''os.getcwd() => "%s"''' % os.getcwd())
    utils_path = os.path.normpath(os.path.split(os.path.abspath(sys.argv[0]))[0])
    parsed_dir = os.path.split(utils_path)[0]
    print('utils_path "%s"' % utils_path)
    print('parsed_dir "%s"' % parsed_dir)

    from gx_cpp_face import gx_gap_interface

    interface_proj = gx_gap_interface(parsed_dir)
    interface_proj.generate()
    
    generated_proj = gx_gap_generated(parsed_dir)
    generated_proj.generate()
