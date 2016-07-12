import glob
import importlib
import inspect
import logging
import os


# Logger and formatter
log = logging.getLogger('Elephant')
log.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
# File handler
fle = logging.FileHandler('Elephant.log')
fle.setLevel(logging.DEBUG)
fle.setFormatter(fmt)
if fle not in log.handlers:
    log.addHandler(fle)
# Console handler
cns = logging.StreamHandler()
cns.setLevel(logging.ERROR)
cns.setFormatter(fmt)
if cns not in log.handlers:
    log.addHandler(cns)


class ElephantTrunk(object):
    def __init__(self):
        self.log = logging.getLogger('Elephant.ElephantTrunk')

    def list_reports(self):
        self.log.debug('list_reports(): {0}'.format(locals()))
        reports_dir = 'reports'
        reports = {}
        path = os.path.abspath(reports_dir)
        if not os.path.isdir(path):
            return reports
        for py_file in glob.glob(os.path.join(path, '*.py')):
            file_name = os.path.basename(py_file)
            mod_name = os.path.splitext(file_name)[0]
            if mod_name.startswith('__'):
                continue
            temp_mod = importlib.import_module('.{0}'.format(mod_name),
                                               package=reports_dir)
            for item in dir(temp_mod):
                obj = getattr(temp_mod, item)
                if not inspect.isclass(obj):
                    continue
                if 'ElephantReport' in [o.__name__ for o in obj.__bases__]:
                    reports[mod_name] = getattr(obj, 'title')
        return reports


class ElephantReport(object):
    title = 'Example Report'

    def __init__(self):
        if type(self) is not ElephantReport:
            raise NotImplementedError(
                'This class needs to be subclassed to be used.')

    def __repr__(self):
        return 'ElephantReport ({0})'.format(self.title)

    def data(self):
        return ''

    def build(self):
        raise NotImplementedError(
            'This class needs to be subclassed to be used.')


if __name__ == '__main__':
    from pprint import pformat

    et = ElephantTrunk()
    print(pformat(et.list_reports()))