"""EdgeQuant Windows MT5 connectivity agent: status-only, NO trade execution."""
from __future__ import annotations
import hashlib
import json
import os
import platform
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

HEARTBEAT_SECONDS=30

def valid_api_base(url: str) -> str:
    parsed=urlsplit(url)
    local=parsed.hostname in ('localhost','127.0.0.1','::1')
    if parsed.scheme!='https' and not (local and parsed.scheme=='http'):
        raise ValueError('HTTPS required outside localhost')
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Invalid API URL')
    return url.rstrip('/')

def worker_identity() -> str:
    raw=os.getenv('EDGEQUANT_WORKER_ID') or platform.node() or 'windowsworker'
    return re.sub(r'[^a-zA-Z0-9_.:@-]', '-', raw)[:120]

def get_terminal_state(mt5) -> dict[str,object]:
    account=mt5.account_info()
    terminal=mt5.terminal_info()
    if account is None or terminal is None:
        return {'accountLogin':'0000','accountServer':'DISCONNECTED','terminalConnected':False,'tradeAllowed':False}
    connected=bool(getattr(terminal,'connected',False))
    allowed=bool(getattr(terminal,'trade_allowed',False) and getattr(account,'trade_allowed',False)) if connected else False
    return {'accountLogin':str(account.login),'accountServer':str(account.server),'terminalConnected':connected,'tradeAllowed':allowed}

def request_json(base:str,route:str,data:dict,token:str) -> dict:
    req=Request(base+route,json.dumps(data,separators=(',',':')).encode('utf-8'),
       {'Content-Type':'application/json','Authorization':'Bearer '+token},method='POST')
    with urlopen(req,timeout=12) as response:
        return json.load(response)

def agent_secret_path() -> Path:
    local=os.environ.get('LOCALAPPDATA')
    if not local:
        raise RuntimeError('Windows LOCALAPPDATA not available')
    account_key=(os.environ['EDGEQUANT_MT5_SERVER'].strip().lower()+':' + os.environ['EDGEQUANT_MT5_LOGIN'].strip())
    account_id=hashlib.sha256(account_key.encode('utf-8')).hexdigest()[:24]
    return Path(local)/'EdgeQuant'/'agents'/(account_id+'.dpapi')

def save_agent_token(token:str)->None:
    if sys.platform!='win32':
        raise RuntimeError('Windows DPAPI only')
    import win32crypt
    path=agent_secret_path()
    path.parent.mkdir(parents=True,exist_ok=True)
    encrypted=win32crypt.CryptProtectData(token.encode('ascii'),'EdgeQuant Worker',None,None,None,0)
    temp=path.with_suffix('.tmp')
    temp.write_bytes(encrypted)
    temp.replace(path)

def load_agent_token() -> str|None:
    path=agent_secret_path()
    if not path.exists():
        return None
    import win32crypt
    return win32crypt.CryptUnprotectData(path.read_bytes(),None,None,None,0)[1].decode('ascii')

def matches_expected(state:dict,server:str,login:str)->bool:
    return state['terminalConnected'] is True and state['accountLogin']==login and str(state['accountServer']).lower()==server.lower()

def main()->None:
    if sys.platform!='win32':
        raise RuntimeError('Windows-only MT5 agent')
    base=valid_api_base(os.environ['EDGEQUANT_API_URL'])
    server=os.environ['EDGEQUANT_MT5_SERVER'].strip()
    login=os.environ['EDGEQUANT_MT5_LOGIN'].strip()
    if not re.fullmatch(r'[0-9]{4,20}',login) or not server:
        raise ValueError('Invalid MT5 server/login')
    import MetaTrader5 as mt5
    path=os.getenv('EDGEQUANT_MT5_TERMINAL_PATH')
    initialized=mt5.initialize(path=path) if path else mt5.initialize()
    if not initialized:
        raise RuntimeError('MT5 initialization failed')
    try:
        token=load_agent_token()
        if not token:
            pair=os.getenv('EDGEQUANT_PAIRING_TOKEN')
            bootstrap=os.getenv('EDGEQUANT_WORKER_BOOTSTRAP_SECRET')
            if not pair or not bootstrap:
                raise RuntimeError('Provision worker secret and one-time pairing token')
            state=get_terminal_state(mt5)
            if not matches_expected(state,server,login):
                raise RuntimeError('Observed MT5 account does not match expected server/login')
            answer=request_json(base,'/api/v1/agents/claim',
                {'pairingToken':pair,'workerId':worker_identity(),**state},bootstrap)
            token=answer['agentToken']
            save_agent_token(token)
            print('Agent token saved with Windows DPAPI. No trading enabled.')
        while True:
            state=get_terminal_state(mt5)
            if not state['terminalConnected'] and state['accountServer']=='DISCONNECTED':
                state.update(accountLogin=login,accountServer=server)
            if state['terminalConnected'] and not matches_expected(state,server,login):
                raise RuntimeError('Wrong MT5 account; worker stopped')
            try:
                reply=request_json(base,'/api/v1/agents/heartbeat',state,token)
                print('MT5 connectivity:',reply.get('status','UNKNOWN'))
            except HTTPError as exc:
                if exc.code in (401,403,409):
                    raise RuntimeError('Worker rejected/revoked') from exc
                print('Heartbeat server temporarily unavailable')
            except (URLError,TimeoutError):
                print('Heartbeat network failure; server will mark stale')
            time.sleep(HEARTBEAT_SECONDS)
    finally:
        mt5.shutdown()

if __name__=='__main__':
    try:
        main()
    except (KeyError,ValueError,RuntimeError) as exc:
        print('MT5 worker failed:',exc,file=sys.stderr)
        raise SystemExit(1)
