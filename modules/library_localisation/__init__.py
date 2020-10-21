from trytond.pool import Pool

from . import library
from . import wizard


def register():
    Pool.register(
        library.Room,
        library.Shelf,
        library.Reserve,
        library.Quarantine,
        library.Exemplary,
        module='library_localisation', type_='model')

    Pool.register(
        wizard.Borrow,
        wizard.Return,
        wizard.CreateExemplariesParameters,
        module='library_localisation', type_='wizard')
