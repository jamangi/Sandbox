#!/usr/bin/python3
from flask import Flask, request, jsonify
from flask_cors import CORS

import db
import nest
# nest = {}
from shell import create_file

app = Flask(__name__)
app.url_map.strict_slashes = False
cors = CORS(app, resources={r"/*": {"origins": "0.0.0.0"}})

####################################################################################
#### Debug Functions ####
@app.route('/clear_containers')
def clear():
    '''
        Removes containers from memory
    '''
    print("clearing containers")
    nest.clear_containers()
    return jsonify({'status': 'containers cleared'})

####################################################################################
#### Auth Functions ####
def bad_request(requirements):
    '''
        Validates input
    '''
    if not request.json:
        return {"msg": "not json", "error": True}
    for req in requirements:
        if not request.json.get(req):
            return {"msg": "no {}".format(req), "error": True}
    return None

def check_user():
    '''
        Verifies username and password
    '''
    requires = ["username", "password"] # moving
    failed = bad_request(requires)
    if failed is not None:
        return failed

    username = request.json['username']
    password = request.json['password']

    user = db.check_user(username, password)
    if user is None:
        return {"msg": "username or password not found"}
    else:
        return user

def return_user(user):
    '''
        Return a user dict without password
    '''
    ret = user.to_dict()
    del ret['password']
    return ret

def return_script(user, script):
    '''
        Return a script dict
    '''
    ret = script.to_dict()
    ret['user'] = return_user(user)
    return ret


##################################################################################
##### User Crud #####
@app.route('/')
def status():
    '''
        Status check
    '''
    return jsonify({"status": "ok"})

@app.route('/create', methods=['POST'])
def create_user():
    '''
        Creates new user
    '''
    requires = ["username", "password"]
    failed = bad_request(requires)
    if failed is not None:
        return jsonify(failed)

    username = request.json['username']
    password = request.json['password']
    character = "goku"
    
    user = db.create_user(username, password, character)
    if user is None:
        return jsonify({"msg":"username taken", "error": True})

    user.touch()
    return jsonify({"user" : return_user(user)})

@app.route('/get')
@app.route('/get/<username>')
def get_user(username=None):
    '''
        Gets user
    '''
    users = []
    if username is None:
        all_users = db.all('User')
        for user in all_users.values():
            users.append(return_user(user))
        return jsonify({'users': users})

    user = db.get_user(username)
    if user is None:
        return {"msg": "could not find user", "error": True}
    else:
        return {"user": user}

@app.route('/touch', methods=["POST"])
def touch():
    ''' Send alive signal '''
    user = check_user() #
    if type(user) == dict:
        return jsonify(user)
    print(type(user))

    requires = [] # #
    failed = bad_request(requires)
    if failed is not None:
        return jsonify(failed)

    user.touch() # # # #
    return jsonify({"user" : return_user(user)})

@app.route('/update', methods=["POST"])
def update_user():
    '''
        Update user in database
    '''
    user = check_user() # check user
    if type(user) == dict:
        return jsonify(user)

    requires = ["username", "password", "character", "location"] # # check require - user could be failure object
    failed = bad_request(requires)
    if failed is not None:
        return jsonify(failed)

    username = request.json['username'] # # # do algorithm
    password = request.json['password']
    character = request.json['character']

    user = db.update_user("User", user.id, username=username,
                          password=password, character=character,
                          location=location)
    if user is None:
        return jsonify({"msg":"update user error", "error": True})

    user.touch() # # # # return user, users, or scripts
    return jsonify({"user" : return_user(user)})

###############################################################################################
##### Routes #####
@app.route('/check', methods=["POST"])
def check_container():
    '''
        template code for route functions
    '''
    user = check_user() #
    if type(user) == dict:
        return jsonify(user)

    requires = [] # #
    failed = bad_request(requires)
    if failed is not None:
        return jsonify(failed)

    container = nest.get_container(user.id) # # #
    if container is None:
        return jsonify({"msg": "no container", "error": True})

    user.touch() # # # #
    return jsonify({"user" : return_user(user)})


###############################################################################################
### End of Refactor ###
###############################################################################################

@app.route('/collect', methods=["POST"])
def collect():
    ''' Execute inside user container and update database '''
    user = check_user() #
    if type(user) == dict:
        return jsonify(user)

    requires = ["fileid"] # #
    failed = bad_request(requires)
    if failed is not None:
        return jsonify(failed)

    fileid = request.json['fileid'] # # #
    if user.form == 'ghost':
        return jsonify({"msg": "you're a ghost", "error": True})
    script = db.get("Script", fileid)
    if script is None:
        return jsonify({"msg":"script not found", "error": True})

    filename = script.filename
    text = script.filetext
    row = script.row
    col = script.col
    is_bad_file = script.material >= 20
    author = db.get("User", script.user_id)

    if author.id == user.id:
        return jsonify({"msg": "script is yours", "error": True})

    if script.has_collected(user.id):
        return jsonify({"msg": "you've already collected this script", "error": True})
   

    container = nest.load_container(user.id) #/// 
    file_obj = create_file(filename, text, row, col)
    result = nest.run_file(user.id, file_obj) # upgrade to use create file internally

    if result["has_heart"] == None or result["has_heart"] == False:
        user.form = 'ghost'
        if is_bad_file:
            author.add_material(user.pay_material(script.material))
    else:
        user.form = user.character
        script.collect(user.id)
        if is_bad_file:
            user.add_material(script.material)
        else:
            user.add_material(script.material)
            author.add_material(script.material)
    db.save()

    result['script'] = script.to_dict();
    user.touch() # # # #
    return jsonify({"user" : return_user(user), "result": result})

@app.route('/drop', methods=["POST"])
def drop():
    ''' Test file and save it to database '''
    user_ip = request.remote_addr #
    user = db.get_user_by_ip(user_ip) 
    if user is None:
        return jsonify({"msg": "ip not set", "error": True})
    user.touch()

    requires = ["filename", "filetext", "row", "col"] # #
    if not request.json:
        return jsonify({"msg": "not json", "error": True})
    for req in requires:
        if not request.json.get(req):
            return jsonify({"msg": "no {}".format(req), "error": True})

    filename = request.json['filename'] # # #
    text = request.json['filetext']
    row = request.json['row']
    col = request.json['col']
    
    if user.form == 'ghost':
        return jsonify({"msg": "you're a ghost", "error": True})

    user.material += 1;
    file_obj = create_file(user_ip, filename, text, row, col)
    material = nest.test_file(file_obj) 
    # test file upgrades to use create file internally & return fileobj with material
    
    script = db.create("Script", user_id=user.id, material=material,
              filename=filename, filetext=text, filetype=file_obj['filetype'],
              row=row, col=col, location=user.location)
    db.save()
    return jsonify({"script" : return_script(user, script), "user": return_user(user)})


@app.route('/edit', methods=["POST"])
def edit():
    '''
        Edit a dropped script
    '''
    requires = ["fileid", "filename", "filetext"]
    user_ip = request.remote_addr
    user = db.get_user_by_ip(user_ip)
    if user is None:
        return jsonify({"msg": "ip not set", "error": True})

    user.touch()
    if not request.json:
        return jsonify({"msg": "not json", "error": True})

    for req in requires:
        if not request.json.get(req):
            return jsonify({"msg": "no {}".format(req), "error": True})

    script = db.get("Script", fileid)
    if script is None:
        return jsonify({"msg":"script not found", "error": True})
    author = db.get("User", script.user_id)
    if author.id != user.id:
        return jsonify({"msg": "script is not yours", "error": True})

    filename = request.json.get("filename")
    text = request.json.get("filetext")
    row = script.row
    col = script.col

    file_obj = create_file(user_ip, filename, text, row, col)
    material = nest.test_file(file_obj)

    script.filename = filename
    script.filetext = text
    script.material = material

    db.save()
    res = user.to_dict()
    del res['ip']
    script = new_file.to_dict()
    script['user'] = res
    return jsonify({"script" : script, "user": res})

#TODO: @app.route('/backup')

@app.route('/full_restore')
def full_restore():
    '''
        Replace user container
    '''
    user_ip = request.remote_addr
    user = db.get_user_by_ip(user_ip)
    if user is None:
        return jsonify({"msg": "ip not set", "error": True})
    nest.remove_container(user.id)
    container = nest.new_container(user.id)
    user.form = user.character
    db.save()
    user.touch()
    ret = user.to_dict()
    del ret["ip"]
    return jsonify({"user": ret, "container_name":container.name})

@app.route('/heal')
def heal():
    '''
        Puts heart file into user's container
    '''
    user_ip = request.remote_addr
    user = db.get_user_by_ip(user_ip)
    if user is None:
        return jsonify({"msg": "ip not set", "error": True})

    container = nest.user_container(user.id)
    if container == None:
        container = nest.new_container(user.id)
    has_heart = nest.heal_container(container)
    if has_heart == False:
        user.form = 'ghost'
    elif has_heart == None:
        user.form = user.form
    else:
        user.form = user.character
    db.save()
    user.touch()
    ret = user.to_dict()
    del ret["ip"]
    return jsonify({"user": ret})

@app.route('/load')
@app.route('/load/<location>')
def load_scripts(location=None):
    '''
        Loads scripts from memory
    '''
    all_scripts = []
    for script in db.get_scripts(location):
        s = script.to_dict()
        user = db.get("User", script.user_id)
        ret = user.to_dict();
        del ret['ip']
        s["user"] = ret
        all_scripts.append(s)
    return jsonify({"scripts": all_scripts})


@app.route('/run', methods=["POST"])
def run_script():
    '''
        Run's script inside own container
    '''
    requires = ["filename", "filetext"]
    if not request.json:
        return jsonify({"msg": "not json", "error": True})
    for req in requires:
        if not request.json.get(req):
            return jsonify({"msg": "no {}".format(req), "error": True})
    filename = request.json['filename']
    text = request.json['filetext']
    row = 0
    col = 0
    user_ip = request.remote_addr
    
    user = db.get_user_by_ip(user_ip) 
    if user is None:
        return jsonify({"msg": "ip not set", "error": True})
    
    user.touch()
    container = nest.load_container(user.id)
    file_obj = create_file(user_ip, filename, text, row, col)
    result = nest.run_file(user.id, file_obj)
    result['filename'] = filename;
    result['filetext'] = text;

    if result["has_heart"] == False:
        user.form = 'ghost'
    elif result["has_heart"] == None:
        user.form = user.form
    else:
        user.form = user.character

    db.save()
    ret = user.to_dict()
    del ret["ip"]
    return jsonify({"result": result, "user": ret})


@app.route('/start')
def start():
    '''
        Creates user container
    '''
    # search database for ip:id
    user_ip = request.remote_addr
    user = db.get_user_by_ip(user_ip)
    if user is None:
        return jsonify({"msg": "ip not set", "error": True})

    container = nest.load_container(user.id)
    user.touch()

    ret = user.to_dict()
    del ret["ip"]
    return jsonify({"user": ret, "container_name":container.name})

@app.route('/test', methods=["POST"])
def test():
    requires = ["filename", "filetext"]
    if not request.json:
        return jsonify({"msg": "not json", "error": True})
    for req in requires:
        if not request.json.get(req):
            return jsonify({"msg": "no {}".format(req), "error": True})
    print(request.json)
    filename = request.json['filename']
    text = request.json['filetext']
    row = request.json['row']
    col = request.json['col']
    user_ip = request.remote_addr
    file_obj = create_file(user_ip, filename, text, row, col)
    print("filename: {}\nfiletext: {}\nuser_ip: {} file_obj: {}".format(filename, 
                                                                        text, 
                                                                        user_ip, 
                                                                        file_obj))
    material = nest.test_file(file_obj)
    return jsonify({"material":material})


    

@app.after_request
def handle_cors(response):
    # allow access from other domains
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
