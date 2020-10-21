import datetime

from sql import Null

from trytond.pool import Pool, PoolMeta, PoolBase
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction
from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, StateTransition, StateAction
from trytond.wizard import Button

__all__ = [
    'Borrow',
    'Return',
    'CreateExemplariesParameters',
]


class Borrow(metaclass=PoolMeta):
    'Borrow Books'
    __name__ = 'library.user.borrow'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.borrow_borrow = StateTransition()

    def transition_borrow(self):
        Checkout = Pool().get('library.user.checkout')
        exemplaries = self.select_books.exemplaries
        user = self.select_books.user
        checkouts = []
        for exemplary in exemplaries:
            if not exemplary.is_available:
                self.raise_user_error('unavailable', {
                    'exemplary': exemplary.rec_name})
            checkouts.append(Checkout(
                user=user, date=self.select_books.date,
                exemplary=exemplary))
        Checkout.save(checkouts)
        self.select_books.checkouts = checkouts

        cursor = Transaction().connection.cursor()
        cursor.execute(
            """UPDATE library_book_exemplary SET memory_shelf = shelf WHERE id IN (SELECT exemplary FROM 
            library_user_checkout WHERE return_date is Null);""")

        return 'checkouts'


class Return(metaclass=PoolMeta):
    'Return'
    __name__ = 'library.user.return'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.return_return_ = StateTransition()

    def transition_return_(self):
        Checkout = Pool().get('library.user.checkout')
        Checkout.write(list(self.select_checkouts.checkouts), {
            'return_date': self.select_checkouts.date})
        cursor = Transaction().connection.cursor()
        cursor.execute(
            """UPDATE library_book_exemplary SET quarantine = 1 WHERE memory_shelf is not Null; """

            """UPDATE library_book_exemplary SET return_date = library_user_checkout.return_date FROM 
            library_user_checkout WHERE library_user_checkout.exemplary = library_book_exemplary.id;"""

            """UPDATE library_book_exemplary SET memory_shelf = Null WHERE quarantine = 1""")

        return 'end'


class CreateExemplariesParameters(metaclass=PoolMeta):
    'Create Exemplaries Parameters'
    __name__ = 'library.book.create_exemplaries.parameters'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.create_exemplaries_create_exemplaries_parameters = StateView('library.book.create_exemplaries.parameters',
                                                                         'library.create_exemplaries_parameters_view_form',
                                                                         [
                                                                             Button('Cancel', 'end', 'tryton-cancel'),
                                                                             Button('Create', 'create_exemplaries',
                                                                                    'tryton-go-next',
                                                                                    default=True)])

    shelf = fields.Many2One('library.room.shelf', 'Shelf')
