# -*- coding: utf-8 -*-

###################################################################################################
# Add this directory to sys.path
###################################################################################################
import os, inspect, sys, shutil
sys.path.append(os.path.dirname(__file__))

###################################################################################################
# Import things
###################################################################################################
import bottle, sqlalchemy, beaker
import beaker.middleware
from bottle import default_app, debug, run, static_file,\
    request, TEMPLATE_PATH, template, route, get, post, put, delete, error, hook, Bottle
        
###################################################################################################
# Hacks
###################################################################################################  
# Python 3 hack for xrange
if sys.version_info >= (3,0,0):
    xrange = range
# Intellisense hack
if 0:
    request.SESSION = []
###################################################################################################

@hook('before_request')
def _before_request():
    request.SESSION = request.environ['beaker.session']

@route('/<path:re:(favicon.ico)>')
@route('/assets/<path:re:.+>')
def _serve_assets(path):
    return static_file(path, root=os.path.join('.runtime', 'assets'))

def rmtree(path, ignore_errors=False, onerror=None):
    shutil.rmtree(path, ignore_errors, onerror)

def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or os.stat(src).st_mtime - os.stat(dst).st_mtime > 1:
                shutil.copy2(s, d)

def _sort_names(names=[], key=None):
    index_exists, empty_exists  = False, False
    index_obj, empty_obj        = None, None
    index_identifier = ['index', 'action_index']
    empty_identifier = ['', 'action', 'action_']
    # remove some special element
    for i in xrange(len(names)):
        # get identifier
        if key is None:
            identifier = names[i]
        else:
            identifier = names[i][key]
        # check identifier
        if identifier in index_identifier:
            index_obj = names[i]
            index_exists = True
        if identifier in empty_identifier:
            empty_obj = names[i]
            empty_exists = True
        # exit from loop
        if index_exists and empty_exists:
            break
    if index_exists:
        names.remove(index_obj)
    if empty_exists:
        names.remove(empty_obj)
    #sort the other normal elements
    names.sort(key = len, reverse=True)    
    # re add those removed special element
    if index_exists:
        names.append(index_obj)
    if empty_exists:
        names.append(empty_obj)
    # return
    return names

def _get_basic_routes(directory, controller, function):
    basic_routes = []    
    # basic routes    
    if not function == '':
        basic_routes.append('/'+directory+'/'+controller+'/'+function)
    if function == '' or function == 'index':
        basic_routes.append('/'+directory+'/'+controller)
    if controller == '' or controller == 'index':
        if not function == '':
            basic_routes.append('/'+directory+'/'+function)
        if function == '' or function == 'index':
            basic_routes.append('/'+directory)            
    if directory == '' or directory == 'index':
        if not controller == '':
            if not function == '':
                basic_routes.append('/'+controller+'/'+function)
            if function == '' or function == 'index':
                basic_routes.append('/'+controller)
        if controller == '' or controller == 'index':
            if function != '':
                basic_routes.append('/'+function)
            if function == '' or function == 'index':
                basic_routes.append('')
    # return
    return basic_routes

def _get_routes(directory, controller, function, parameters):
    basic_routes = _get_basic_routes(directory, controller, function)    
    # parameter patterns
    parameter_patterns = []
    for parameter in parameters:
        parameter_patterns.append('<'+parameter+'>')
    # complete routes
    routes = []
    for basic_route in basic_routes:
        for i in reversed(xrange(len(parameter_patterns))):
            parameter_segment = "/".join(parameter_patterns[:i+1])
            routes.append(basic_route+'/'+parameter_segment)
        routes.append(basic_route)
        routes.append(basic_route+'/')
    # return
    return routes
    
def kokoro_init(**kwargs):
    """ Start a server instance. This method blocks until the server terminates.

        :param app: WSGI application or target string supported by
               :func:`load_app`. (default: :func:`default_app`)
        :param server: Server adapter to use. See :data:`server_names` keys
               for valid names or pass a :class:`ServerAdapter` subclass.
               (default: `wsgiref`)
        :param host: Server address to bind to. Pass ``0.0.0.0`` to listens on
               all interfaces including the external one. (default: 127.0.0.1)
        :param port: Server port to bind to. Values below 1024 require root
               privileges. (default: 8080)
        :param reloader: Start auto-reloading server? (default: False)
        :param interval: Auto-reloader interval in seconds (default: 1)
        :param quiet: Suppress output to stdout and stderr? (default: False)
        :param options: Options passed to the server adapter.
     """
    ###################################################################################################
    # kwargs arguments
    ###################################################################################################
    APPLICATION_PATH    = kwargs.pop('application_path',    './applications'    )
    APP                 = kwargs.pop('app',                 bottle.app()        )
    SERVER              = kwargs.pop('server',              'wsgiref'           )
    DEBUG               = kwargs.pop('debug',               True                )
    PORT                = kwargs.pop('port',                8080                )
    RELOADER            = kwargs.pop('reloader',            True                )
    HOST                = kwargs.pop('host',                '127.0.0.1'         )
    QUIET               = kwargs.pop('quiet',               False               )
    INTERVAL            = kwargs.pop('interval',            1                   )
    PLUGINS             = kwargs.pop('plugins',             None                )
    ###################################################################################################
    # parameters
    ###################################################################################################
    APPLICATION_PACKAGE = os.path.split(APPLICATION_PATH)[-1]
    CURRENT_PATH        = os.path.split(APPLICATION_PATH)[0]
    RUNTIME_PATH        = os.path.join(CURRENT_PATH,'.runtime')
    ###################################################################################################
    # prepare runtime path
    ###################################################################################################
    print ('PREPARE RUNTIME PATH')
    if not os.path.exists(RUNTIME_PATH):
        os.makedirs(RUNTIME_PATH)
    ###################################################################################################
    # get all kokoropy module directory_list
    ###################################################################################################
    # init directory_list
    print ('INIT APPLICATION DIRECTORIES')
    directory_list = []
    for directory in os.listdir(APPLICATION_PATH):
        if os.path.isfile(os.path.join(APPLICATION_PATH, directory, '__init__.py')) and \
        os.path.isfile(os.path.join(APPLICATION_PATH, directory, 'controllers', '__init__.py')) and \
        os.path.isdir(os.path.join(APPLICATION_PATH, directory, 'views')):
            directory_list.append(directory)
    directory_list = _sort_names(directory_list)    
    ###################################################################################################
    # get directory controller modules
    ###################################################################################################
    # controller_module_directory_list is a dictionary with directory name as key 
    # and array of controller as value
    controller_module_directory_list = {}
    for directory in directory_list:
        for file_name in os.listdir(APPLICATION_PATH+'/'+directory+'/controllers'):
            # get module inside directory's controller
            file_name_segments = file_name.split('.')
            first_segment = file_name_segments[0]
            last_segment = file_name_segments[-1]
            if (first_segment == '__init__') or (not last_segment == 'py'):
                continue
            module_name = inspect.getmodulename(file_name)
            if module_name is None:
                continue
            if not directory in controller_module_directory_list:
                controller_module_directory_list[directory] = []
            controller_module_directory_list[directory].append(module_name)    
    ###################################################################################################
    # Load everything inside controller modules
    ###################################################################################################
    exec('import '+APPLICATION_PACKAGE)
    for directory in controller_module_directory_list:
        for controller_module in controller_module_directory_list[directory]:
            # load everything inside the controllers
            print('LOAD CONTROLLER : '+controller_module)
            exec('from '+APPLICATION_PACKAGE+'.'+directory+'.controllers.'+controller_module+' import *')                
    ###################################################################################################
    # Load Default_Controller inside controller modules
    ###################################################################################################
    for directory in controller_module_directory_list:
        for controller_module in controller_module_directory_list[directory]:
            module_obj = None
            exec('import '+APPLICATION_PACKAGE+'.'+directory+'.controllers.'+controller_module+' as module_obj')
            members = inspect.getmembers(module_obj, inspect.isclass)
            # determine if default_controller exists
            default_controller_found = False
            Default_Controller = None
            for member in members:
                if member[0] == 'Default_Controller':
                    default_controller_found = True
                    Default_Controller = member[1]
                    break
            # skip if there is no default_controller
            if not default_controller_found:
                continue
            # make an instance of Default_Controller
            controller = Default_Controller()            
            methods = inspect.getmembers(controller, inspect.ismethod)
            methods = _sort_names(methods, 0)
            for method in methods:
                method_name = str(method[0])
                method_object = method[1]
                name_segments = method_name.split('_')
                # ignore functions without "action" prefix
                if not name_segments[0] == 'action':
                    continue 
                method_published_name = "_".join(name_segments[1:])
                parameters = inspect.getargspec(method_object)[0][1:]
                routes = _get_routes(directory, controller_module, method_published_name, parameters)
                for single_route in routes:
                    route(single_route)(method_object)
                    get(single_route)(method_object)
                    post(single_route)(method_object)
                    put(single_route)(method_object)
                    delete(single_route)(method_object)
    ###################################################################################################
    # add template & assets path
    ###################################################################################################
    global_view_path = os.path.join(RUNTIME_PATH, 'views')
    global_asset_path = os.path.join(RUNTIME_PATH, 'assets')
    rmtree(global_view_path)
    rmtree(global_asset_path)
    # application's assets & views
    for directory in directory_list:
        print('REGISTER TEMPLATE PATH : '+directory+'/views/')
        old_path = os.path.join(APPLICATION_PATH, directory, 'views')
        app_view_path = os.path.join(global_view_path, directory)
        copytree(old_path, app_view_path)
        print('REGISTER ASSETS PATH : '+directory+'/assets/')
        old_path = os.path.join(APPLICATION_PATH, directory, 'assets')
        app_view_path = os.path.join(global_asset_path, directory)
        copytree(old_path, app_view_path)
    # global assets
    old_path = os.path.join(APPLICATION_PATH, 'assets')
    copytree(old_path, global_asset_path)
    # register template path
    TEMPLATE_PATH.append(global_view_path)
    ###################################################################################################
    # run the application
    ###################################################################################################
    session_opts = {
        'session.type': 'file',
        'session.data_dir': os.path.join(RUNTIME_PATH,'session'),
        'session.auto': True,
    }
    app = beaker.middleware.SessionMiddleware(APP, session_opts)
    port = int(os.environ.get("PORT", PORT))
    run(app=app, server=SERVER, reloader=RELOADER, host=HOST, 
        port=port, quiet=QUIET, interval=INTERVAL, debug=DEBUG, plugins=PLUGINS, **kwargs)