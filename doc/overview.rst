========
Overview
========

In which the purpose of this app is explained, alongside pointers as
to how to use it to add metadata to arbitrary models.

In short
========

This package provides metadata services that can be attached to
existing models to add key-value metadata.  It is used in the URY
LASS project to store show names, descriptions, thumbnails and other
such data.

What is metadata?
=================

The ``django-lass-metadata`` system defines *metadata* as a key-value
map whereby the same keys can be mapped to different values
in different models.  The keys are typically referred to by a string,
but are themselves contained in a global model alongside some
additional properties each key has.

Each collection of metadata attached to a model is known as a
*metadata strand*, and is homogeneous (that is, every value inside it
is of the same type).

Each strand is its own model, but the package provides convenience
functions for spawning new models for 
This package provides both a generic metadata abstract model that can
be used to define these homogeneous strand models, as well as
predefined versions for textual and image-based metadata.

Keys are global
---------------

As mentioned before, there is only one key repository shared by all
models; this was a design decision primarily for simplicity, but has
the result of promoting a common language or taxonomy for all objects
inside a domain.

Keys can be singular or multiple
--------------------------------

Each key can decide whether or not multiple instances of itself in a
strand are allowed, via the
:attr:`metadata.models.MetadataKey.allow_multiple` field.

When retrieving a multiple-use metadatum, all values active during the
reference date are returned in a list (and the empty list is used to
represent no active data); otherwise the latest value is returned (and
a :class:`KeyError` is raised if none are active).

This distinction allows the metadata system to store items such as
titles and descriptions unambiguously whilst also being usable for
storing, for example, arbitrary tags or notes.

Metadata has history
--------------------

Metadata has an *effective range*, which means that it can be set to
come into and go out of force at given date-times.  This allows the
metadata system to track history of metadata, instead of just holding
the current state.

Metadata has approvers and creators
-----------------------------------

Metadata also tracks who created it, and (optionally) who approved it
for usage.
