import pytest
from httpx import AsyncClient
from app.core.auth.models import User
from app.core.communication.messages.models import Message, MessageStatus

@pytest.mark.asyncio
async def test_send_message(client: AsyncClient, auth_headers: dict, doctor_user: User, nurse_user: User):
    res = await client.post(
        "/api/v1/communication/message/",
        headers=auth_headers,
        json={
            "receiver_id": str(nurse_user.id),
            "message_content": "Patient 123 needs attention",
            "message_type": "text"
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["message_content"] == "Patient 123 needs attention"
    assert data["status"] == MessageStatus.SENT.value
    assert data["sender_id"] == str(doctor_user.id)

@pytest.mark.asyncio
async def test_receive_message_and_mark_read(client: AsyncClient, auth_headers: dict, doctor_user: User, nurse_user: User):
    # Setup
    send_res = await client.post(
        "/api/v1/communication/message/",
        headers=auth_headers,
        json={
            "receiver_id": str(nurse_user.id),
            "message_content": "Hello nurse",
            "message_type": "text"
        }
    )
    msg_id = send_res.json()["id"]

    # 1. Fetch conversations with that nurse
    res = await client.get(f"/api/v1/communication/message/{nurse_user.id}", headers=auth_headers)
    assert res.status_code == 200
    msgs = res.json()
    assert len(msgs) >= 1

    # 2. Mark as read
    read_res = await client.put(f"/api/v1/communication/message/{msg_id}/read", headers=auth_headers)
    assert read_res.status_code == 200
    assert read_res.json()["status"] == MessageStatus.READ.value

@pytest.mark.asyncio
async def test_alert_creation_and_workflow(client: AsyncClient, auth_headers: dict, test_patient):
    # Create Alert
    alert_res = await client.post(
        "/api/v1/communication/alert/",
        headers=auth_headers,
        json={
            "patient_id": str(test_patient.id),
            "alert_type": "critical_lab",
            "severity": "critical",
            "message": "Hemoglobin level critically low"
        }
    )
    assert alert_res.status_code == 201
    alert_id = alert_res.json()["id"]

    # Acknowledge Alert
    ack_res = await client.put(
        f"/api/v1/communication/alert/{alert_id}/acknowledge",
        headers=auth_headers
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["acknowledged_by"] is not None

@pytest.mark.asyncio
async def test_channel_messaging(client: AsyncClient, auth_headers: dict):
    # Create channel
    chan_res = await client.post(
        "/api/v1/communication/channel/",
        headers=auth_headers,
        json={
            "channel_name": "Emergency Staff",
            "department": "ER"
        }
    )
    assert chan_res.status_code == 201
    chan_id = chan_res.json()["id"]

    # Post message
    msg_res = await client.post(
        "/api/v1/communication/channel/message",
        headers=auth_headers,
        json={
            "channel_id": chan_id,
            "message_content": "Code Blue in ER 1"
        }
    )
    assert msg_res.status_code == 201

    # Fetch
    get_res = await client.get(f"/api/v1/communication/channel/{chan_id}/messages", headers=auth_headers)
    assert get_res.status_code == 200
    assert len(get_res.json()) == 1
