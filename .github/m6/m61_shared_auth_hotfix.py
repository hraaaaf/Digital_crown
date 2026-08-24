from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    src = p.read_text()
    count = src.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, got {count}")
    p.write_text(src.replace(old, new))


auth_path = "backend/routers/auth.py"

replace_once(
    auth_path,
    '''    # Cookie-first, fallback Authorization header\n    token = request.cookies.get("access_token") or token_header\n    if not token:\n        raise credentials_exception\n''',
    '''    # Desktop reste cookie-first, mais un Bearer explicitement mobile doit\n    # rester device-bound même si un cookie web existe dans le même navigateur.\n    mobile_header = False\n    if token_header:\n        try:\n            mobile_header = jwt.get_unverified_claims(token_header).get("type") == "mobile"\n        except (JWTError, ValueError, TypeError):\n            mobile_header = False\n    token = token_header if mobile_header else (request.cookies.get("access_token") or token_header)\n    if not token:\n        raise credentials_exception\n''',
)

replace_once(
    auth_path,
    '''        if token_type == "mobile":\n            # sub est l'employer_id (int) pour les tokens mobiles\n            user_id = int(payload["sub"])\n            user = db.query(models.User).filter(models.User.id == user_id).first()\n        else:\n''',
    '''        if token_type == "mobile":\n            # Une session mobile ne peut jamais devenir un simple access token web.\n            # Réutiliser le validateur mobile canonique garde user/tenant/device et\n            # révocation alignés sur les routes /api/mobile/* et les routes partagées.\n            from backend.routers.mobile_legacy import _decode_mobile_identity\n            user, _tenant_id, _mobile_payload = _decode_mobile_identity(f"Bearer {token}", db)\n        else:\n''',
)

replace_once(
    auth_path,
    '''    except (JWTError, ValueError, KeyError):\n        raise credentials_exception\n''',
    '''    except HTTPException:\n        raise credentials_exception\n    except (JWTError, ValueError, KeyError, TypeError):\n        raise credentials_exception\n''',
)


test_path = Path("backend/tests/test_mobile_identity_security.py")
test_src = test_path.read_text()
replace = "from backend.security import ALGORITHM, SECRET_KEY, get_password_hash, token_blacklist\n"
if test_src.count(replace) != 1:
    raise SystemExit("security import anchor mismatch")
test_src = test_src.replace(
    replace,
    "from backend.security import ALGORITHM, SECRET_KEY, create_access_token, get_password_hash, token_blacklist\n",
)

marker = "\ndef test_admin_revoke_mobile_invalidates_claimed_device_and_refresh(client, db, dentiste, monkeypatch):\n"
if test_src.count(marker) != 1:
    raise SystemExit("test append anchor mismatch")

new_tests = r'''

def test_shared_auth_me_accepts_valid_device_bound_mobile_token(client, db, dentiste):
    body = _claim(client, _pairing(db, dentiste, dentiste)).json()
    response = client.get(
        '/api/auth/me',
        headers={'Authorization': f"Bearer {body['access_token']}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()['id'] == dentiste.id


def test_shared_auth_me_rejects_revoked_mobile_header_even_with_valid_web_cookie(client, db, dentiste):
    body = _claim(client, _pairing(db, dentiste, dentiste)).json()
    device = db.query(models.MobilePairedDevice).filter(
        models.MobilePairedDevice.device_id == body['device_id']
    ).one()
    device.revoked_at = datetime.utcnow()
    db.commit()

    # Un cookie desktop valide ne doit jamais masquer un Bearer mobile révoqué.
    client.cookies.set('access_token', create_access_token(data={'sub': dentiste.email}))
    response = client.get(
        '/api/auth/me',
        headers={'Authorization': f"Bearer {body['access_token']}"},
    )
    client.cookies.clear()
    assert response.status_code == 401, response.text


def test_shared_auth_me_rejects_mobile_tenant_mismatch(client, db, dentiste):
    device = models.MobilePairedDevice(
        device_id=str(uuid.uuid4()),
        user_id=dentiste.id,
        employer_id=dentiste.id,
        client_public_key_hex=_client_public_key(),
        refresh_jti='refresh-shared-auth-tenant',
    )
    db.add(device)
    db.commit()
    forged = _create_mobile_jwt(
        dentiste.id,
        'DENTISTE',
        dentiste.id + 99999,
        device.device_id,
    )
    response = client.get('/api/auth/me', headers={'Authorization': f'Bearer {forged}'})
    assert response.status_code == 401, response.text


def test_shared_auth_me_rejects_legacy_mobile_token_without_device(client, dentiste):
    legacy = jwt.encode(
        {
            'sub': str(dentiste.id),
            'tenant_id': dentiste.id,
            'type': 'mobile',
            'role': 'DENTISTE',
            'jti': str(uuid.uuid4()),
            'exp': datetime.utcnow() + timedelta(hours=1),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    response = client.get('/api/auth/me', headers={'Authorization': f'Bearer {legacy}'})
    assert response.status_code == 401, response.text
'''

test_src = test_src.replace(marker, new_tests + marker)
test_path.write_text(test_src)
