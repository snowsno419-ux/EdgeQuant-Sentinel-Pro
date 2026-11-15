"""EdgeQuant Sentinel Pro: signed, READ-ONLY MetaTrader 5 DEMO telemetry worker.
Requires an isolated Windows VM, Python, MetaTrader5 and cryptography. NEVER sends orders.
No broker passwords or real-money trading are supported.
Install on Windows: py -m pip install MetaTrader5 cryptography
"""
import argparse, base64, getpass, json, os, secrets, sys, time, urllib.request, urllib.error
from pathlib import Path
import MetaTrader5 as mt5
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

ROOT=Path.home()/".edgequant_demo_worker"
IDENTITY=ROOT/"identity.json"
BASE="https://edgequant-mobile-web.vercel.app"

def keys():
    if IDENTITY.exists():
        state=json.loads(IDENTITY.read_text(encoding="utf8"))
    else:
        ROOT.mkdir(parents=True,exist_ok=True)
        private=Ed25519PrivateKey.generate()
        data=private.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()).decode()
        state={"worker_id":secrets.token_hex(16),"private_pem":data}
        fd=os.open(str(IDENTITY),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,"w",encoding="utf8") as f: json.dump(state,f)
        print("Created private Ed25519 worker identity; restrict local Windows user permissions.")
    private=serialization.load_pem_private_key(state["private_pem"].encode(),password=None)
    if not isinstance(private,Ed25519PrivateKey): raise RuntimeError("Invalid private key type")
    return state["worker_id"],private

def mt5_account(terminal=None):
    ok=mt5.initialize(path=terminal) if terminal else mt5.initialize()
    if not ok: raise RuntimeError("MT5 did not initialize: open your logged-in DEMO terminal first")
    info=mt5.account_info()
    if info is None or info.trade_mode!=mt5.ACCOUNT_TRADE_MODE_DEMO:
        mt5.shutdown()
        raise RuntimeError("ONLY DEMO MT5 accounts are accepted; real accounts are blocked")
    return info

def request(url,payload,signature=None):
    if not url.startswith("https://edgequant-mobile-web.vercel.app/"): raise RuntimeError("Unexpected cloud API origin")
    headers={"Content-Type":"application/json"}
    if signature: headers["x-eq-signature"]=signature
    data=json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode()
    req=urllib.request.Request(url,data=data,headers=headers,method="POST")
    try:
        with urllib.request.urlopen(req,timeout=12) as r:
            return r.status,json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError("Cloud request rejected, HTTP "+str(e.code)) from None

def signature(private,payload):
    raw=json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()
    return base64.b64encode(private.sign(raw)).decode()

def pair(args):
    info=mt5_account(args.terminal)
    try:
        worker_id,private=keys()
        token=getpass.getpass("One-time 15-minute worker pairing token (hidden): ").strip()
        if not token: raise RuntimeError("Pairing token is required")
        login,server=str(info.login),str(info.server)
        proof="\n".join(["EDGEQUANT-MT5-PAIR-V1",token,worker_id,server,login])
        pub=private.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        payload={"login_hint":login,"public_key_pem":pub,"server":server,
            "signature":base64.b64encode(private.sign(proof.encode())).decode(),
            "token":token,"worker_id":worker_id}
        code,data=request(BASE+"/api/mt5-pair-claim",payload)
        if code!=202 or not data.get("claimed"): raise RuntimeError("Worker claim not accepted")
        import hashlib
        print("Claim received. On your phone, CHECK PAIR STATUS and verify fingerprint:")
        print(hashlib.sha256(pub.encode()).hexdigest()[:24])
        print("Worker ID:",worker_id,"server:",server,"DEMO login:",login)
        print("Approve only if these match your own trusted Windows worker.")
    finally: mt5.shutdown()

def observe(args):
    if not args.broker_id or not args.login or not args.server:
        raise RuntimeError("observe needs --broker-id, --login and --server")
    worker_id,private=keys()
    while True:
        try:
            info=mt5_account(args.terminal)
            try:
                if str(info.login)!=args.login or str(info.server)!=args.server:
                    raise RuntimeError("DEMO account/server mismatch; no data sent")
                payload={"balance":format(info.balance,".2f"),"broker_id":args.broker_id,
                  "equity":format(info.equity,".2f"),"event_id":secrets.token_hex(16),
                  "floating":format(info.profit,".2f"),"login_hint":args.login,
                  "mode":"DEMO","open_positions":len(mt5.positions_get() or ()),
                  "pending_orders":len(mt5.orders_get() or ()),
                  "server":args.server,"terminal_connected":True,
                  "timestamp_ms":int(time.time()*1000),"worker_id":worker_id}
                code,data=request(BASE+"/api/worker-observation",payload,signature(private,payload))
                if code!=202 or data.get("accepted") is not True: raise RuntimeError("Signed observation rejected")
                print("Signed DEMO status received by EdgeQuant at",time.strftime("%H:%M:%S"))
            finally: mt5.shutdown()
        except (RuntimeError,urllib.error.URLError) as exc:
            print("Read-only status:",str(exc),file=sys.stderr)
        if args.once: return
        time.sleep(30)

def main():
    parser=argparse.ArgumentParser(description="EdgeQuant Windows cloud read-only MT5 DEMO worker")
    parser.add_argument("mode",choices=["pair","observe"])
    parser.add_argument("--broker-id")
    parser.add_argument("--server")
    parser.add_argument("--login")
    parser.add_argument("--terminal",help="Optional path to already-logged-in terminal64.exe")
    parser.add_argument("--once",action="store_true")
    args=parser.parse_args()
    pair(args) if args.mode=="pair" else observe(args)
if __name__=="__main__": main()
