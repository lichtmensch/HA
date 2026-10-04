"""Bounded local QNAP/UniFi adapter. Credentials stay in existing HA entries."""
import base64, http.cookiejar, json, socket, ssl, sys
from pathlib import Path
from urllib import request, parse, error
import xml.etree.ElementTree as ET

CONFIG = Path('/config/.storage/core.config_entries')

def entries():
    if '--stdin-config' in sys.argv:
        return json.load(sys.stdin)['data']['entries']
    return json.loads(CONFIG.read_text())['data']['entries']

def config(domain):
    return next(e['data'] for e in entries() if e['domain']==domain)

class Client:
    def __init__(self, data, domain):
        self.data=data
        protocol='https' if domain=='unifi' or data.get('ssl') else 'http'
        self.base=f"{protocol}://{data['host']}:{data.get('port',443 if protocol=='https' else 80)}"
        # Retain the user's existing integration certificate setting.
        context=ssl.create_default_context() if data.get('verify_ssl',True) else ssl._create_unverified_context()
        self.opener=request.build_opener(request.HTTPSHandler(context=context),request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def raw(self,path,data=None,form=False):
        headers={}
        if data is not None:
            headers['Content-Type']='application/x-www-form-urlencoded' if form else 'application/json'
            data=(parse.urlencode(data) if form else json.dumps(data)).encode()
        return self.opener.open(request.Request(self.base+path,data=data,headers=headers),timeout=12).read()
    def api(self,path,data=None):
        result=json.loads(self.raw(path,data))
        if result.get('meta',{}).get('rc')!='ok':
            raise ValueError('UniFi meldet keine erfolgreiche API-Antwort')
        return result['data']

def unifi_check():
    c=Client(config('unifi'),'unifi')
    c.api('/api/login',{'username':c.data['username'],'password':c.data['password']})
    site=parse.quote(c.data.get('site','default'),safe='')
    devices=c.api(f'/api/s/{site}/stat/device')
    system=c.api(f'/api/s/{site}/stat/sysinfo')
    if any(d.get('state')==4 for d in devices):
        return {'ok':False,'status':'busy','error':'Firmware-Aktualisierung laeuft'}
    if not devices or any(not isinstance(d.get('upgradable'),bool) for d in devices):
        raise ValueError('Update-Status unvollstaendig')
    updates=[{'name':d.get('name',d.get('model','UniFi')), 'installed':d.get('version','?'), 'available':d.get('upgrade_to_firmware','?')} for d in devices if d.get('upgradable')]
    if not system or not isinstance(system[0].get('update_available'),bool):
        raise ValueError('Controller-Update-Status fehlt')
    if system[0]['update_available']:
        updates.append({'name':'UniFi Network Controller','installed':system[0].get('version','?'),'available':'Controller meldet neue Version'})
    result={'ok':True,'status':'updates' if updates else 'current','device_count':len(devices),'updates':updates,'controller_version':system[0].get('version','?')}
    try: c.raw('/logout',{})
    except Exception: pass
    return result

def qnap_login():
    c=Client(config('qnap'),'qnap')
    pwd=base64.b64encode(c.data['password'].encode()).decode()
    root=ET.fromstring(c.raw('/cgi-bin/authLogin.cgi',{'user':c.data['username'],'pwd':pwd},form=True))
    sid=root.findtext('authSid')
    if root.findtext('authPassed')!='1' or not sid:
        raise ValueError('QNAP-Anmeldung fehlgeschlagen')
    return c,sid

def qnap_auth_check():
    c,sid=qnap_login()
    c.raw('/cgi-bin/authLogout.cgi',{'sid':sid},form=True)
    return {'ok':True,'status':'authenticated'}

def shutdown():
    c,sid=qnap_login()
    body=c.raw('/cgi-bin/sys/sysRequest.cgi',{'sid':sid,'subfunc':'power_mgmt','apply':'shutdown'},form=True)
    root=ET.fromstring(body)
    if root.findtext('authPassed')!='1':
        raise ValueError('QNAP-Shutdown nicht bestaetigt')
    return {'ok':True,'status':'shutdown_requested'}

def probe():
    try:
        with socket.create_connection((config('qnap')['host'],443),timeout=3): pass
        return {'ok':True,'online':True}
    except OSError:
        return {'ok':True,'online':False}

if __name__=='__main__':
    try:
        commands={'probe':probe,'check':unifi_check,'shutdown':shutdown,'auth-check':qnap_auth_check}
        print(json.dumps(commands[sys.argv[1]](),ensure_ascii=False))
    except Exception as e:
        # No URLs, credentials or session tokens in output.
        print(json.dumps({'ok':False,'status':'error','error':type(e).__name__,'code':getattr(e,'code',None)},ensure_ascii=False))
