# -*- coding: utf-8 -*-

###################################################################################################
# Add this directory to sys.path
###################################################################################################
import os, inspect, sys
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
py   = sys.version_info
py3k = py >= (3,0,0)
if py3k:
    xrange = range
# Intellisense hack
if 0:
    request.SESSION = []
################################################################################################### 

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

def _application_static(path):
    return static_file(path, root='application/assets')

def _module_static(module_path, path):
    return static_file(path, root='application/'+module_path+'/assets')

def _pop_dynamic_argument(kwargs, key, default_value):
    if key in kwargs:
        value = kwargs[key]
        del kwargs[key]
    else:
        value = default_value
    return value, kwargs

@hook('before_request')
def _setup_request():
    request.SESSION = request.environ['beaker.session']

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
    # arguments
    ###################################################################################################
    APP,            kwargs = _pop_dynamic_argument(kwargs, 'app',           bottle.app()    )
    SERVER,         kwargs = _pop_dynamic_argument(kwargs, 'server',        'wsgiref'       )
    DEBUG,          kwargs = _pop_dynamic_argument(kwargs, 'debug',         True            )
    PORT,           kwargs = _pop_dynamic_argument(kwargs, 'port',          8080            )
    RELOADER,       kwargs = _pop_dynamic_argument(kwargs, 'reloader',      True            )
    HOST,           kwargs = _pop_dynamic_argument(kwargs, 'host',          '127.0.0.1'     )
    ERROR_HANDLER,  kwargs = _pop_dynamic_argument(kwargs, 'error_handler', {}              )
    QUIET,          kwargs = _pop_dynamic_argument(kwargs, 'quiet',         False           )
    INTERVAL,       kwargs = _pop_dynamic_argument(kwargs, 'interval',      1               )
    PLUGINS,        kwargs = _pop_dynamic_argument(kwargs, 'plugins',       None            )
    ###################################################################################################
    # get all kokoropy module directory_list
    ###################################################################################################
    # init directory_list
    print ('INIT APPLICATION DIRECTORIES')
    directory_list = []
    for directory in os.listdir('./application'):
        if os.path.isfile(os.path.join('./application', directory, '__init__.py')) and \
        os.path.isfile(os.path.join('./application', directory, 'controllers', '__init__.py')) and \
        os.path.isdir(os.path.join('./application', directory, 'views')):
            directory_list.append(directory)
    directory_list = _sort_names(directory_list)    
    ###################################################################################################
    # get directory controller modules
    ###################################################################################################
    # controller_module_directory_list is a dictionary with directory name as key 
    # and array of controller as value
    controller_module_directory_list = {}
    for directory in directory_list:
        for file_name in os.listdir('./application/'+directory+'/controllers'):
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
    for directory in controller_module_directory_list:
        for controller_module in controller_module_directory_list[directory]:
            # load everything inside the controllers
            print('LOAD CONTROLLER : '+controller_module)
            exec('from application.'+directory+'.controllers.'+controller_module+' import *')                
    ###################################################################################################
    # Load Default_Controller inside controller modules
    ###################################################################################################
    for directory in controller_module_directory_list:
        for controller_module in controller_module_directory_list[directory]:
            module_obj = None
            exec('import application.'+directory+'.controllers.'+controller_module+' as module_obj')
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
    # serve application's static file
    ###################################################################################################
    print('ADD STATIC FILE ROUTE : /favicon.ico, /human.txt')
    print('ADD STATIC FILE ROUTE: "/assets/*"')
    route('/<path:re:(favicon.ico|humans.txt)>')(_application_static)
    route('/assets/<path:re:.+>')(_application_static)
    ###################################################################################################
    # serve module's static file
    ###################################################################################################
    directory_pattern = '|'.join(directory_list)
    print('ADD STATIC FILE ROUTE: "module/assets/*"')
    route('/<module_path:re:('+directory_pattern+')>/assets/<path:re:.+>')(_module_static)
    ###################################################################################################
    # add template path
    ###################################################################################################
    TEMPLATE_PATH.remove('./views/')
    for directory in directory_list:
        print('REGISTER TEMPLATE PATH : '+directory+'/views/')
        TEMPLATE_PATH.append('./application/'+directory+'/views/')
    ###################################################################################################
    # Handling error
    ###################################################################################################
    for key in ERROR_HANDLER:
        error(key)(ERROR_HANDLER[key])
    ###################################################################################################
    # run the application
    ###################################################################################################
    session_opts = {
        'session.type': 'file',
        'session.data_dir': './session/',
        'session.auto': True,
    }
    app = beaker.middleware.SessionMiddleware(APP, session_opts)
    port = int(os.environ.get("PORT", PORT))
    run(app=app, server=SERVER, reloader=RELOADER, host=HOST, 
        port=port, quiet=QUIET, interval=INTERVAL, debug=DEBUG, plugins=PLUGINS, **kwargs)