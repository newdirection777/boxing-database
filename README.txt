This web app provides a simple database for the sport of boxing.  
It allows you to add, edit, and delete your favorite fighters.

This app assumes you have the following already installed in your 
environment:
	-Python
	-Flask
	-SQLAlchemy
	-Oauth2client
	
Assuming all the required software is present, run the app as follows:

1. copy all the files to a single directory and cd into that directory.

2. type 'python database_setup.py'.  This will create the database, as well
	as populate the boxing categories with some sample boxers.
	
3. type 'python application.py'.  This will run the app's webserver.

4. point your browser to localhost:5000.  This will bring up the home page.

5. click the 'login' link in the upper right corner, and log in using your
	Google or Facebook account.  For best results, use Chrome.  Facebook login
	may not work on Firefox because of the default security settings on Firefox.
	If you MUST use Firefox, set 'Allow Tracking' to True in your settings.
	
6. Once you are logged in, you can add, edit, delete fighters.  Enjoy!