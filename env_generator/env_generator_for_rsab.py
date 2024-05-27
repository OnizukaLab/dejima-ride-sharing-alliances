import random
from graphviz import Graph
import json
import os
import sys
import shutil
import glob
import subprocess
import data_for_rsab
import re

if len(sys.argv) != 3:
    print("2 argument required")
    exit()
    
N = sys.argv[1]
if not N.isdigit() or int(N) < 1:
    print("Invalid argument.")
    exit()
N = int(N)

M = sys.argv[2]
if not M.isdigit() or int(M) < 1:
    print("Invalid argument.")
    exit()
M = int(M)

benchmark = "RSAB"

# colors = ['green', 'red', 'blue', 'black', 'orange']
colors = ['#332288', '#88CCEE', '#44AA99', '#117733', '#999933', '#DDCC77', '#CC6677', '#882255', '#AA4499', '#DDDDDD']
cond_n = len(colors)
#cond_n = 5

# legend
legend = Graph()
for i in range(1,cond_n+1):
    g = Graph()
    g.attr(rankdir='LR', rank='same')
    g.node('cond{}'.format(i), label='COND{}'.format(i), shape='plaintext')
    g.node('ph_cond{}'.format(i), label='', shape='plaintext')
    g.edge('cond{}'.format(i), 'ph_cond{}'.format(i), color=colors[i-1], style='bold')
    legend.subgraph(g)
for i in range(1, cond_n):
    legend.edge('cond{}'.format(i), 'cond{}'.format(i+1), style='invis')

# main
output_dir_path = '{}_N{}_M{}'.format(benchmark, N, M)
if os.path.isdir(output_dir_path):
    print("A same environment has already been created")
    exit()
os.mkdir(output_dir_path)

shutil.copytree('src/{}/db'.format(benchmark), '{}/db'.format(output_dir_path))
shutil.copytree('src/{}/proxy'.format(benchmark), '{}/proxy'.format(output_dir_path))

config = {'dejima_table': {}, 'base_table': {}, 'alliance_list': {}, 'peer_address': {}}

G = Graph(format='pdf')
G.attr('graph', rankdir='BT')
alliance_edges = {}
provider_edges = {}


# Node and Edge
# Alliance
for i in range(0,N+1):
    shutil.copytree('src/{}/Peer'.format(benchmark), '{}/db/setup_files/alliance{}'.format(output_dir_path, i))
    alliance_edges[i] = []
    G.node('A{}'.format(i))
    config['base_table']['alliance{}'.format(i)] = ['mt']
    config['peer_address']['alliance{}'.format(i)] = 'alliance{}-proxy:8000'.format(i)
    
# Alliance0 - Alliancek
for i in range(1,N+1):
    cond = random.randint(0, cond_n - 1)
    target_node = i
    G.edge('A0', 'A{}'.format(target_node), color=colors[cond], style='bold')
    dt_name = 'd0_{}'.format(target_node)
    config['dejima_table'][dt_name] = ['alliance0', 'alliance{}'.format(target_node)]
    alliance_edges[target_node].append(0)
    alliance_edges[0].append(target_node)

# Provider
for j in range(1,M+1):
    shutil.copytree('src/{}/Peer'.format(benchmark), '{}/db/setup_files/provider{}'.format(output_dir_path, j))
    provider_edges[j] = []
    G.node('P{}'.format(j))
    config['base_table']['provider{}'.format(j)] = ['bt']
    config['peer_address']['provider{}'.format(j)] = 'provider{}-proxy:8000'.format(j)
    # connect nodes
    al_list = []
    # n = random.randint(1, N)
    n = 2
    al_idx_list = list(range(1, N+1))
    target_node_list = random.sample(al_idx_list, n)
    for target_node in target_node_list:
        cond = random.randint(0, cond_n - 1)
        G.edge('P{}'.format(j), 'A{}'.format(target_node), color=colors[cond], style='bold')
        dt_name = 'd{}_{}'.format(target_node, j)
        config['dejima_table'][dt_name] = ['provider{}'.format(j), 'alliance{}'.format(target_node)]
        alliance_edges[target_node].append(j)
        provider_edges[j].append(target_node)
        al_list.append('AL{}'.format(target_node))
    config['alliance_list']['provider{}'.format(j)] = al_list


# Datalog
# Alliance
for i in alliance_edges:
    # 00_init.sql
    with open("{}/db/setup_files/alliance{}/00_init.sql".format(output_dir_path, i), mode="w") as f:
        if i == 0:
            f.write(data_for_rsab.init_sql_alliance0)
        else:
            f.write(data_for_rsab.init_sql_alliance)
        
    # 01_dnum.dl  (Alliancek)
    for j in alliance_edges[i]:
        dt_name = "d{}_{}".format(i, j)
        p_flag = "P={}".format(j)
        a_flag = "A={}".format(j)
        if j == 0:
            dt_name = "d0_{}".format(i)
        with open("{}/db/setup_files/alliance{}/01_{}.dl".format(output_dir_path, i, dt_name), mode="w") as f:
            datalog = data_for_rsab.birds_datalog_alliance
            if i == 0:
                f.write(data_for_rsab.birds_datalog_alliance0.replace("dt_name", dt_name).replace("a_flag", a_flag))
            elif j == 0:
                f.write(data_for_rsab.birds_datalog_alliancek.replace("dt_name", dt_name))
            else:
                f.write(datalog.replace("dt_name", dt_name).replace("p_flag", p_flag))

# Provider
for j in provider_edges:
    # 00_init.sql
    columns = []
    for i in provider_edges[j]:
        alliance = "AL{}".format(i)
        columns.append("    {} varchar,".format(alliance))
    columns = "\n".join(columns)
    with open("{}/db/setup_files/provider{}/00_init.sql".format(output_dir_path, j), mode="w") as f:
        f.write(data_for_rsab.init_sql_provider.replace("columns", columns))
        
    # 01_dnum.dl
    columns = []
    underscores = []
    alliances = []
    all_flags = []
    for i in provider_edges[j]:
        alliance = "AL{}".format(i)
        columns.append("'{}':string".format(alliance))
        underscores.append("_")
        alliances.append(alliance)
        all_flags.append("{}='false'".format(alliance))
    columns_ = ", ".join(columns)
    alliances_ = ",".join(alliances)
    underscores_ = ",".join(underscores)
    
    for k, i in enumerate(provider_edges[j]):
        dt_name = "d{}_{}".format(i, j)
        alliance = "AL{}".format(i)
        underscores[k] = alliance
        alliances[k] = "_"
        all_flags[k] = "{}='true'".format(alliance)
        
        underscores_alliance = ",".join(underscores)
        alliances_under = ",".join(alliances)
        all_flags_ = ", ".join(all_flags)
        alliance_flag = "{}='true'".format(alliance)
        
        with open("{}/db/setup_files/provider{}/01_{}.dl".format(output_dir_path, j, dt_name), mode="w") as f:
            datalog = data_for_rsab.birds_datalog_provider
            datalog = datalog.replace("underscores_alliance", underscores_alliance).replace("alliances_under", alliances_under)
            datalog = datalog.replace("columns", columns_).replace("underscores", underscores_).replace("alliances", alliances_)
            datalog = datalog.replace("alliance_flag", alliance_flag).replace("all_flags", all_flags_)
            f.write(datalog.replace("dt_name", dt_name))
            
        underscores[k] = "_"
        alliances[k] = alliance
        all_flags[k] = "{}='false'".format(alliance)
        
        
# 01_dnum.sql
for datalog in glob.glob("{}/db/setup_files/**/*.dl".format(output_dir_path), recursive=True):
    sql = "{}.sql".format(datalog[:-3])
    command = "birds -i -e -f {} -o {} --dejima -b src/{}/Peer/dejima_update.sh".format(datalog, sql, benchmark)
    print(command)
    subprocess.run(command, shell=True)

for filename in glob.glob("{}/db/setup_files/**/01_d*.sql".format(output_dir_path), recursive=True):
    with open(filename, 'r') as f:
        lines = f.readlines()
        
    patterns = []
    patterns.append(r'--DELETE FROM public.__dummy__(.*)_detected_deletions;')
    patterns.append(r'--DELETE FROM public.__dummy__(.*)_detected_insertions;')
    patterns.append(r'DROP TABLE IF EXISTS (.*)_detect_update_on_(.*)_flag;')
    replaces = []
    replaces.append([r'DELETE FROM public.__dummy__\1_detected_deletions t where t.txid = $1;'])
    replaces.append([r'DELETE FROM public.__dummy__\1_detected_insertions t where t.txid = $1;'])
    replaces.append([
        r'DROP TABLE IF EXISTS \1_detect_update_on_\2_flag;',
        r'    DROP TABLE IF EXISTS __tmp_delta_del_\1_for_\2;',
        r'    DROP TABLE IF EXISTS __tmp_delta_ins_\1_for_\2;'
    ])
    mask = [True] * len(patterns)
        
    for i, line in enumerate(lines):
        for j, (pattern, replace) in enumerate(zip(patterns, replaces)):
            if re.search(pattern, line) and mask[j] == True:
                replace_string = '\n'.join(replace)
                lines[i] = re.sub(pattern, replace_string, line)
                mask[j] = False    
    
    with open(filename, 'w') as f:
        f.writelines(lines)

with open(output_dir_path + '/proxy/dejima_config.json', mode='w', encoding='utf-8') as file:
    json.dump(config, file, ensure_ascii=False, indent=2)

with open(output_dir_path + '/src.dot', mode='w', encoding='utf-8') as file:
    file.write(G.source)

G.subgraph(legend)
G.render(output_dir_path + '/graph', cleanup=True)

# generate docker-compose.yml 

import yaml

yml = {}
yml['version'] = '3'

yml['services'] = {}
for i in range(0,N+M+1):
    if i <= N:
        peer_name_uc = "alliance{}".format(i)
        peer_name_lc = "alliance{}".format(i)
    else:
        peer_name_uc = "provider{}".format(i-N)
        peer_name_lc = "provider{}".format(i-N)

    # db
    db = yml['services'][peer_name_lc+'-db'] = {}
    db['image'] = 'ekayim/dejima-pg'
    db['container_name'] = peer_name_uc+'-db'
    # db['ports'] = ['{}:5432'.format(50000+i)]
    db['volumes'] = ['./db/postgresql.conf:/etc/postgresql.conf', './db/initialize.sh:/docker-entrypoint-initdb.d/initialize.sh', './db/setup_files:/etc/setup_files']
    db['environment'] = ['PEER_NAME={}'.format(peer_name_uc)]
    db['networks'] = {'dejima_net': None}
    db['cap_add'] = ['NET_ADMIN']

    # proxy
    proxy = yml['services'][peer_name_lc+'-proxy'] = {}
    proxy['image'] = 'ekayim/dejima-proxy:latest'
    proxy['container_name'] = peer_name_uc+'-proxy'
    proxy['command'] = 'gunicorn -b 0.0.0.0:8000 --threads {} server:app'.format(M+10)
    proxy['volumes'] = ['./proxy:/code']
    proxy['ports'] = ['{}:8000'.format(8000+i)]
    proxy['depends_on'] = ['{}-db'.format(peer_name_lc)]
    proxy['environment'] = ['PEER_NAME={}'.format(peer_name_uc)]
    proxy['networks'] = {'dejima_net': None}
    proxy['cap_add'] = ['NET_ADMIN']

yml['networks'] = {'dejima_net': {'driver': 'bridge', 'ipam': {'driver': 'default'}}}

with open(output_dir_path + '/docker-compose.yml', mode='w') as f:
    f.write(yaml.dump(yml))

print("complete")
