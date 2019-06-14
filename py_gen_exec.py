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
"""

import os, sys, re, json
from gx_cpp_glsl import QtGltfBuiltinPri

gx_gen_regexp = re.compile("^gx_gen_([_a-z][_a-z0-9]*)$")

def generate_source_from_gltf(target_dir, match):
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
                                        # EXAMLE: 
    proj = QtGltfBuiltinPri( namespace  # Slava_Rig_2
        , gltf_file_path                # /bla/bla/Blender_export/Slava_Rig_2014_2015_NEW.gltf
        , target_dir                    # /bla/bla/my_qt_project/builtins/gx_gen_Slava_Rig_2
        , target_pri                    # /bla/bla/my_qt_project/builtins/gx_gen_Slava_Rig_2/gx_gen_Slava_Rig_2.pri'
    )
    proj.generate()
    print('  -o-END "%s"' % target_dir)

class gx_gap_generated(object):
    """Each gx_gen_* folder in working directory must be added to factory.
    only factory can contain all methods and appropriate methametods with
    ability to create generated item instance. Each item separate, and all
    items in scene.
    """
    def __init__(self, working_directory = '../'):
        self.working_directory = working_directory
        self.generated = dict()              # all sub-folders generated in working_directory
        self.final_gen = "gx_gap_generated"  # folder & pri generated-factory project name

if __name__=='__main__':
    print('''Python %s''' % sys.version)
    print('''os.getcwd() => "%s"''' % os.getcwd())
    utils_path = os.path.normpath(os.path.split(os.path.abspath(sys.argv[0]))[0])
    parsed_dir = os.path.split(utils_path)[0]
    print('utils_path "%s"' % utils_path)
    print('parsed_dir "%s"' % parsed_dir)
    
    for name in os.listdir(parsed_dir):
        print("  ?%s" % os.path.join(parsed_dir, name))
        match = gx_gen_regexp.match(name)
        if match:
            target_dir = os.path.join(parsed_dir, name)
            generate_source_from_gltf(target_dir, match)
