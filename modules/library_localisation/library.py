from datetime import datetime

from sql import Null

from trytond import backend

from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction
from trytond.model import ModelSQL, ModelView, fields, Model
from trytond.pyson import Eval, If, Bool

__all__ = [
    'Room',
    'Shelf',
    'Reserve',
    'Quarantine',
    'Exemplary',
]


class Room(ModelSQL, ModelView):
    'Room'
    __name__ = 'library.room'

    shelves = fields.One2Many('library.room.shelf', 'room', 'Shelves')
    name = fields.Char('Name', required=True)


class Shelf(ModelSQL, ModelView):
    'Shelf'
    __name__ = 'library.room.shelf'

    room = fields.Many2One('library.room', 'Room', ondelete='CASCADE', required=True)
    exemplaries = fields.One2Many('library.book.exemplary', 'shelf', 'Exemplaries')
    name = fields.Char('Name', required=True)


class Reserve(ModelSQL, ModelView):
    'Reserve'
    __name__ = 'library.reserve'

    exemplaries = fields.One2Many('library.book.exemplary', 'reserve', 'Exemplaries')
    name = fields.Char('Name', required=True)


class Quarantine(ModelSQL, ModelView):
    'Quarantine'
    __name__ = 'library.quarantine'

    exemplaries = fields.One2Many('library.book.exemplary', 'quarantine', 'Exemplaries')
    name = fields.Char('Name', required=True)


class Exemplary(metaclass=PoolMeta):
    __name__ = 'library.book.exemplary'

    shelf = fields.Many2One('library.room.shelf', 'Shelf', ondelete='CASCADE',
                            states={'invisible': Bool(Eval('reserve', 'False')) and Bool(Eval('quarantine', 'False'))},
                            depends=['reserve', 'quarantine'])
    reserve = fields.Many2One('library.reserve', 'Reserve', ondelete='RESTRICT',
                              states={'invisible': Bool(Eval('shelf', 'False'))}, depends=['shelf'])
    quarantine = fields.Many2One('library.quarantine', 'Quarantine', ondelete='RESTRICT',
                                 states={'invisible': ~Bool(Eval('quarantine', 'False'))}, depends=['quarantine'])

    return_date = fields.Date('Return Date')

    memory_shelf = fields.Integer('Memory shelf')

    is_available = fields.Function(
        fields.Boolean('Is available', help='If True, the exemplary is currently available for borrowing'),
        'getter_is_available', searcher='search_is_available')

    borrowed = fields.Function(
        fields.Boolean('Borrowed', help='If True, exemplary currently borrowed by a user'), 'getter_borrowed')

    ready_to_quit_quarantine = fields.Function(
        fields.Boolean('Ready to quit quarantine',
                       help='If True, the exemplary spent 7 days on quarantine, ready to be put back on its shelf',
                       states={'invisible': ~Eval('ready_to_quit_quarantine')}), 'getter_ready_to_quit_quarantine')

    @classmethod
    @ModelView.button_change('ready_to_quit_quarantine', 'quarantine')
    def quit_quarantine(self, exemplaries):
        try:
            if not self.ready_to_quit_quarantine or self.ready_to_quit_quarantine is False:
                raise ValueError
        except ValueError:
            self.raise_user_error('invalid_isbn')
        if self.ready_to_quit_quarantine is True:
            cursor = Transaction().connection.cursor()
            cursor.execute(""" """)

    @classmethod
    def getter_is_available(cls, exemplaries, name):
        checkout = Pool().get('library.user.checkout').__table__()
        exemplary = Pool().get('library.book.exemplary').__table__()
        cursor = Transaction().connection.cursor()
        result = {x.id: True for x in exemplaries}
        cursor.execute("""(SELECT a.id FROM library_book_exemplary a WHERE reserve is not Null or quarantine is not 
        Null) UNION (SELECT b.exemplary FROM library_user_checkout b WHERE return_date is Null);""")
        for exemplary_id, in cursor.fetchall():
            result[exemplary_id] = False
        return result

    def getter_ready_to_quit_quarantine(self, name):
        if self.quarantine:
            if (datetime.now() - datetime(self.return_date.year,
                                          self.return_date.month,
                                          self.return_date.day)).days > 7:
                return True
            else:
                return False

    @classmethod
    def getter_borrowed(cls, exemplaries, name):
        cursor = Transaction().connection.cursor()
        result = {x.id: False for x in exemplaries}
        cursor.execute("""SELECT exemplary FROM library_user_checkout WHERE return_date is Null;""")
        for exemplary_id, in cursor.fetchall():
            result[exemplary_id] = True
        return result

    @classmethod
    def default_return_date(cls):
        return Null

    @classmethod
    def default_memory_shelf(cls):
        return Null

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._error_messages.update({'quarantine_not_completed': 'The quarantine period should last 7 days at least'})
        cls._buttons.update({
                'quit_quarantine': {},
                })
