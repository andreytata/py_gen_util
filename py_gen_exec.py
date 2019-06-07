#!/usr/bin/env python
# coding: utf-8

"""Execute rebuild source for each qmake pri projects at self parent folder.
All folders named as gx_gen_NAMESPACE_NAME, with gx_gen_NAMESPACE_NAME.pri, this
script find line with source glTF2.0 file. Folder can contain more then one file
used ".gltf" extention, generator must use only one, defined in projects *.pri
file."""

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
    if not os.path.isfile(gltf_file_path):
        raise IOError(gltf_file_path)
    namespace = match.groups()[0]
    target_pri = os.path.join(target_dir, "gx_gen_%s.pri" % namespace)
                                               # EXAMLE: 
    proj = QtGltfBuiltinPri( namespace  #'Slava_Rig_2'
        , gltf_file_path   #'C:/work/EXP61/devicea/gx_fbx_test/Slava_Rig_2014_2015_NEW.gltf'
        , target_dir       #'C:/WORK/GEN/gx_gen_Slava_Rig_2'
        , target_pri       #'C:/WORK/GEN/gx_gen_BoxTextured/gx_gen_Slava_Rig_2.pri'
    )
    proj.generate()

    print('  -o-END "%s"' % target_dir)



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