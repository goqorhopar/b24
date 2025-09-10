import os, requests
BITRIX_WEBHOOK_URL = os.getenv('BITRIX_WEBHOOK_URL')

def update_lead_comment(lead_id: str, comment: str):
    url = BITRIX_WEBHOOK_URL.rstrip('/') + '/crm.lead.update.json'
    payload = {'id': lead_id, 'fields': {'COMMENTS': comment}, 'params': {'REGISTER_SONET_EVENT': 'Y'}}
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()
