coverage run --source=ballot,project,timeline,util --omit=django,dbindexer,djangoappengine,djangotoolbox,autoload manage.py test project ballot project report timeline util
coverage report 
coverage html
