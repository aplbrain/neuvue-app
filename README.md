# neuvue
MICrONS Proofreading App
## Install
- Install [nvm](https://github.com/nvm-sh/nvm)
- Install neuroglancer
	```
	git clone https://github.com/aplbrain/neuroglancer
	nvm install --lts
	cd neuroglancer
	npm i
	npm run build
	npm link
	```
## How to run the app locally

- create a virtual environment using the requirements.txt file 
- activate the environment

- Build the NG wrapper
	```
	cd django/static/ts/wrapper
	ln -s <path-to-neuroglancer>/src/neuroglancer ./third_party/neuroglancer
	npm i
	npm link neuroglancer
	``` 
- check for django updates:
	- run `python3 manage.py makemigrations` 
	- run `python3 manage.py migrate`
- run `python3 manage.py runserver localhost:8000` 
- navigate to [http://127.0.0.1:8000/]( http://127.0.0.1:8000/) in your browser
