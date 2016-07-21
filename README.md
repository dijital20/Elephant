# Elephant
Back in a past life, I worked for a company with a division that supplied equipment for evaluation.  A side effect of that work is that they supplied equipment for several large conferences where speakers used their products. Planning for the equipment to send and staff to send for support became a huge task. I was commissioned to build a database, where the conference's informationc could be entered, equipment and staff assignments made, and then reports could be produced to help coordinate the people and things headed there.

It was my first project, and there are definitely things I'd do different, now that I am older and wiser.

So here I am. Elephant will be an application where a user can import events, rooms, and sites for a conference, assign staff and equipment, and produce reporting for the conference. Some design guidelines and goals of the project:

* Data, interface, and reporting should be separate.
* Data should be portable from computer to computer, but need only be used by one user at a time.
* Should support both GUI and command line manipulation.
* Reporting system should be modular, with each report module defining the query of informaiton it needs, and the presentation.
* All code should be well-documented so that anyone can fork the project as they choose.
* User documentation should be present.

# Status
**elephant**: Command line interface - Started

**elephant-gui**: GUI interface - Not Started

**ElephantBrain**: Database interface - Started

**ElephantTrunk**: Reporting interface - Started

**ElephantLog**: Logging wrapper - Code complete

**Reporting documentation** - Not Started

**User documentation** - Not Started
