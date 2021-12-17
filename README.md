<h3 align=center>Neuvue</h3>
<h6 align=center>Proofreading web-app and task management system</h6>

## Installation

Create a python3 virtual environment and install the requirements in neuvue_project/requirements.txt. 

```shell
python -m venv venv
source  venv/bin/activate
pip install -r neuvue_project/requirements.txt
```


## (optional) Compiling the neuroglancer project

A working neuroglancer compilation is included under `neuvue_project/workspace/static/workspace/`. However, if the underlying neuroglancer client needs to change,it must be compiled and linked.

Requirements: [nvm](https://github.com/nvm-sh/nvm)

1. Clone the neuroglancer repo, and build it
	```
	git clone https://github.com/aplbrain/neuroglancer
	nvm install --lts
	cd neuroglancer
	npm i
	npm run build
	npm link
	```

1. Build the NG wrapper
	```
	cd neuvue_project/workspace/static/ts/wrapper
	ln -s <absolute-path-to-neuroglancer>/src/neuroglancer ./third_party/neuroglancer
	npm i
	npm link neuroglancer
	npm run build
	``` 
1. Copy the built files to static
	```
	cd neuvue_project/workspace/static/ts/wrapper
	cp -r dist/workspace ../../
	```

## Running a development environment

For development purposes, there is a included neuvueDB.sqlite3 database file containing the tables needed to run the Django app. By default, the settings are configured for production which uses a cloud-enabled MySQL datatbase server. Here are the steps to enable development mode. 

1. Open `neuvue_project/neuvue/settings.py` and set `DEBUG=True`

2. In the same file, modify `NEUVUE_QUEUE_ADDR` variable to the Nuevue-Queue endpoint you would like to use. 

3. Get the recent migrations to the database by running 

	`python manage.py migrate`

4. (OPTIONAL) Create a superuser to modify the app in your development environment.

	`python manage.py createsuperuser`

5. Run the app with the `runserver` command to start a development instance. Run on the localhost:8000 address and port to allow OAuth client to properly authenticate user. 

	`python manage.py runserver localhost:8000`

6. Open your app on http://localhost:8000 

## Deploying to production

We use AWS Elastic Beanstalk to deploy Neuvue. To re-deploy after changes are made to the production branch, follow the instructions below.

1. Update your AWS credentials in `~/.aws/credentials` file with a long-lived token generated on cloudmanager.jhuapl.edu.

2. Install the elastic beanstalk CLI and restart the terminal.

	`sudo pip install --upgrade awsebcli`

3. Change directories to `neuvue_project` and run `eb init`. This will connect to the current deployment environment. 

	```bash
	cd neuvue_project
	eb init
	```

4. (OPTIONAL) Run `eb health` to check the current status of the app. 

5. Run `eb deploy` to upload your local environment to the production system. You do not have to run `manage.py collectstatic`, elastic beanstalk will do this for you. 

Modifications to the elastic beanstalk environment (database, instance types, error logs, etc) are best handled directly throught the AWS console. 


## OAuth Set-up

The included development database is preconfigured to allow OAuth to authetnticate user accounts from `localhost:8000`. For a more complete guide on how this was done, refer to this link: 

https://www.section.io/engineering-education/django-google-oauth/

We use `django-allauth` to connect Google OAuth to the Django environment. Users also have the option to log in through the base allauth login/signup page:

http://localhost:8000/accounts/login/

Django users, OAuth settings, and site configuration can be modified in the admin console. 

http://localhost:8000/admin


## Cloud Blueprint

<img src="Neuvue_Blueprint.png" style="background-color: rgb(300, 300, 300);">
