"""Generate Ed25519 keypair for local Windows MT5/Telegram worker.

Only upload the PUBLIC key into cloud database using an operator-controlled workflow.
Private key stays outside Git, locally under Windows file ACLs.
"""
import argparse,os,stat,secrets
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,PublicFormat,NoEncryption

p=argparse.ArgumentParser();p.add_argument('--private-path',required=True);p.add_argument('--public-path',required=True);a=p.parse_args()
private=Path(a.private_path).resolve();public=Path(a.public_path).resolve()
if private==public:raise SystemExit('Private and public paths must differ')
private.parent.mkdir(parents=True,exist_ok=True)
key=Ed25519PrivateKey.generate();b=key.private_bytes(Encoding.PEM,PrivateFormat.PKCS8,NoEncryption())
# Exclusive creation prevents overwriting/reusing an existing identity.
with os.fdopen(os.open(str(private),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),'wb') as f:f.write(b)
os.chmod(private,stat.S_IRUSR|stat.S_IWUSR)
with os.fdopen(os.open(str(public),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644),'wb') as f:f.write(key.public_key().public_bytes(Encoding.PEM,PublicFormat.SubjectPublicKeyInfo))
print('Signing keys created. NEVER upload the private key. PUBLIC path:',public)
