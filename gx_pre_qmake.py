#!/usr/bin/env python
# coding: utf-8

import sys
import os
import subprocess

print("\r\n")
print("-^-" * 20)
print("\r\n")
print(sys.version)
print("\r\n")
print(sys.argv[0])
gx_con_qmake = os.path.join(os.path.split( os.path.abspath( sys.argv[0]))[0], "gx_con_qmake.py")
print("\r\n")

if len(sys.argv) == 1:
    print("IS TEST ONLY, C:/WORK/GEN/gx_qt5_cube")
    import gx_con_qmake
    gx_con_qmake.main( os.path.normpath(os.path.split( os.path.abspath( sys.argv[0]))[0])
                     , os.path.normpath(os.path.abspath("../gx_qt5_cube" )))
else:
    print(sys.argv[1])
    print("\r\n")
    subprocess.call(
        "python %s %s" % (gx_con_qmake, sys.argv)
        , creationflags=subprocess.CREATE_NEW_CONSOLE)

print("CWD = '%s'" % os.getcwd())
print("\r\n")
print("-_-" * 20)
print("\r\n")
