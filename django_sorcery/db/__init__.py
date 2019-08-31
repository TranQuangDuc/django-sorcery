# -*- coding: utf-8 -*-
"""
Package with SQLAlchemy abstractions to interact with the database.
All tools implemented here assume `unit-of-work`_ usage pattern.

Connecting
----------

Connecting to the DB is as simple as using a url with :py:class:`.SQLAlchemy` abstraction::

    >>> from django_sorcery.db import SQLAlchemy
    >>> db = SQLAlchemy('sqlite://')

You can also use an alias to connect to a database as well. Just like Django's ``DATABASES``, connection settings for
aliases are stored in ``SQLALCHEMY_CONNECTIONS``. As such all databases are referred by their aliases just like in
Django ORM. For example ``"default"`` is an alias to the default connect::

    >>> db = SQLAlchemy('default')

ORM Goodies
-----------

:py:class:`.SQLAlchemy` is itself also a threadlocal manager that proxies calls to a thread local ``Session`` instance
and provides a couple of shortcuts when interacting with SQLAlchemy session.
To have them installed, you can subclass from the declarative base generated by the DB.
In addition :py:class:`.SQLAlchemy` also exposes most of SQLALchemy's elements
so a single import should suffice to define most tables::

    >>> class BarModel(db.Model):
    ...     id = db.Column(db.Integer(), primary_key=True)

    >>> class FooModel(db.Model):
    ...     id = db.Column(db.Integer(), primary_key=True)
    ...     id2 = db.Column(db.Integer(), primary_key=True)
    ...     name = db.Column(db.String(length=32))
    ...     bar_id = db.Column(db.Integer(), db.ForeignKey(BarModel.id, name='FK_foo_bar', use_alter=True))
    ...     bar = db.relationship(BarModel)

    >>> db.create_all()

Doing so will allow to use a couple of useful shortcuts:

:py:meth:`.Query.get`:

    Identity map in SQLAlchemy is amazing. Composite keys not so much. Put them together is even worse.
    :py:attr:`.SQLAlchemy` uses a special session which allows keyword arguments when using ``.get()``.
    It is much more explicit and is less error-prone as SQLAlchemy's default implementation expects only
    positional arguments where order of primary keys matters.
    For example::

        >>> db.query(FooModel).get(id=123, id2=456)

:py:meth:`.SQLAlchemy.queryproperty()`:

    Allows to create a property which will normalize to a query object of the model.
    It will use the correct session within the transaction so no need to pass session around.
    For example::

        >>> class MyView(object):
        ...     queryset = db.queryproperty(FooModel)

    You can even pass default filtering criteria if needed::

        >>> class MyView(object):
        ...     queryset = db.queryproperty(FooModel, to_be_deleted=False)

    In addition this pattern can be used to implement Django's ORM style model managers::

        >>> class UserModel(db.Model):
        ...     id = db.Column(db.Integer(), primary_key=True)
        ...     username = db.Column(db.String())
        ...     is_active = db.Column(db.Boolean())
        ...
        ...     objects = db.queryproperty()
        ...     active = db.queryproperty(is_active=True)

    That can be used directly::

        >>> UserModel.metadata.create_all(bind=db.engine)
        >>> db.add_all([
        ...     UserModel(id=1, username='foo', is_active=False),
        ...     UserModel(id=2, username='bar', is_active=True),
        ... ])
        >>> db.flush()

        >>> UserModel.objects.all()
        [UserModel(id=1, is_active=False, username='foo'), UserModel(id=2, is_active=True, username='bar')]
        >>> UserModel.active.all()
        [UserModel(id=2, is_active=True, username='bar')]

    This pattern is very useful when combined with Django style views::

        >>> class MyView(object):
        ...     queryset = UserModel.active

        >>> MyView().queryset.all()
        [UserModel(id=2, is_active=True, username='bar')]

    Additional filters/options can be applied as well::

        >>> class MyView(object):
        ...     queryset = UserModel.active.filter(UserModel.username == 'test')

        >>> MyView().queryset.all()
        []

Transactions
------------

If you need to explicitly use transactions, you can use :py:meth:`.SQLAlchemy.atomic`::

    >>> with db.atomic(savepoint=False):
    ...     _ = db.query(UserModel).filter_by(username='hello').update(dict(username='world'))

    >>> @db.atomic(savepoint=False)
    ... def do_something():
    ...     db.query(UserModel).filter_by(username='hello').update(username='world')

.. warning::

    You better know what you are doing if you need this.
    If you are not, sure, **JUST USE THE MIDDLEWARE** (see below).

Django
------

To complete the unit-of-work :py:class:`.SQLAlchemy` ships with capability
to generate Django middleware to commit at the end of the request
for the used session within the request::

    # settings.py
    >>> MIDDLEWARE = [
    ...     # should be last in response life-cycle
    ...     # or first in middleware list
    ...     'path.to.db.middleware',
    ...     # rest of middleware
    ... ]

.. _unit-of-work: https://martinfowler.com/eaaCatalog/unitOfWork.html

"""


from .sqlalchemy import SQLAlchemy  # noqa
from .utils import dbdict


databases = dbdict()
