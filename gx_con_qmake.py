#!/usr/bin/env python
# coding: utf-8

import os, sys, re, json, pdb
from hashlib import md5
from pprint import pprint as pp
from gx_gltf_make import Gltf, DagTree, gxDagTree
from gx_cpp_glsl import QtGltfBuiltinPri

builtin = re.compile("""^#<BUILTIN>\\s*(.*)\\s*=\\s*(.*)\\s*$""", re.MULTILINE)

def generate_skin(PWD, GTX, KEY, VBO, vertices, IBO, indices ):
    name = GTX.source.gltf.path
    print()

def generate_mesh(PWD, GTX, KEY, VBO, vertices, IBO, indices ):
    name = GTX.source.gltf.path
    print()

def generate_from_file( NAME, PATH, PWD ):
    """ This generator use each gltf-file, as source to build
    1. Target folder named gx_gen_%%get_file_name%%
    2. QT-pri file named gx_gen_%%get_file_name%%.pri
    3. CPP-header file for each skin and each mesh in target folder
    4. Separate class for each skin and mesh in source GLTF file
    5. Copy all textures referenced in source GLTF file
    6. Single qrc file with references to each texture in target folder
    gx_gen_%%get_file_name%%                  // folder as 'PWD/..'
       gx_gen_%%get_file_name%%.pri           // QT project include file
       gx_gen_geometry_%%get_file_name%%.h    // 
       gx_gen_builtins_%%get_file_name%%.cpp  // 
       gx_gen_textures_%%get_file_name%%.qrc  // 
    """
    NAME = NAME.strip()
    PATH = os.path.normpath(os.path.abspath(PATH))  # PATH TO SOURCE GLTF FILE
    GEN_DIR = os.path.join(os.path.split(PWD)[0], 'gx_gen_' + NAME)
    if not os.path.isdir(GEN_DIR):
        os.makedirs(GEN_DIR)
    GEN_PRI = os.path.join(GEN_DIR, 'gx_gen_' + NAME + '.pri')

    # TRY TO EXTRACT ALL STORED MD5-s FROM EXISTED PRI FILE
    gltf_txt_md_line = '#'
    gltf_bin_md_line = '#'
    try:
        with open(GEN_PRI, "r") as gen_pri_file:
            gltf_txt_md_line = gen_pri_file.readline()
            gltf_bin_md_line = gen_pri_file.readline()
    except IOError:
        with open(GEN_PRI, "w") as gen_pri_file:
            print("GENERATE: dst PRI-file recreated '%s'" % GEN_PRI )
    
    cpp_generator = QtGltfBuiltinPri(NAME,PATH,GEN_DIR,GEN_PRI)
    cpp_generator.rebuild_all()
    return

    # TRY COMPUTE MD5 GLTF SOURCE TEXT FILE
    try:
        with open(PATH, "r") as src_gltf_text_file:
            gltf_json = src_gltf_text_file.read()
            curr_gltf_txt_md = md5(gltf_json).hexdigest()
    except IOError:
        print("GENERATE: src GLTF-file not found '%s'" % PATH )
        return
    

    print("%s for %s" % (NAME, PWD) )

    ## ALL NEXT LINES MUST BE INCAPCULATED IN class GxBuiltinPri(SRC, PRI, NAME)
    gltf = Gltf(PATH)
    dag  = DagTree(gltf)
    gxt  = gxDagTree(dag)
    print("  skin count %d" % len(gltf.skins))
    print("  mesh count %d" % len(gltf.meshes))
    print("  mtrl count %d" % len(gltf.materials))
    mesh_keys = set(gxt.get_mesh_keys())
    for i in mesh_keys:
        vertex_attributes =  gxt.get_mesh_attributes(i)
        method_name = 'get_interleaved_'
        mode = ('mesh', 'skin') [ u'WEIGHTS_0' in vertex_attributes ]
        print("  %s[%s] %s %s" % (mode, i, gxt.get_mesh_name(i), vertex_attributes))
        if u'POSITION'   in vertex_attributes: method_name += 'P3'
        if u'NORMAL'     in vertex_attributes: method_name += 'N3'
        if u'WEIGHTS_0'  in vertex_attributes: method_name += 'W4'
        if u'JOINTS_0'   in vertex_attributes: method_name += 'J4'
        if u'TEXCOORD_0' in vertex_attributes: method_name += 'T2'
        print("           %s" % method_name)
        method = getattr(gxt, method_name)
        vertices, vbo = method(i)
        indices,  ibo = gxt.get_indices_PP()
        if mode == 'skin':
            generate_skin( PWD, gxt, i, vbo, vertices, ibo, indices)
        else:
            generate_mesh( PWD, gxt, i, vbo, vertices, ibo, indices)
    print()

def generate(PWD, CWD, PRO, SRC):
    print(PWD)
    print(CWD)
    print(PRO)
    builtins = dict([ match.groups() for match in re.finditer(builtin, SRC) ])
    pp(builtins, width=1)
    for project_name in sorted(builtins.keys()):
        name = project_name
        path = builtins[project_name]
        generate_from_file(name, path, PWD)
    print()

def main(sources_dir, project_dir, rebuild_all = False):

    # WHERE IS QMAKE(META OBJECT COMPILER) PROJECT-FILE CALLED THIS GENERATOR
    PWD    = project_dir
    print("PWD    = %s"%PWD)

    # WHERE IS THIS FILE's PARENT FOLDER
    CWD    = sources_dir
    print("CWD    = %s"%CWD)

    # ONLY ONE '.pro' FILE SUPPORTED
    PRO    = os.path.join(PWD, [ i for i in os.listdir(PWD) if i.endswith(".pro") ][0] )
    print("PRO    = %s"%PRO)

    # READ '.pro' FILE
    SRC    = open(PRO,"r").read()

    # for i in os.listdir(PWD): print(i)

    # COMPUTE '.pro' FILE MD5
    MD5    = md5(SRC).hexdigest()

    # TRY TO EXTRACT STORED_MD5
    STORED_MD5 = ''
    try:
        with open(PRO+".builtins", "r") as f:
            STORED_MD5 = json.loads(f.read())['MD5']
    except IOError   : print("GENERATE: '.builtins' file not found")
    except KeyError  : print("GENERATE, 'md5' not stored in '.builtins' file")
    except ValueError: print("GENERATE, '.builtins' file invalid")

    # COMPARE CURRENT MD5 WITH STORED_MD5
    if STORED_MD5 == MD5:
        if rebuild_all:
            print("GENERATE: MD5 ARE EQUAL, BUT rebuild_all == True")
        else:
            print("GENERATE: MD5 ARE EQUAL, SKIPPED")
            return

    print("GENERATE BEGIN")
    session = dict()
    session['MD5'] = MD5
    session['PWD'] = PWD
    session['CWD'] = CWD

    generate( PWD, CWD, PRO, SRC )  # ALL GLTF-TO-PRI CONVERTER

    with open(PRO+".builtins", "w") as f:
        f.write(json.dumps(session, sort_keys=True, indent=4, separators=(',', ':')))

    print("GENERATE END")

if __name__ == '__main__':

    if len(sys.argv) == 1:
        rebuild = True                      # TEST/DEBUG CASE force rebuild.
        generator_source = os.path.normpath(os.path.abspath(sys.argv[0]))
        generator_source_dir = os.path.split(sys.argv[0])[0]
        test_project_folder = os.path.join(os.path.split(generator_source_dir)[0], "gx_qt5_cube")
        sys.argv.append(test_project_folder)   # SO, IS TEST/DEBUG CASE.
    else:
        rebuild = False

    sources_dir = os.path.normpath(os.path.split(os.path.abspath(sys.argv[0]))[0])
    project_dir = os.path.normpath(os.path.abspath(sys.argv[1]))
    main( sources_dir, project_dir, rebuild )
