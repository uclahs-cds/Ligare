Ligare Dependency Relationships
===============================

This diagram represents the interdependent relationships some Ligare libraries share.

The libraries are independent, however, some depend on other Ligare functionality.
For example, ``Ligare.web`` depends on ``Ligare.platform`` which depends on ``Ligare.database``.

These relationships are visualized below.

.. uml::

   @startuml
   skinparam componentStyle rectangle
   skinparam linetype ortho
   left to right direction

   caption Ligare libraries and their dependency relationships

   label " " as emptynode

   component [Ligare.all.toplevel] as "Ligare.all"
   component [Ligare.AWS.toplevel] as "Ligare.AWS" #lightblue
   component [Ligare.database.toplevel] as "Ligare.database" #lightgreen
   component [Ligare.development.toplevel] as "Ligare.development" #lightyellow
   component [Ligare.GitHub.toplevel] as "Ligare.GitHub" #lightcoral
   component [Ligare.identity.toplevel] as "Ligare.identity" #plum
   component [Ligare.platform.toplevel] as "Ligare.platform" #CCCCFF
   component [Ligare.programming.toplevel] as "Ligare.programming" #wheat
   component [Ligare.testing.toplevel] as "Ligare.testing" #pink
   component [Ligare.web.toplevel] as "Ligare.web" #orange

   [Ligare.all.toplevel] --> [Ligare.AWS.toplevel]
   [Ligare.all.toplevel] --> [Ligare.database.toplevel]
   [Ligare.all.toplevel] --> [Ligare.development.toplevel]
   [Ligare.all.toplevel] --> [Ligare.GitHub.toplevel]
   [Ligare.all.toplevel] --> [Ligare.identity.toplevel]
   [Ligare.all.toplevel] --> [Ligare.platform.toplevel]
   [Ligare.all.toplevel] --> [Ligare.programming.toplevel]
   [Ligare.all.toplevel] --> [Ligare.testing.toplevel]
   [Ligare.all.toplevel] --> [Ligare.web.toplevel]


   component [Ligare.programming.database] as "Ligare.programming" #wheat
   component [Ligare.AWS.database] as "Ligare.AWS" #lightblue
   [Ligare.database.toplevel] --> [Ligare.programming.database]
   [Ligare.database.toplevel] --> [Ligare.AWS.database]

   component [Ligare.database.platform] as "Ligare.database" #lightgreen
   [Ligare.platform.toplevel] --> [Ligare.database.platform]
   [Ligare.database.platform] -[#lightgreen,norank]-> [Ligare.database.toplevel]

   component [Ligare.AWS.web] as "Ligare.AWS" #lightblue
   component [Ligare.programming.web] as "Ligare.programming" #wheat
   component [Ligare.platform.web] as "Ligare.platform" #CCCCFF
   component [Ligare.identity.web] as "Ligare.identity" #plum
   component [Ligare.database.web] as "Ligare.database" #lightgreen
   [Ligare.web.toplevel] --> [Ligare.AWS.web]
   [Ligare.web.toplevel] --> [Ligare.programming.web]
   [Ligare.web.toplevel] --> [Ligare.platform.web]
   [Ligare.web.toplevel] --> [Ligare.identity.web]
   [Ligare.web.toplevel] --> [Ligare.database.web]
   [Ligare.platform.web] -[#CCCCFF,norank]-> [Ligare.platform.toplevel]
   [Ligare.database.web] -[#lightgreen,norank]-> [Ligare.database.toplevel]

   [Ligare.AWS.database] -[#lightblue,norank]-> [Ligare.AWS.toplevel]
   [Ligare.AWS.web] -[#lightblue,norank]-> [Ligare.AWS.toplevel]
   [Ligare.programming.database] -[#wheat,norank]-> [Ligare.programming.toplevel]
   [Ligare.programming.web] -[#wheat,norank]-> [Ligare.programming.toplevel]
   [Ligare.database.platform] -[#lightgreenashed,norank]-> [Ligare.database.toplevel]
   [Ligare.identity.web] -[#plum,norank]-> [Ligare.identity.toplevel]


   'positional arrows only
   [Ligare.development.toplevel] -[hidden]-> emptynode
   [Ligare.testing.toplevel] -[hidden]-> emptynode
   [Ligare.GitHub.toplevel] -[hidden]-> emptynode

   @enduml
