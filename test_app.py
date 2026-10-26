import os,base64
from app import app
c=app.test_client()
a='Basic '+base64.b64encode((os.environ['APP_USER']+':'+os.environ['APP_PASSWORD']).encode()).decode()
assert c.get('/').status_code==302
assert c.get('/login').status_code==200
assert c.post('/tasks',headers={'Authorization':a},data={'title':'Tidak boleh tersimpan','course':'Uji'}).status_code==400
with c.session_transaction() as s: token=s['csrf']
assert c.post('/login',data={'csrf':token,'username':'wrong','password':'wrong'}).status_code==401
assert c.post('/login',data={'csrf':token,'username':os.environ['APP_USER'],'password':os.environ['APP_PASSWORD']}).status_code==302
assert c.get('/').status_code==200
with c.session_transaction() as s: token=s['csrf']
assert c.post('/tasks',data={'csrf':token,'title':'','course':'Uji'}).status_code==400
assert c.post('/tasks',data={'csrf':token,'title':'Uji','course':'Uji','due':'invalid'}).status_code==400
assert c.post('/logout',data={'csrf':token}).status_code==302
assert c.get('/').status_code==302
print('PASS: redirect login, form login, login salah/benar, CSRF kosong, judul kosong, tanggal invalid, logout.')
