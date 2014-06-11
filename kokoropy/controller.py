from kokoropy import load_view, base_url, request
from sqlalchemy.ext.declarative import declared_attr
import math

class Crud_Controller(object):
    __model__               = None
    __application_name__    = ''
    __view_directory__      = ''
    __url_list__            = {}
    __table_name__          = ''
    
    def action_index(self):
        return self.list()
    
    def action_list(self):
        return self.list()
    
    def action_show(self, id):
        return self.show(id)
    
    def action_new(self):
        return self.new(id)
    
    def action_create(self):
        return self.create(id)
    
    def action_edit(self, id):
        return self.edit(id)
    
    def action_update(self,id):
        return self.update(id)
    
    def action_trash(self, id):
        return self.trash(id)
    
    def action_remove(self, id):
        return self.remove(id)
    
    def action_delete(self, id):
        return self.delete(id)
    
    def action_destroy(self, id):
        return self.destroy(id)
    
    @declared_attr
    def __url_list__(self):
        url = base_url(self.__application_name__+'/' + self.__table_name__) + '/'
        url_list = {
            'index'   : url + 'index',
            'list'    : url + 'list',
            'show'    : url + 'show',
            'new'     : url + 'new',
            'create'  : url + 'create',
            'edit'    : url + 'edit',
            'update'  : url + 'update',
            'trash'   : url + 'trash',
            'remove'  : url + 'remove',
            'delete'  : url + 'delete',
            'destroy' : url + 'destroy'
        }
        return url_list
    
    @declared_attr
    def __table_name__(self):
        if self.__table_name__ == '' and hasattr(self.__model__, '__tablename__'):
            return self.__model__.__tablename__
        else:
            return ''
    
    def _setup_parameter(self):
        self._parameter = {'url_list': self.__url_list__}
        
    
    def _set_parameter(self, key, value):
        if not hasattr(self, '_parameter'):
            self._setup_parameter()
        self._parameter[key] = value
    
    def _get_parameter(self, key):
        if not hasattr(self, '_parameter'):
            self._setup_parameter()
        if key in self.__parameter:
            return self._parameter[key]
    
    def _load_view(self, view):
        return load_view(self.__application_name__, self.__table_name__ + '/' + view, **self._parameter)
    
    def list(self):
        ''' Show table '''
        # get page index
        current_page = int(request.GET['page']) if 'page' in request.GET else 1
        # determine limit and offset
        limit = 50
        offset = (current_page-1) * limit
        # get the data
        data_list = self.__model__.get(limit = limit, offset = offset)
        # calculate page count
        page_count = int(math.ceil(float(self.__model__.count())/limit))
        # load the view
        self._setup_parameter()
        self._set_parameter(self.__table_name__+'_list', data_list)
        self._set_parameter('current_page', current_page)
        self._set_parameter('page_count', page_count)
        return self._load_view('list')
    
    def show(self, id):
        ''' Show One Record '''
        data = self.__model__.find(id)
        data.set_state_show()
        # load the view
        self._setup_parameter()
        self._set_parameter(self.__table_name__, data)
        return self._load_view('show')
    
    def new(self):
        ''' Insert Form '''
        data = self.__model__()
        data.set_state_insert()
        # load the view
        self._setup_parameter()
        self._set_parameter(self.__table_name__, data)
        return self._load_view('new')
    
    def create(self):
        ''' Insert Action '''
        data = self.__model__()
        data.set_state_insert()
        # put your code here
        data.assign_from_dict(request.POST)
        data.save()
        # get result
        success = data.success
        error_message = data.error_message
        # load the view
        self._setup_parameter()
        self._set_parameter(self.__table_name__, data)
        self._set_parameter('success', success)
        self._set_parameter('error_message', error_message)
        return self._load_view('create')
    
    def edit(self, id):
        ''' Update Form '''
        data = self.__model__.find(id)
        data.set_state_update()
        # load the view
        self._setup_parameter()
        self._set_parameter(self.__table_name__, data)
        return self._load_view('edit')
    
    def update(self,id):
        ''' Update Action '''
        data = self.__model__.find(id)
        data.set_state_update()
        # put your code here
        data.assign_from_dict(request.POST)
        data.save()
        success = data.success
        error_message = data.error_message
        # load the view
        self._setup_parameter()
        self._set_parameter(self.__table_name__, data)
        self._set_parameter('success', success)
        self._set_parameter('error_message', error_message)
        return self._load_view('update')
    
    def trash(self, id):
        ''' Trash Form '''
        data = self.__model__.find(id)
        # load the view
        self._setup_parameter()
        self._set_parameter(self.__table_name__, data)
        return self._load_view('show')
    
    def remove(self, id):
        ''' Trash Action '''
        data = self.__model__.find(id)
        data.trash()
        success = data.success
        error_message = data.error_message
        # load the view
        self._setup_parameter()
        self._set_parameter(self.__table_name__, data)
        self._set_parameter('success', success)
        self._set_parameter('error_message', error_message)
        return self._load_view('remove')
    
    def delete(self, id):
        ''' Delete Form '''
        data = self.__model__.find(id)
        # load the view
        self._setup_parameter()
        self._set_parameter(self.__table_name__, data)
        return self._load_view('delete')
    
    def destroy(self, id):
        ''' Delete Action '''
        data = self.__model__.find(id)
        data.delete()
        success = data.success
        error_message = data.error_message
        # load the view
        self._setup_parameter()
        self._set_parameter(self.__table_name__, data)
        self._set_parameter('success', success)
        self._set_parameter('error_message', error_message)
        return self._load_view('destroy')