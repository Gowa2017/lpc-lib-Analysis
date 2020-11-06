from io import DEFAULT_BUFFER_SIZE
import os
import re
import sys
from graphviz import Digraph
import json
from config import INC_FMT, GLOBAL_INC_FMT, LIB_FMT

LIBPATH = None
INCLUDEPATH = None
GLOBALPATH = None
globals = dict()
dot = Digraph('')


def match(s):
    s = re.sub(r' +', ' ', s.replace('"', ''))
    return s.split(' ')


def parse_predefine(path, defs):
    with open(path) as f:
        for line in f:
            if line.startswith('#include'):
                if '<' in line:
                    parse_predefine(find_includefile(line.strip()), defs)
                    continue
            if line.startswith('#define'):
                s = re.sub(r' +', ' ', line.replace('"', '').strip('\n'))
                s = re.sub(r'\t+', ' ', s)
                fs = s.split(' ')
                for i in range(2, len(fs)):
                    for k, v in globals.items():
                        if k in fs[i]:
                            fs[i] = fs[i].replace(k, v)
                defs[fs[1]] = ''.join(fs[2:])
    return defs


def find_includefile(s):
    f = s
    m = re.search('<.*>', s)
    if m:
        f = s[m.span()[0]+1:m.span()[1]-1]
    for path in INCLUDEPATH.split(':'):
        if os.path.exists(LIBPATH+os.sep + path + os.sep + f):
            return LIBPATH+os.sep + path + os.sep+f


def parse_cfg(path):
    global LIBPATH
    global INCLUDEPATH
    global GLOBALPATH
    with open(path, 'r') as f:
        for line in f:
            m = re.search(INC_FMT, line)
            if m:
                INCLUDEPATH = m.group(1)
                continue
            m = re.search(GLOBAL_INC_FMT, line)
            if m:
                GLOBALPATH = m.group(1)
                continue
            m = re.search(LIB_FMT, line)
            if m:
                LIBPATH = find_lib_path(m.group(1))
                continue


def find_lib_path(dir):
    if dir.startswith('/'):
        return dir
    # 如果指定的目录是相对目录，那么要根据配置文件的路径来计算
    cfgdir = os.path.dirname(os.path.abspath(sys.argv[1]))
    p = cfgdir + os.sep + dir
    return os.path.abspath(p) if os.path.exists(p) else None


def postfix_filename(name):
    if name.endswith('.c'):
        return name
    return name+'.c'


def parse_inherit(path, level=0):
    path = postfix_filename(path)
    predefine = dict()
    parse_predefine(LIBPATH+path, predefine)
    defs = globals.copy()
    defs.update(predefine)
    # s = ''
    dot.node(path)
    with open(LIBPATH + os.sep + path, 'r') as f:
        for line in f:
            m = re.search("inherit\s+(\S+) *;", line)
            if m:
                inheritfile = defs[m.group(1)] if m.group(
                    1) in defs else m.group(1)
                print('\t|'*level+inheritfile+'\t'+m.group(1))
                dot.edge(path, postfix_filename(inheritfile))
                parse_inherit(inheritfile, level+1)
                # s = s+'"%s" -> "%s.c"\n' % (path, inheritfile)
                # s = s+parse_inherit(inheritfile, level+1)
    # return s


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('请指定 lib 的配置文件，和要解析的文件')
        exit(1)
    parse_cfg(sys.argv[1])
    if not LIBPATH:
        print('找不到LIB路径')
        exit(1)
    if not INCLUDEPATH:
        print('找不到头文件路径')
        exit(1)
    if not GLOBALPATH:
        print('找不到全局头文件')
        exit(1)
    print(LIBPATH, INCLUDEPATH, GLOBALPATH)
    print(sys.argv[2])
    parse_predefine(find_includefile(GLOBALPATH), globals)
    path = sys.argv[2] if sys.argv[2].startswith('/') else '/' + sys.argv[2]
    parse_inherit(path)
    # dot.render('res', view=True, format='svg')
    print(dot.source)
    dot.view()
