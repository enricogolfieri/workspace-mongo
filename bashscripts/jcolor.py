import os 
import sys
import json 
from termcolor import colored, cprint


def print_connpool(jsonline):
    cprint(f"### CONNPOOL {jsonline['attr']['hostAndPort']} - ctx:{jsonline['ctx']} msg:{jsonline['msg']}", 'white',file = sys.stdout)

def print_network(jsonline):
    cprint(f"### NETWORK - ctx:{jsonline['ctx']} msg:{jsonline['msg']}", 'white',file = sys.stdout) 


def print_shrefr(jsonline):
    cprint(f"SH_REFR - ctx:{jsonline['ctx']} msg:{jsonline['msg']} namespace:{jsonline['attr']['namespace']}", 'green',file = sys.stdout) 

colored_print = {
    "CONNPOOL": lambda x: print_connpool(x),
    "SH_REFR":  lambda x: print_shrefr(x),
    "NETWORK":  lambda x: print_network(x),
    "ELECTION": lambda x: cprint(x, 'grey', file = sys.stdout),
    "MIGRATE":  lambda x: cprint(x, 'magenta', file = sys.stdout),
    "SHARDING": lambda x: cprint(x, 'yellow', file = sys.stdout),
    "RESHARD":  lambda x: cprint(x, 'cyan', file = sys.stdout),
    "QUERY":    lambda x: cprint(x, 'blue', file = sys.stdout),
    "COMMAND":  lambda x: cprint(x, 'red', file = sys.stdout),
}


def colored_print_function(jsonline):
    if jsonline['s'] == 'E':
        cprint(f"### ERROR - ctx:{jsonline['ctx']} msg:{jsonline['msg']} attr:{jsonline['attr']}", 'white','on_red',file = sys.stdout)
    elif jsonline['s'] == 'W':
        cprint(f"### WARNING - ctx:{jsonline['ctx']} msg:{jsonline['msg']} attr:{jsonline['attr']}",'white','on_yellow',file = sys.stdout)
    elif jsonline['s'] == 'F':
        cprint(f"### FATAL - ctx:{jsonline['ctx']} msg:{jsonline['msg']} attr:{jsonline['attr']}", 'yellow','on_red',attrs=['bold'],file = sys.stdout)
    else:
        c = jsonline["c"]
        if c in colored_print:
            colored_print[c](jsonline)
        else:
            cprint(line,file=sys.stdout)


while True:
    line = os.sys.stdin.readline()
    if not line:
        break

    try:
        jsonline = json.JSONDecoder().decode(line)
        
        colored_print_function(jsonline)
    except json.decoder.JSONDecodeError as e:
        #if not json just print it 
        cprint(line,file=sys.stdout)
