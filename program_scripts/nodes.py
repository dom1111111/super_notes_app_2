import json
from datetime import datetime
from os import path, listdir

# currently in the 'nodes' folder in same dir as this script
STORAGE_DIR = path.join(path.dirname(__file__), 'nodes')
DELETED_NODES_FILEPATH = path.join(STORAGE_DIR, 'deleted_nodes.json')


class ReadWriteNodes:
    def __init__(self):
        self.current_nodes_filepath = None
        self.time_str_format_1 = '%Y%m%d%H%M%S%f'
        self.time_str_format_2 = '%Y-%m-%d_%H:%M:%S:%f'
        self.year_month_str_format = '%Y%m'

        self.__setup_files()

    def __read_file(self, filepath) -> dict:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    
    def __write_file(self, filepath, content:dict):
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(content, file, indent=1)

    def __setup_files(self):
        # create current node storage file name by combining current year+month with '_nodes.json'
        f_name = datetime.now().strftime(self.year_month_str_format) + '_nodes.json'
        self.current_nodes_filepath = path.join(STORAGE_DIR, f_name)
        # if this file name does not exist in the storage folder, then create it with empty dict
        if not path.isfile(self.current_nodes_filepath):
            self.__write_file(self.current_nodes_filepath, {})
        # also create deleted nodes file if it doesn't exist yet
        if not path.isfile(DELETED_NODES_FILEPATH):
            self.__write_file(DELETED_NODES_FILEPATH, {})

    def __get_all_node_file_paths(self):
        node_files = []
        for file in listdir(STORAGE_DIR):
            # first check if the file is a json file
            is_json = file.endswith('.json')
            # then check that the file has a proper time name format
            time = file[0:6]
            try:
                time_valid = datetime.strptime(time, self.year_month_str_format)
            except:
                time_valid = False
            # if both are True, append to node_files
            if is_json and time_valid:
                filepath = path.join(STORAGE_DIR, file)
                node_files.append(filepath)
        return node_files

    def __find_filepath_for_node(self, id:str):
        # isolate year and month in timestamp from id
        node_time = datetime.strptime(id, self.time_str_format_1).strftime(self.year_month_str_format)
        # then match node_time to file_time
        for filepath in self.__get_all_node_file_paths():
            file_name = path.basename(filepath)
            file_time = file_name[0:6]
            if node_time == file_time:
                return filepath
    
    def __get_node_and_outside_data(self, id):
        filepath = self.__find_filepath_for_node(id)
        nodes = self.__read_file(filepath)
        content = nodes.get(id)
        return ({id: content}, nodes, filepath)

    #---

    def create_node(self, name:str, node_type:str='text', content:str=''):
        # create node:
        node_data = {       
            'name': name,       # should be a longer descriptive name, almost like a short description (makes it easier to find)
            'type': node_type,  # type of node - determines how content should be read
            'supe': [],         # super links
            'side': [],         # side links
            'sub':  [],         # sub links
            'cont': content     # the actual content of the node - can also be a file reference
        }
        id = datetime.now().strftime(self.time_str_format_1)    # creation time, also serves as id
        node = {id: node_data}
        # add node to storage file:
        filepath = self.current_nodes_filepath
        nodes = self.__read_file(filepath)
        nodes.update(node)
        self.__write_file(filepath, nodes)
    
    def get_node(self, id):
        node_and_data = self.__get_node_and_outside_data(id)
        node = node_and_data[0]
        return node

    def edit_node(self, id, content:list):
        # get all needed data
        node_and_data = self.__get_node_and_outside_data(id)
        nodes_dict = node_and_data[1]
        filepath = node_and_data[2]
        # update file with the new node/content
        new_node = {id: content}
        nodes_dict.update(new_node)
        self.__write_file(filepath, nodes_dict)

    def delete_node(self, id):
        # get all needed data
        node_and_data = self.__get_node_and_outside_data(id)
        node = node_and_data[0]
        nodes_dict = node_and_data[1]
        filepath = node_and_data[2]
        # remove deleted node from the nodes dict and update the file
        nodes_dict.pop(id)
        self.__write_file(filepath, nodes_dict)
        # then add deleted node to delete_nodes.json
        deleted_nodes_dict = self.__read_file(DELETED_NODES_FILEPATH)
        deleted_nodes_dict.update(node)
        self.__write_file(DELETED_NODES_FILEPATH, deleted_nodes_dict)

    def search_nodes(self, search:str):
        # search all node files for word matches, and order them by most to least
        search_words = search.lower().split()
        matches = []
        for filepath in self.__get_all_node_file_paths():
            nodes = self.__read_file(filepath)
            # search each node in each file:
            for id, content in nodes.items():           # nodes is a dict, and nodes.items() is a tuple (key,value) of each node
                match_count = 0
                for line in content:                    # content is a list, each line should be a string
                    for word in search_words:
                        n = line.lower().count(word)    # count how many times the word appears in line
                        match_count += n
                # if more than 0 words were matched, then append the match count, id, and content to matches
                if match_count:
                    matches.append((match_count, id, content))
        ordered_matches = sorted(matches, reverse=True) # sorted by default selects the first value of the tuples, which is convenient
        return ordered_matches
