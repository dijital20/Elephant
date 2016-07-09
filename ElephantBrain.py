import logging
import os
import sqlite3


# Logger and formatter
log = logging.getLogger('Elephant')
log.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
# File handler
# fle = logging.FileHandler('Elephant.log')
# fle.setLevel(logging.DEBUG)
# fle.setFormatter(fmt)
# if fle not in log.handlers:
#     log.addHandler(fle)
# Console handler
cns = logging.StreamHandler()
cns.setLevel(logging.DEBUG)
cns.setFormatter(fmt)
if cns not in log.handlers:
    log.addHandler(cns)


def dict_factory(cur, row):
    return dict([(c[0], row[i]) for i, c in enumerate(cur.description)])


class ElephantBrain(object):
    def __init__(self, file_path, new=False):
        self.log = logging.getLogger('Elephant.ElephantBrain')
        self.file_path = os.path.abspath(file_path)
        if new:
            # Handle new files
            if os.path.isfile(self.file_path):
                self.log.warn('{0} exists and will be overwritten.'.format(
                    self.file_path))
                try:
                    os.remove(self.file_path)
                    self.log.debug('Deleted: {0}'.format(self.file_path))
                except (IOError, OSError) as err:
                    self.log.error('Deleting {0}: {1}'.format(
                        self.file_path, err))
            self.db = self._make_new_db()
        else:
            # Handle existing files
            if not os.path.isfile(self.file_path):
                self.log.warn('{0} does not exist.'.format(self.file_path))
            try:
                self.db = sqlite3.connect(self.file_path)
            except sqlite3.Error as err:
                self.log.error('Connecting to database {0}'.format(err))
        self.db.row_factory = dict_factory

    def __del__(self):
        self.db.close()

    def __repr__(self):
        return 'ElephantBrain ({0})'.format(self.file_path)

    @property
    def info(self):
        counts = {}
        for table in ['Site', 'Room', 'People', 'Equipment', 'Event',
                      'StaffAssign', 'EquipmentAssign', 'EquipmentAdjust']:
            counts[table] = len(
                self.get([table]).fetchall())
        return '{0}:\n  Metadata:\n{1}\n  Table Counts:\n{2}'.format(
            repr(self),
            '\n'.join(['    {0}: {1}'.format(k, self.metadata[k])
                       for k in self.metadata]),
            '\n'.join(['    {0}: {1}'.format(k, counts[k])
                       for k in counts]))

    @property
    def metadata(self):
        return dict([(r['Name'], r['Value']) for r in self.get(['Metadata'])])

    @property
    def _table_list(self):
        return [
            i['name'] for i in
            self.get('sqlite_master', 'name', 'type=\'table\'', fetchall=True)
            if not i['name'].startswith('sqlite')
            ]

    def _make_new_db(self):
        self.log.debug('_make_new_db()')
        db = sqlite3.connect(self.file_path)
        cur = db.cursor()
        self.log.debug('Setting Foreign Keys to on')
        cur.execute('PRAGMA FOREIGN_KEYS=ON')
        self.log.debug('Creating Metadata table...')
        cur.execute(
            '''
            CREATE TABLE Metadata(
                Name text primary key not null,
                Value text
            );
            ''')
        self.log.debug('Creating Site table...')
        cur.execute(
            '''
            CREATE TABLE Site(
                id integer primary key autoincrement not null,
                Name text not null,
                Location text
            );
            ''')
        self.log.debug('Creating Room table...')
        cur.execute(
            '''
            CREATE TABLE Room(
                id integer primary key autoincrement not null,
                Name text not null,
                RoomGroup text not null,
                Capacity integer,
                Type text,
                Site integer,
                foreign key(Site) references Site(id)
            );
            ''')
        self.log.debug('Creating People table...')
        cur.execute(
            '''
            CREATE TABLE People(
                id integer primary key autoincrement not null,
                FirstName text not null,
                LastName text not null,
                WorkPhone text,
                CellPhone text,
                EMail text,
                Type text
            );
            ''')
        self.log.debug('Creating Equipment table...')
        cur.execute(
            '''
            CREATE TABLE Equipment(
                id integer primary key autoincrement not null,
                Name text not null,
                ShortName text not null,
                Description text,
                Notes text,
                RoleRequired text
            );
            ''')
        self.log.debug('Creating Event table...')
        cur.execute(
            '''
            CREATE TABLE Event(
                id integer primary key autoincrement not null,
                Name text not null,
                Room integer not null,
                Start datetime not null,
                End datetime not null,
                Speaker integer not null,
                Notes text,
                foreign key(Room) references Room(id),
                foreign key(Speaker) references People(id)
            );
            ''')
        self.log.debug('Creating StaffAssign table...')
        cur.execute(
            '''
            CREATE TABLE StaffAssign(
                id integer primary key autoincrement not null,
                Event integer not null,
                Person integer not null,
                Role text,
                foreign key(Event) references Event(id),
                foreign key(Person) references People(id)
            );
            ''')
        self.log.debug('Creating EquipmentAssign table...')
        cur.execute(
            '''
            CREATE TABLE EquipmentAssign(
                id integer primary key autoincrement not null,
                Event integer not null,
                Piece integer not null,
                Quantity integer not null,
                Notes text,
                foreign key(Event) references Event(id),
                foreign key(Piece) references Equipment(id)
            );
            ''')
        self.log.debug('Creating EquipmentAdjust table...')
        cur.execute(
            '''
            CREATE TABLE EquipmentAdjust(
                id integer primary key autoincrement not null,
                Piece integer not null,
                Site integer not null,
                Quantity integer not null,
                foreign key(Piece) references Equipment(id),
                foreign key(Site) references Site(id)
            );
            ''')
        db.commit()
        return db

    def _validate_db(self):
        pass

    def add(self, table, fields, values):
        self.log.debug('add(): {0}'.format(locals()))
        qry = 'INSERT INTO {0}({1}) VALUES ({2})'.format(
            table, ', '.join(fields), ', '.join([repr(v) for v in values]))
        self.log.debug('{0}'.format(qry))
        return self.query(qry)

    def add_csv(self, table, csv_file, field_map=None):
        self.log.debug('add_csv(): {0}'.format(locals()))
        from csv import DictReader
        csv_file = os.path.abspath(csv_file)
        if field_map and (not isinstance(field_map, dict) or not all(
                [isinstance(v, basestring) for v in field_map.values()])):
            raise TypeError('field_map must be a dictionary mapping strings '
                            'to strings.')
        if not os.path.isfile(csv_file):
            raise ValueError('{0} either does not exist or is not a '
                             'file.'.format(csv_file))
        self.log.debug('Reading: {0}'.format(csv_file))
        with open(csv_file, mode='r') as csv:
            dr = DictReader(csv)
            for row in dr:
                # Parse the field map if there is one.
                if field_map:
                    ins_row = {}
                    for k, v in field_map.iteritems():
                        if v:
                            ins_row[k] = row.get(v)
                        else:
                            ins_row[k] = row.get(k)
                    row = ins_row
                # Add the row values to the database
                self.log.debug('Adding: {0}'.format(row))
                self.add(table, row.keys(), row.values())

    def add_xlsx(self, xlsx_file, field_map=None):
        pass

    def get(self, tables, fields=None, where=None, fetchall=False):
        self.log.debug('get(): {0}'.format(locals()))
        # Take string params and turn them into lists.
        if isinstance(tables, basestring):
            tables = [tables]
        if isinstance(fields, basestring):
            fields = [fields]
        if isinstance(where, basestring):
            where = [where]
        # Build the Query string and query
        qry = 'SELECT ' + (', '.join(fields) if fields else '*') + \
              ' FROM ' + ', '.join(tables)
        if where:
            qry += ' WHERE ' + ' AND '.join(where)
        self.log.debug('{0}'.format(qry))
        return self.query(qry, fetchall=fetchall)

    def query(self, qry, fetchall=False):
        self.log.debug('query(): {0}'.format(locals()))
        cur = self.db.cursor()
        new_cur = cur.execute(qry)
        return new_cur if not fetchall else new_cur.fetchall()

if __name__ == '__main__':
    from pprint import pformat

    eb = ElephantBrain('test.db', new=True)
    eb.add('Metadata',
           ['Name', 'Value'],
           ['Name', 'Some Conference 2016'])
    eb.add('Metadata',
           ['Name', 'Value'],
           ['Location', 'Somewhere, Some State'])
    eb.add('Equipment',
           ['Name', 'ShortName'],
           ['Thingy', 'T'])
    eb.add('Equipment',
           ['Name', 'ShortName'],
           ['Bobber', 'B'])
    eb.add_csv('Equipment', 'ti_eq.csv',
               {'Name': '', 'ShortName': '', 'Description': ''})
    eb.add('Site',
           ['Name', 'Location'],
           ['Site A', '?'])
    eb.add('Room',
           ['Name', 'RoomGroup', 'Site'],
           ['Room 1', 'Hall A', 1])
    eb.add('People',
           ['FirstName', 'LastName', 'Type'],
           ['John', 'Doe', 'Instructor'])
    eb.add('Event',
           ['Name', 'Room', 'Start', 'End', 'Speaker'],
           ['Cool Session #1', 1, '2016-01-01 10:30',
            '2016-01-01 11:30', 1])
    eb.add('EquipmentAssign',
           ['Event', 'Piece', 'Quantity'],
           [1, 1, 2])
    eb.add('EquipmentAssign',
           ['Event', 'Piece', 'Quantity'],
           [1, 2, 5])
    print(eb.info)
    events = eb.get(
        ['Event', 'Room', 'People', 'Site'],
        fields=['Site.Name AS Site',
                'Room.Name AS Room',
                'Event.Name',
                'Event.Start',
                'Event.End',
                'People.FirstName',
                'People.LastName'],
        where=['Room.Site=Site.id',
               'Event.Room=Room.id',
               'Event.Speaker=People.id']
    )
    print('\nEvents:\n{0}'.format(pformat(events.fetchall())))

    assigns = eb.get(
        ['Event', 'Room', 'Site', 'Equipment', 'EquipmentAssign'],
        fields=['Equipment.Name AS Equipment',
                'EquipmentAssign.Quantity',
                'Site.Name AS Site',
                'Room.Name AS Room',
                'Event.Name AS Event',
                'Event.Start',
                'Event.End'],
        where=['Room.Site=Site.id',
               'Event.Room=Room.id',
               'EquipmentAssign.Piece=Equipment.id',
               'EquipmentAssign.Event=Event.id']
    )
    print('\nEquipment Assignments:\n{0}'.format(
        pformat(assigns.fetchall())))

    print('\nEquipment:\n{0}'.format(
        pformat(eb.get('Equipment', fetchall=True))))
