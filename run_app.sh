pg_ctl -D /usr/local/var/postgres stop
pg_ctl -D /usr/local/var/postgres start

trytond-admin -c trytond.conf -d training --all
trytond-admin -c trytond.conf -d training -u ir
trytond-admin -c trytond.conf -d training -u library
trytond-admin -c trytond.conf -d training -u library_borrow
trytond-admin -c trytond.conf -d training -u library_localisation

trytond -c trytond.conf