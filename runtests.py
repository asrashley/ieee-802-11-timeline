import sys,os

sys.stderr= open('test-err.log','wt')
sys.stdout= open('test-out.log','wt')

os.execlp('python','python','manage.py','test')