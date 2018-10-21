import docker
from time import sleep

import db
import shell

client = docker.from_env()
NEST = {}
IMG = "rubyshadows/heartbeat:v1"

def clear_containers():
    '''
        TEMP FUNC: clears all containers from memory 
    '''
    for user_id, container in NEST.items():
        remove_container(user_id)


def heal_container(container):
    '''puts heart into container'''
    c_name = container.name

    filename = "heart"
    text = ""
    with open(filename, 'r') as fd:
        text = fd.read()
    row = 0
    col = 0

    file_obj = shell.create_file("1", filename, text, row, col)
    file_id = file_obj['fileid']
    file_name = file_obj['filename']
    file_type = file_obj['filetype']

    responding = check_container(c_name)
    if responding:
        shell.copy_file(c_name, file_id, file_name)
        has_heart = shell.extract_heart(c_name)
    else:
        has_heart = None

    return {"has_heart": has_heart}

def save_container(user):
    '''
        Commit and save container to dockerhub
    '''
    pass

def load_container(user):
    '''
        TODO: Pull container from dockerhub and return it
        If none on dockerhub, create new one
    '''
    if NEST.get(user.id) != None:
        return NEST.get(user.id);
    return new_container(user)


def new_container(user):
    '''
        Remove old container and create new one
    '''
    remove_container(user)
    NEST[user.id] = client.containers.run(IMG, detach=True) 
    user.container_name = NEST[user.id].name
    return NEST[user.id]

def user_container(user):
    '''
        Finds running container on machine and returns it
    '''
    return NEST.get(user.id)

def remove_container(user):
    '''
        Remove container from memory
    ''' 
    if NEST.get(user.id) == None:
        return
    else:
        container = NEST.get(user.id)
        # save_container(user)
        del NEST[user.id]
        container.remove(force=True)

def run(container, file_obj):
    '''
        Run file inside container, return output and hasHeart
    '''
    c_name = container.name
    file_id = file_obj['fileid']
    file_name = file_obj['filename']
    file_type = file_obj['filetype']

    copy_good = shell.copy_file(c_name, file_id, file_name)
    output = shell.execute_file(c_name, file_name, file_type)
    if output:
        output = output.decode('utf-8')
        print("output: {}".format(output))
    responding = check_container(c_name)
    if responding:
        has_heart = shell.extract_heart(c_name)
    else:
        has_heart = None

    material = 0

    if "python" in file_type:
        material = 6
    elif "bash" in file_type:
        material = 2
    else:
        material = 10

    if output is not None:
        if has_heart:
            pass
        else:
            material *= 10
    else:
        material = 0

    return {"output": output, "file_obj":file_obj, "has_heart": has_heart, "material": material}


def run_file(user, file_obj):
    '''
        Run a file within container, return output and hasHeart
    '''
    container = NEST.get(user.id)
    if not check_container(container.name):
        print("container not alive, resetting it")
        container = new_container(user.id)
    return run(container, file_obj)


def test_file(file_obj):
    """ Copy file into container, execute file in container, return output """
    testtube = client.containers.run(IMG, detach=True) 
    return run(testtube, file_obj)

def check_container(container_name):
    """ Checks whether container is running """
    container = client.containers.get(container_name)
    print("check_container: {}".format(container.status))
    if container.status == "running":
        return True
    else:
        return False
