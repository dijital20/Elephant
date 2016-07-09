import logging
import os
import re
import sqlite3


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
cns.setLevel(logging.DEBUG)
cns.setFormatter(fmt)
if cns not in log.handlers:
    log.addHandler(cns)


def dict_factory(cur, row):
    """
    Dictionary factor for sqlite3. Converts Row objects to dictionaries.

    Args:
        cur (sqlite3.Cursor): Cursor object
        row (sqlite3.Row): Current Row object.

    Returns (dict):
    Dictionary of the current row's values with the field name as the key.
    """
    return dict([(c[0], row[i]) for i, c in enumerate(cur.description)])


class AddledBrainError(Exception):
    pass


class ElephantBrain(object):
    """
    ElephantBrain is the interface to the database that stores all of your
    glorious data. This class aims to handle opening and interfacing with the
    database, and will provide methods for getting data to and from the
    database.
    """

    schema = {
        'Metadata':
            '''
            CREATE TABLE Metadata(
                Name text primary key not null,
                Value text
            );
            ''',
        'Site':
            '''
            CREATE TABLE Site(
                id integer primary key autoincrement not null,
                Name text not null,
                Location text
            );
            ''',
        'Room':
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
            ''',
        'People':
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
            ''',
        'Equipment':
            '''
            CREATE TABLE Equipment(
                id integer primary key autoincrement not null,
                Name text not null,
                ShortName text not null,
                Description text,
                Notes text,
                RoleRequired text
            );
            ''',
        'Event':
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
            ''',
        'StaffAssign':
            '''
            CREATE TABLE StaffAssign(
                id integer primary key autoincrement not null,
                Event integer not null,
                Person integer not null,
                Role text,
                foreign key(Event) references Event(id),
                foreign key(Person) references People(id)
            );
            ''',
        'EquipmentAssign':
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
            ''',
        'EquipmentAdjust':
            '''
            CREATE TABLE EquipmentAdjust(
                id integer primary key autoincrement not null,
                Piece integer not null,
                Site integer not null,
                Quantity integer not null,
                foreign key(Piece) references Equipment(id),
                foreign key(Site) references Site(id)
            );
            ''',
    }

    def __init__(self, file_path, new=False):
        """
        Prepares an ElephantBrain for use.

        Args:
            file_path (str): Path to the database file.
            new (bool): True if you want to create a new file (this will
                overwrite existing files) or False if you intend to open an
                existing file.
        """
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
        if not self._validate_db():
            raise AddledBrainError(
                'The database isn\'t valid. Check logs for details.')

    def __del__(self):
        self.db.close()

    def __repr__(self):
        return 'ElephantBrain ({0})'.format(self.file_path)

    @property
    def info(self):
        """
        Information about the current ElephantBrain instance.

        Returns (str):
        A string containing information on how many items are in each table,
        and the database's metadata.
        """
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
        """
        A dictionary of the ElephantBrain's Metadata table.

        Returns (dict):
        A dictionary of the metadata from the Metadata table.
        """
        return dict([(r['Name'], r['Value']) for r in self.get(['Metadata'])])

    @property
    def _table_dict(self):
        """
        List of the tables in the current database.

        Returns (list):
        List of table names in the current database.
        """
        return dict([
            (i['name'], i['sql'])
            for i in self.get('sqlite_master', ['name', 'sql'],
                              'type=\'table\'', fetchall=True)
            if not i['name'].startswith('sqlite')
            ])

    def _make_new_db(self):
        """
        Create a new database and set the schema.

        Returns (sqlite3.Connection):
        The sqlite3 Connection object.
        """
        self.log.debug('_make_new_db()')
        db = sqlite3.connect(self.file_path)
        cur = db.cursor()
        self.log.debug('Setting Foreign Keys to on')
        cur.execute('PRAGMA FOREIGN_KEYS=ON')
        for table in self.schema:
            self.log.debug('Creating {0} table...'.format(table))
            cur.execute(self.schema[table])
        self.log.debug('Committing.')
        db.commit()
        return db

    def _validate_db(self):
        for table in self.schema:
            if table not in self._table_dict:
                self.log.error('Table {0} not in database'.format(table))
                return False
            db_sql = re.sub(r'[\s]+', ' ', self._table_dict[table]).strip()
            schema_sql = re.sub(r'[\s]+', ' ', self.schema[table]).strip()[:-1]
            if schema_sql != db_sql:
                self.log.error(
                    'Table {0} sql doesn\'t match schema\n'
                    '\ndb sql:\n{1}\n'
                    '\nschema sql:\n{2}\n'.format(
                        table, db_sql, schema_sql))
                return False
        return True

    def add(self, table, fields, values):
        """
        Add a row to a database table.

        Args:
            table (str): The name of the table to add data to.
            fields (list, tuple): The list of fields present in the data. The
                index of a field should match the index of its data in values.
            values (list, tuple): The list of values present int he data. The
                index of a value should match the index of its field in the
                fields.

        Returns (sqlite3.Cursor):
        The Cursor object resulting from the query.
        """
        self.log.debug('add(): {0}'.format(locals()))
        qry = 'INSERT INTO {0}({1}) VALUES ({2})'.format(
            table, ', '.join(fields), ', '.join([repr(v) for v in values]))
        self.log.debug('{0}'.format(qry))
        return self.query(qry)

    def add_csv(self, table, csv_file, field_map=None):
        """
        Add rows to the database from a CSV file of data.

        Args:
            table (str): The name of the table to add data to.
            csv_file (str): The path to the CSV file containing the data.
            field_map (dict, None): A dictionary mapping database fields
                (key) to CSV fields (value). If this parameter is specified,
                ONLY the fields specified in the dictionary will be added. If
                you want a database field to use its corresponding name in the
                csv, make the value a blank string.

        Returns (None):
        None. Zip. Nada.

        Raises:
            TypeError: If field_map is not a dictionary or does not contain
                all string values.
            ValueError: If csv_path does not exist or is not a file.
        """
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
        return None

    def add_xlsx(self, xlsx_file, field_map=None):
        # TODO: Implement this
        pass

    def get(self, tables, fields=None, where=None, fetchall=False):
        """
        Get data from the database (without having to worry about writing a
        SQL string).

        Args:
            tables (str, list, tuple): Table or collection of tables.
            fields (str, list, tuple, None): Field or collection of
                fields. If None is specified, uses *. If you are using multiple
                tables, be sure to prepend the field name with the table name
                (foo.bar for 'bar' from the 'foo' table). Also, if you are
                using mutliple fields with the same name from different tables,
                use the AS keyword and assign a unique alias, or the values
                will overwrite themselves in the output.
            where (str, list, tuple, None): If you have criteria for
                the WHERE clause in the SQL, add it here. Useful for joining
                tables. For example, if you want to join tables foo and bar by
                their id and foo fields respectively, you'd add:
                 'bar.foo=foo.id'
            fetchall (bool): Fetch and return all rows? Defaults to False.

        Returns (sqlite3.Cursor, list):
        If fetchall is True, will return a list of dictionaries for each row.
        If fetchall is False, will return a Cursor object.
        """
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
        """
        Send a raw query to the database. add(), get() and others use this.

        Args:
            qry (str): SQL Query string.
            fetchall (bool): Fetch and return all rows? Defaults to False.

        Returns (sqlite3.Cursor, list):
        If fetchall is True, will return a list of dictionaries for each row.
        If fetchall is False, will return a Cursor object.
        """
        self.log.debug('query(): {0}'.format(locals()))
        cur = self.db.cursor()
        new_cur = cur.execute(qry)
        return new_cur if not fetchall else new_cur.fetchall()

if __name__ == '__main__':
    from pprint import pformat

    eb = ElephantBrain('test.db', new=True)
    # Test adding some data to the Metadata
    eb.add('Metadata',
           ['Name', 'Value'],
           ['Name', 'Some Conference 2016'])
    eb.add('Metadata',
           ['Name', 'Value'],
           ['Location', 'Somewhere, Some State'])
    # Test adding some things to the Equipment table.
    eb.add('Equipment',
           ['Name', 'ShortName'],
           ['Thingy', 'T'])
    eb.add('Equipment',
           ['Name', 'ShortName'],
           ['Bobber', 'B'])
    eb.add_csv('Equipment', 'eq.csv',
               {'Name': '', 'ShortName': '', 'Description': ''})
    # Add a site, a room, and a person.
    eb.add('Site',
           ['Name', 'Location'],
           ['Site A', '?'])
    eb.add('Room',
           ['Name', 'RoomGroup', 'Site'],
           ['Room 1', 'Hall A', 1])
    eb.add('People',
           ['FirstName', 'LastName', 'Type'],
           ['John', 'Doe', 'Instructor'])
    # Add an event, and then assign equipment to it.
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
    # Print out info.
    print(eb.info)
    # Get and print the events with their associated details.
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
    # Get and print the assignments with their associated details.
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
    # Print the equipment table
    print('\nEquipment:\n{0}'.format(
        pformat(eb.get('Equipment', fetchall=True))))