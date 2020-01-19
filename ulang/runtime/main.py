# decompyle3 version 3.3.2
# Python bytecode 3.7 (3394)
# Decompiled from: Python 3.8.1 (default, Jan  3 2020, 22:44:00) 
# [GCC 8.3.0]
# Embedded file name: ulang\runtime\main.py
# Size of source mod 2**32: 82682 bytes
import ast, dis, imp, os, sys, getopt, time, threading, trace
from datetime import datetime
from ulang.runtime.env import create_globals
from ulang.runtime.repl import repl
from ulang.parser.core import Parser
from ulang.parser.lexer import lexer
from ulang.codegen import blockly, python, ulgen

def usage(prog):
    info = '''usage: %s [-apbcidsDth] input_file
Options and arguments:
 --dump-ast,        -a   dump ast info
 --dump-python,     -p   dump python source code
 --dump-blockly,    -b   dump blockly xml (experimental)
 --dump-bytecode,   -c   dump donsok bytecode (experimental)
 --python-to-ulang, -s   convert python to ulang
 --debug,           -D   debug with Pdb (experimental)
 --interact,        -i   inspect interactively after running script
 --disassemble,     -d   disassemble the python bytecode
 --exec-code=<code> -e   run code from cli argument
 --show-backtrace,  -t   show backtrace for errors
 --version,         -v   show the version
 --help,            -h   show this message
'''
    sys.stderr.write(info % os.path.basename(prog))
    sys.exit(-1)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    try:
        opts, args = getopt.getopt(argv[1:], 'hdapbctisDTe:v', [
            'dump-ast',
            'dump-python',
            'dump-blockly',
            'dump-bytecode',
            'dump-tokens',
            'python-to-ulang',
            'exec-code=',
            'debug',
            'disassemble',
            'show-backtrace',
            'help',
            'version',
            'interact'])
            
    except getopt.GetoptError as e:
        try:
            sys.stderr.write(str(e) + '\n')
            usage(argv[0])
        finally:
            e = None
            del e
    
    input_file = None
    dump_ast = False
    dump_python = False
    dump_blockly = False
    dump_bytecode = False
    dump_tokens = False
    disassemble = False
    trace_exception = False
    interactive = False
    python2ulang = False
    exec_code = None
    debug = False
    for opt, value in opts:
        if opt in ('-i', '--interact'):
            interactive = True
        elif opt in ('-p', '--dump-python'):
            dump_python = True
        elif opt in ('-a', '--dump-ast'):
            dump_ast = True
        elif opt in ('-b', '--dump-blockly'):
            dump_blockly = True
        elif opt in ('-c', '--dump-bytecode'):
            dump_bytecode = True
        elif opt in ('-d', '--disassemble'):
            disassemble = True
        elif opt in ('-s', '--python-to-ulang'):
            python2ulang = True
        elif opt in ('-D', '--debug'):
            debug = True
        elif opt in ('-t', '--show-backtrace'):
            trace_exception = True
        elif opt in ('-T', '--dump-tokens'):
            dump_tokens = True
        elif opt in ('-e', '--exec-code'):
            exec_code = value
        elif opt in ('-v', '--version'):
            from ulang import __version__
            sys.stderr.write('%s\n' % __version__)
            sys.exit()

    if len(argv) == 1:
        sys.exit(repl())

    if len(args) > 0:
        input_file = args[0]

    if input_file is None:
        if len(argv) == 1:
            sys.exit(repl())
        if not exec_code:
            usage(argv[0])
    try:
        source = None
        if exec_code:
            source = exec_code
            input_file = '<CLI>'
        elif input_file == '-':
            source = sys.stdin.read()
            input_file = '<STDIN>'
        else:
            with open(input_file, 'r') as f:
                source = f.read()
        if not source:
            sys.stderr.write('cannot open file "%s"!\n' % input_file)
            sys.exit(-1)
        
        if python2ulang:
            nodes = ast.parse(source, input_file)
            print(ulgen.dump(nodes))
            return

        if dump_tokens:
            tokens = lexer.lex(source)
            for token in tokens:
                print((token.gettokentype()), end=' ')

            return
        parser = Parser()
        nodes = parser.parse(source, input_file)
        if dump_ast:
            print(ast.dump(nodes, True, True))
            return
        if dump_python:
            print(python.dump(nodes))
            return
        if dump_blockly:
            print(blockly.dump(nodes))
            return
        if dump_bytecode:
            from pygen.compiler import Compiler
            print(Compiler().compile(nodes, input_file).dump())
            return
        code = compile(nodes, input_file, 'exec')
        if disassemble:
            dis.dis(code)
            return
        
        globals = create_globals(argv=(args[1:]),
            fname=input_file)
        if debug:
            import pdb
            while True:
                try:
                    pdb.run(code, globals, None)
                except pdb.Restart:
                    pass
                else:
                    break
        else:
            exec(code, globals)
        if interactive:
            repl(globals=globals)
    except Exception as e:
        try:
            sys.stderr.write('%s: %s\n' % (e.__class__.__name__, str(e)))
            if trace_exception:
                import pdb
                extype, value, tb = sys.exc_info()
                pdb.post_mortem(tb)
                raise e
        finally:
            e = None
            del e