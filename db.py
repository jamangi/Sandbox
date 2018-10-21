import models
from models.base_model import BaseModel
from models.user import User
from models.script import Script
from models.map import Map


def check_user(username, password):
	'''
		Checks for username password combination in database
	'''
	return User.check_user(username, password)

def all(cls):
	'''
		Returns all instances of class
	'''
	return models.storage.all(cls)

def get_user(username):
	'''
		Gets user from database
	'''
	return User.get_user(username)

def create_user(username, password, character):
	'''
		Creates new user in database
	'''
	user = get_user(username)
	if user is not None:
		print("** user already exists **")
		return None
	new_user = create("User", username=username, character=character, form=character)
	new_user.save()
	return new_user


def create(classname, **kwargs):
	'''
		Create a new instance of class BaseModel and saves it
		to the JSON file.
	'''
	try:
		new_instance = eval(classname)()
		for key, value in kwargs.items():
		    setattr(new_instance, key, value)
		new_instance.save()
		return new_instance

	except Exception as e:
		print("** create instance error **")
		print(e)
		return None
def get(classname, id):
	'''
		Get object by id
	'''
	instance = models.storage.get(classname, id)
	return instance

def get_scripts(location=None):
	'''
		Searches for scripts in given location
	'''
	result = Script.get_scripts(location)
	return result

def update(cls, uid, **kwargs):
	'''
		Update instance to have desired attributes
	'''
	instance = models.get(cls, uid)
	if instance is None:
		print("** no instance found **")
		return None
	try:
		for key, value in kwargs.items():
			setattr(instance, key, value)
		instance.save()
		return instance

	except Exception as e:
		print("** update instance error **")
		return None

def save():
	'''
		Saves changes to db
	'''
	models.storage.save()
