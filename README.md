# Item Catalog
This project is required for Udacity's Full Stack Web Developer Nanodegree program.

# Introduction
A web application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own categories and items.

# Prerequisites
__1. Start	with	Software	Installation:__
* Vagrant:	https://www.vagrantup.com/downloads.html	
* Virtual	Machine:	https://www.virtualbox.org/wiki/Downloads	
* Download	a	FSND	virtual	machine:	https://github.com/udacity/fullstack-nanodegree-vm	
<br /> __Note:__ You	will	also	need	a	Unix-style	terminal	program.	On	Mac	or	Linux	systems,	you	can	use	the	built-in	Terminal.	On	Windows, Git	Bash is recommended,	which	is	installed	with	the	Git	version	control	software.	
<br />Once	you	get	the	above	software	installed,	follow	the	following	instructions:	
<br />1. cd vagrant.
<br />2. vagrant up.
<br />3. vagrant ssh. 
<br />4. cd /vagrant.
<br />5. mkdir catalog.
<br />6. cd catalog. 
 
__2. Write your Flask application locally in the vagrant/catalog directory (which will automatically be synced to /vagrant/catalog within the VM).__

__3. Create a setup application database: catalog/database_setup.py.__
</br>__4. seed it with fake date catalog/seeder.py.__

# Run The Project
1. Make sure that you have vagrant up and connected to it.
2. cd into the correct project directory: cd /vagrant/catalog.
3. Run python database_setup.py.
4. Run seeder.py to seed it.
5. Run item_catalog.py.
6. Access and test your application by visiting http://localhost:4000 locally

# Add Google Sign in
1. go to the link https://console.developers.google.com/apis/dashboard?pli=1
2. Choose Credentials.
3. Create an OAuth Client ID.
4. configure the consent screen.
5. Select Web application.
6. write name 'Item-Catalog'
7. set the authorized JavaScript origins'http://localhost:4000'
8. set redirect URIs: (http://localhost:4000/login) and (http://localhost:4000/gconnect) then click Create.
9. Copy the Client ID and paste it into the data-clientid in login.html.
10. Download JSON and place it in catalog directory
11. Run application.

# JSON Endpoints
The project implements a JSON endpoint that serves the same information as displayed in the HTML endpoints for an arbitrary item in the catalog.
1. '/catalog/JSON' - Returns JSON of all categories in catalog
2. '/catalog/<path:category_name>/items/JSON' - Returns JSON of all items of specified category
3. '/catalog/<path:category_name>/<path:item_name>/JSON' - Returns JSON of specified category item
