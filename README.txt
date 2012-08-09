GT Phi Psi - The Georgia Beta Chapter of the Phi Kappa Psi Fraternity

This is a Django-based web application called gtphipsi. It is still under development, but it is ultimately intended to replace the chapter's current website, located at http://gtphipsi.org/. The content of the public pages mirrors that of the current site, but this Django rewrite offers several improvements over the current version:

* New (and improved!) layout and design, including the chapter's new logo
* Modular structure providing separation of concerns and easy extensibility
* Easy-to-read and easy-to-maintain Python code base (no more PHP!)
* Database integration!
* Brothers-only section with many capabilities...
     - CRUD rush schedules, including individual events and the rush as a whole
     - CRUD announcements, which (if made public) are shown to non-brothers as well
     - brothers can create profiles to keep track of each other after graduating
     - profile visibility settings are easily customizable, and can be different for brothers and for non-brothers
     - user administration (creating new accounts, resetting passwords, etc.)

I intend to add additional brothers-only content, such as a Dropbox-style shared file storage area and a forum section to replace long email threads. And yet, knowing how many dozens of hours that functionality will take to write, in the short term I plan to polish up the code I have written so far and focus on the initial deployment from there.

All code was written by me, William Dye. Feel free to contact me with any comments or questions at williamdye@gatech.edu.

