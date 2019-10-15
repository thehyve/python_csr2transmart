How to add changes to the Central Subject Registry (CSR) data model?
====================================================================

This page describes the changes that are required to modify the CSR data model.


Adding new entity
*****************

Changes in `csr` package:
-------------------------

The data model is defined as a data class in `<csr/csr.py>`_.
In order to add a new entity, a new class has to be defined.

Classes are defined using `pydantic` - library to validate JSON documents and convert them into Python objects, 
based on Python Type Annotations.

All new entities have to have a non-nullable `identity` defined. They also have to be a part of `SubjectEntity` union 
and `CentralSubjectRegistry` class defined in `csr.py`.
If there is a relation between the new entity and other entities, it has to be specified as a value of `references` key 
in Schema dictionary.

For more details see `official pydantic documentation`_.

.. _`official pydantic documentation`: https://pydantic-docs.helpmanual.io/


Changes in `sources2csr` package:
---------------------------------

If a property of the new entity requires some additional calculation, e.g. its value has to be derived
from other input values, the calculation logic should be added to `<sources2csr/derived_values.py>`_.


Extending tests and documentation:
----------------------------------

Changes added to the code should be well-covered by tests (test coverage should not be decreased).
In order to test reading of the source data and mapping it to CSR, extend `<tests/csr2transmart/test_csr_mapper.py>`_.
In order to test CSR to tranSMART mapping, extend `<tests/sources2csr/test_sources2csr.py>`_.
All new test data sets should be added to `<test_data>`_ folder.


Remember to update the section about data model in `<README.rst>`_.

Updating entity
***************

When updating one of the existing entities, there is a change required only in `<csr/csr.py>`_.
In order to add new property, rename or change the type of a property for existing entity, just modify the entity class.

When changing `<csr/csr.py>`_, tests both for mapping from sources to CSR and from CSR to tranSMART has to be
changed or extended - see "`Extending tests and documentation`" section above.


Leaving out entity
******************

Some of the entities can be left out, if no data is available for them.
In order to do this is, an empty "attributes" array should be assigned to the entities in one of the configuration files
of sources2csr - `sources_config.json` file.

For example:

.. code-block:: json

  {
    "entities": {
      "Biosource": {
        "attributes": []
      }
    }
  }
