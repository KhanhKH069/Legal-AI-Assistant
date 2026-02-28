"""Gateway tests"""
from src.services.database import SQLDatabase

from src.core.gateway import APIGateway
from src.services.audit import AuditLogger


def test_auth():
    db = SQLDatabase()
    audit = AuditLogger(db)
    gw = APIGateway(audit)
    assert gw.authenticate("user001")
