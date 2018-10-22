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
@app.route('/')
def status():
    '''
        Status check
    '''
    return jsonify({"status": "ok"})

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
    requires = ["username", "password"] # #
    failed = bad_request(requires)
    if failed is not None:
        return failed

    username = request.json['username'] # # #
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
@app.route('/create', methods=['POST'])
def create_user():
    '''
        Creates new user
    '''
    requires = ["username", "password"] # #
    failed = bad_request(requires)
    if failed is not None:
        return jsonify(failed)

    username = request.json['username'] # # #
    password = request.json['password']
    even = len(username) % 2 == 0 
    character = "goku" if even else "titan"
    
    user = db.create_user(username, password, character)
    if user is None:
        return jsonify({"msg":"username taken", "error": True})

    user.touch()
    # # # #
    return jsonify({"user" : return_user(user)})

@app.route('/user')
@app.route('/user/<username>')
@app.route('/users')
@app.route('/users/<username>')
def get_user(username=None):
    '''
        Gets user
    '''
    users = [] # # #
    if username is None:
        all_users = db.all('User')
        for user in all_users.values():
            users.append(return_user(user))
        return jsonify({'users': users})

    user = db.get_user(username)
    if user is None:
        return jsonify({"msg": "could not find user", "error": True})
    else:
        # # # #
        return jsonify({"user" : return_user(user)})

@app.route('/touch', methods=["POST"])
def touch():
    ''' Send alive signal '''
    user = check_user() #
    if type(user) == dict:
        return jsonify(user)

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
    location = request.json['location']

    user = db.update("User", user.id, username=username,
                          password=password, character=character,
                          form=character, location=location)
    if user is None:
        return jsonify({"msg":"update user error", "error": True})

    user.touch()
    db.save()
    # # # # return user, users, scripts, or outputs
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

    container = nest.user_container(user) # # #
    if container is None:
        return jsonify({"msg": "no container", "error": True})

    user.touch() # # # #
    return jsonify({"user" : return_user(user)})

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
    author = db.get("User", script.user_id)

    if author.id == user.id:
        return jsonify({"msg": "script is yours", "error": True})

    if script.has_collected(user.id):
        return jsonify({"msg": "you've already collected this script", "error": True})
   

    is_bad_file = script.material >= 20
    container = nest.load_container(user)
    file_obj = create_file(filename, text, row, col)
    result = nest.run_file(user, file_obj)

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

    result['script'] = return_script(user, script)
    result['material'] = script.material
    user.touch()
    db.save()
    # # # #
    return jsonify({"user" : return_user(user), "result": result})

@app.route('/drop', methods=["POST"])
def drop():
    ''' Test file and save it to database '''
    user = check_user() #
    if type(user) == dict:
        return jsonify(user)

    requires = ["filename", "filetext", "row", "col"] # #
    failed = bad_request(requires)
    if failed is not None:
        return jsonify(failed)

    if user.form == 'ghost': # # #
        return jsonify({"msg": "you're a ghost", "error": True})

    filename = request.json['filename']
    text = request.json['filetext']
    row = request.json['row']
    col = request.json['col']

    user.material += 1;
    file_obj = create_file(filename, text, row, col)
    result = nest.test_file(file_obj) 
    material = result['material']
    script = db.create("Script", user_id=user.id, material=material,
              filename=filename, filetext=text, filetype=file_obj['filetype'],
              row=row, col=col, location=user.location)
    result['script'] = return_script(user, script)
    user.touch()
    db.save()
    # # # #
    return jsonify({"result" : result, "user": return_user(user)})


@app.route('/edit', methods=["POST"])
def edit():
    '''
        Edit a dropped script
    '''
    user = check_user() #
    if type(user) == dict:
        return jsonify(user)

    requires = ["fileid", "filename", "filetext"] # #
    failed = bad_request(requires)
    if failed is not None:
        return jsonify(failed)

    fileid = request.json.get("fileid")
    script = db.get("Script", fileid) # # #
    if script is None:
        return jsonify({"msg":"script not found", "error": True})

    author = db.get("User", script.user_id)
    if author.id != user.id:
        return jsonify({"msg": "script is not yours", "error": True})

    filename = request.json.get("filename")
    text = request.json.get("filetext")
    row = script.row
    col = script.col

    file_obj = create_file(filename, text, row, col)
    result = nest.test_file(file_obj)

    script.filename = filename
    script.filetext = text
    script.material = result['material']
    result['script'] = return_script(user, script)

    user.touch()
    db.save()
    # # # #
    return jsonify({"result" : result, "user": return_user(user)})

#TODO: @app.route('/backup')

@app.route('/full_restore', methods=["POST"])
def full_restore():
    '''
        Replace user container
    '''
    user = check_user() #
    if type(user) == dict:
        return jsonify(user)

    nest.remove_container(user) # # #
    container = nest.new_container(user)
    user.form = user.character
    user.touch()
    db.save()
    # # # #
    return jsonify({"user": return_user(user)})

@app.route('/heal', methods=["POST"])
def heal():
    '''
        Puts heart file into user's container
    '''
    user = check_user() #
    if type(user) == dict:
        return jsonify(user)

    container = nest.load_container(user) # # #
    has_heart = nest.heal_container(container)
    if has_heart == False:
        user.form = 'ghost'
    elif has_heart == None:
        user.form = user.form
    else:
        user.form = user.character
    user.touch()
    db.save()
    # # # #
    return jsonify({"user": return_user(user)})

@app.route('/load')
@app.route('/load/<location>')
def load_scripts(location=None):
    '''
        Loads scripts from memory
    '''
    all_scripts = [] # # #
    for script in db.get_scripts(location):
        user = db.get("User", script.user_id)
        s = return_script(script, user)
        all_scripts.append(s)
    # # # #
    return jsonify({"scripts": all_scripts})


@app.route('/run', methods=["POST"])
def run_script():
    '''
        Run's script inside own container
    '''
    user = check_user() #
    if type(user) == dict:
        return jsonify(user)

    requires = ["filename", "filetext"] # #
    failed = bad_request(requires)
    if failed is not None:
        return jsonify(failed)

    filename = request.json['filename'] # # #
    text = request.json['filetext']
    row = 0
    col = 0
    
    user.touch()
    container = nest.load_container(user)
    file_obj = create_file(filename, text, row, col)
    result = nest.run_file(user, file_obj)

    if result["has_heart"] == False:
        user.form = 'ghost'
    elif result["has_heart"] == None:
        pass
    else:
        user.form = user.character

    db.save()
    # # # #
    return jsonify({"result": result, "user": return_user(user)})


@app.route('/start')
def start():
    '''
        Creates user container
    '''
    user = check_user() #
    if type(user) == dict:
        return jsonify(user)

    container = nest.load_container(user) # # #
    user.touch()
    # # # #
    return jsonify({"user": return_user(user)})

@app.route('/test', methods=["POST"])
def test():
    requires = ["filename", "filetext"] # #
    failed = bad_request(requires)
    if failed is not None:
        return jsonify(failed)

    filename = request.json['filename'] # # #
    text = request.json['filetext']
    row = request.json['row']
    col = request.json['col']
    file_obj = create_file(filename, text, row, col)
    print("filename: {}\nfiletext: {} file_obj: {}".format(filename, text, file_obj))
    result = nest.test_file(file_obj)
    # # # #
    return jsonify({"result": result})


###############################################################################################
### End of routes ###
###############################################################################################

@app.after_request
def handle_cors(response):
    # allow access from other domains
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
