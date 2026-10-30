"""LOT07 R5 07-D DEV API: isolation, strict allowlist and server rollback."""
import secrets
import hashlib
import pytest

from backend import models
from backend.security import get_password_hash
from backend.config import settings


def _token(client, email, password):
    r=client.post("/api/auth/login",data={"username":email,"password":password})
    assert r.status_code == 200,r.text
    value=r.json()["access_token"]
    client.cookies.delete("access_token")
    client.cookies.delete("refresh_token")
    return {"Authorization":f"Bearer {value}"}


def _station(client, header):
    r=client.get("/api/workstation/state",headers=header)
    assert r.status_code == 200,r.text
    assert client.cookies.get("dc_workstation")
    return r.json()["workstationId"]


def _pref(user,tenant,station,mode="iconic"):
    return {"version":1,"tenantId":str(tenant),"userId":str(user),
            "workstationId":station,"signature":mode,"layout":None}


def test_r5_server_scope_conflict_rollback_and_revocation(client,db,dentiste,monkeypatch):
    monkeypatch.setattr(settings,"ENVIRONMENT","test")
    header=_token(client,dentiste.email,"TestPass123!")
    station=_station(client,header)
    base=f"/api/workstation/r5-preferences"
    r=client.get(base,headers=header)
    assert r.status_code==200 and r.json()=={"record":None,"revision":0,"canRollback":False}
    first=_pref(dentiste.id,dentiste.get_employer_id(),station)
    r=client.put(base,headers=header,json={"expectedRevision":0,"record":first})
    assert r.status_code==200,r.text
    assert r.json()["revision"]==1
    assert not r.json()["canRollback"]
    assert client.get(base,headers=header).json()["record"]==first
    assert client.put(base,headers=header,json={"expectedRevision":0,"record":first}).status_code==409
    next_record={**first,"signature":"core"}
    r=client.put(base,headers=header,json={"expectedRevision":1,"record":next_record})
    assert r.status_code==200 and r.json()["revision"]==2 and r.json()["canRollback"]
    r=client.post(base+"/rollback",headers=header,json={"expectedRevision":2})
    assert r.status_code==200 and r.json()["revision"]==3 and r.json()["record"]==first
    assert client.post(base+"/rollback",headers=header,json={"expectedRevision":2}).status_code==409
    assert db.query(models.R5DesktopPreference).count()==1

    # A station revoked in DB is immediately denied, even if an old cookie remains.
    station_row=db.query(models.WorkstationMode).filter_by(id=station).one()
    from datetime import datetime
    station_row.revoked_at=datetime.utcnow()
    db.commit()
    assert client.get(base,headers=header).status_code==423
    assert client.put(base,headers=header,json={"expectedRevision":3,"record":first}).status_code==423


def test_r5_no_phi_unknown_fields_and_authenticated_identity(client,db,dentiste,monkeypatch):
    monkeypatch.setattr(settings,"ENVIRONMENT","test")
    headers=_token(client,dentiste.email,"TestPass123!")
    station=_station(client,headers)
    url="/api/workstation/r5-preferences"
    valid=_pref(dentiste.id,dentiste.get_employer_id(),station)
    for bad in [
        {**valid,"patientId":17},
        {**valid,"token":"PRIVATE"},
        {**valid,"userId":"999999"},
        {**valid,"tenantId":"999999"},
        {**valid,"workstationId":"spoofed"},
        {**valid,"layout":{"version":1,"patient":"PRIVATE"}},
    ]:
        res=client.put(url,headers=headers,json={"expectedRevision":0,"record":bad})
        assert res.status_code in (403,422),res.text
    assert client.get(url).status_code in (401,403)

    valid_layout={**valid,"layout":{
        "version":1,"userId":str(dentiste.id),"workstationId":station,
        "id":"consultation","geometry":"two-columns",
        "slots":[{"id":"slot-1","module":"dossier"},{"id":"slot-2","module":"agenda"}],
        "ratio":50}}
    res=client.put(url,headers=headers,json={"expectedRevision":0,"record":valid_layout})
    assert res.status_code==200,res.text
    for invalid in [
        {**valid_layout,"layout":{**valid_layout["layout"],"patientId":1}},
        {**valid_layout,"layout":{**valid_layout["layout"],"id":"patient-secrecy"}},
        {**valid_layout,"layout":{**valid_layout["layout"],"slots":[
            {"id":"slot-1","module":"dossier","patientName":"X"},{"id":"slot-2","module":"agenda"}]}},
        {**valid_layout,"layout":{**valid_layout["layout"],"slots":[
            {"id":"slot-1","module":"dossier"},{"id":"slot-2","module":"dossier"}]}},
    ]:
        res=client.put(url,headers=headers,json={"expectedRevision":1,"record":invalid})
        assert res.status_code==422,res.text
    assert client.get(url,headers=headers).json()["record"]==valid_layout


def test_r5_two_users_two_workstations_and_production_flag(client,db,dentiste,monkeypatch):
    monkeypatch.setattr(settings,"ENVIRONMENT","test")
    owner=_token(client,dentiste.email,"TestPass123!")
    station_a=_station(client,owner)
    url="/api/workstation/r5-preferences"
    employee=models.User(email="r5.employee@cabinet.ma",hashed_password=get_password_hash("EmployeePass123!"),
        role=models.UserRole.ADMIN,nom_complet="R5 Employee",is_active=True,is_licensed=True,
        employer_id=dentiste.id)
    db.add(employee)
    db.commit()
    headers_b=_token(client,employee.email,"EmployeePass123!")
    assert client.get(url,headers=headers_b).json()["record"] is None
    b=_pref(employee.id,dentiste.id,station_a)
    assert client.put(url,headers=headers_b,json={"expectedRevision":0,"record":b}).status_code==200
    assert client.get(url,headers=owner).json()["record"] is None

    station_b_raw=secrets.token_urlsafe(32)
    station_b=models.WorkstationMode(employer_id=dentiste.id,
        token_hash=hashlib.sha256(station_b_raw.encode()).hexdigest(),default_experience="cabinet")
    db.add(station_b)
    db.commit()
    db.refresh(station_b)
    client.cookies.set("dc_workstation",station_b_raw)
    assert client.get(url,headers=headers_b).json()["record"] is None
    assert client.put(url,headers=headers_b,json={"expectedRevision":0,
        "record":_pref(employee.id,dentiste.id,station_b.id)}).status_code==200
    assert client.get(url,headers=headers_b).json()["record"]["workstationId"]==station_b.id
    monkeypatch.setattr(settings,"ENVIRONMENT","production")
    assert client.get(url,headers=headers_b).status_code==404

def test_r5_unverified_duplicate_cephalo_preset_is_rejected_without_write(client, db, dentiste, monkeypatch):
    """The 2-Cephalo preset stays unavailable until independent module isolation is certified."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "test")
    headers = _token(client, dentiste.email, "TestPass123!")
    station = _station(client, headers)
    record = _pref(dentiste.id, dentiste.get_employer_id(), station)
    record["layout"] = {
        "version": 1, "userId": str(dentiste.id), "workstationId": station,
        "id": "comparaison-orthodontique", "geometry": "three-columns",
        "slots": [
            {"id": "slot-1", "module": "cephalo"},
            {"id": "slot-2", "module": "cephalo"},
            {"id": "slot-3", "module": "photos"},
        ],
        "ratio": 50,
    }
    url = "/api/workstation/r5-preferences"
    response = client.put(url, headers=headers, json={"expectedRevision": 0, "record": record})
    assert response.status_code == 422, response.text
    assert response.json()["detail"] == "DUPLICATE_MODULE"
    assert client.get(url, headers=headers).json() == {
        "revision": 0, "record": None, "canRollback": False,
    }
