
.. _ligare-platform:

Ligare.platform
===============

``Ligare.platform`` offers `PaaS <https://en.wikipedia.org/wiki/Platform_as_a_service>`_-like libraries for applications.
Although currently limited in functionality, it is useful for managing users, and `active functionality <https://martinfowler.com/articles/feature-toggles.html>`_ in an application.

Why Use Ligare.platform?
------------------------

Managing User Access Control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``Ligare.platform`` offers a limited form of user management and `RBAC <https://en.wikipedia.org/wiki/Role-based_access_control>`_ within ``ligare.platform.identity``.

This functionality is useful for accessing user information in a database, and controlling a user's access to running code.

Managing Active Functionality
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``ligare.platform.feature_flag`` offers functionality to control whether a given piece of code
should run. This is useful for controlling things like, e.g., "test" user accounts having access to "beta" functionality while keeping
"stable" software in place for everyone else. Feature flags are not limited to user access controls, and can be managed by any arbitary
criteria.
