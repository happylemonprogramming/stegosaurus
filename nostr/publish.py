import asyncio, os, json, ast
from datetime import timedelta
from nostr_sdk import Keys, Client, NostrSigner, Metadata, HttpData, HttpMethod, EventId, EventBuilder, Filter, EventSource, init_logger, LogLevel
init_logger(LogLevel.WARN)

# Get relay list
relay_str = os.environ["relaylist"]
relaywss_list = ast.literal_eval(relay_str)

def hex_to_note(target_eventID):
    note = EventId.from_hex(target_eventID).to_bech32()
    return note

# Publish content to nostr
async def nostrpost(private_key, content, kind=None, reply_to=None, url=None, payload=None, tags=[]):
    # Initialize with Keys signer
    keys = Keys.parse(private_key)
    signer = NostrSigner.keys(keys)
    client = Client(signer)

    # Add relays and connect
    for relay in relaywss_list:
        await client.add_relay(relay)
    await client.connect()

    # Send an event using the Nostr Signer
    if content and reply_to: # Replies
        # Create Event Object
        f = Filter().id(EventId.parse(reply_to))
        source = EventSource.relays(timeout=timedelta(seconds=10))
        reply_to = await client.get_events_of([f], source)
        reply_to = reply_to[0]
        builder = EventBuilder.text_note_reply(content=content, reply_to=reply_to)
    elif url and payload: # NIP98
        builder = EventBuilder.http_auth(HttpData(url=url, method=HttpMethod.POST, payload=payload))
    elif kind == 0: # Metadata
        builder = EventBuilder.metadata(Metadata.from_json(content))
    else: # Default to Text Note
        builder = EventBuilder.text_note(content=content, tags=tags)
    await client.send_event_builder(builder)

    # Allow note to send
    await asyncio.sleep(2.0)
    
    # Get event ID from relays
    f = Filter().authors([keys.public_key()]).limit(1)
    source = EventSource.relays(timedelta(seconds=10))
    events = await client.get_events_of([f], source)
    for event in events:
        event = event.as_json()
        eventID = json.loads(event)['id']
    
    return eventID

if __name__ == "__main__":
    # Publish Note
    # private_key = os.environ["nostrdvmprivatekey"]
    # pubkey = Keys.parse(private_key).public_key()
    # content = 'test again'
    # event = '3589d9a28644890fd3904d11854669327a2c19f4123760dd68bbaccd9502fc9e'
    # eventID = asyncio.run(nostrpost(private_key, content=content, reply_to=event))
    # print(eventID)

    # Publish Metadata
    private_key = os.environ["swanndvmprivatekey"]
    pubkey = Keys.parse(private_key).public_key()
    content = {"name":"Swann Machine","display_name":"SwannDVM","about":"Text-to-speech DVM\nThe legendary voice of nostr:npub1h8nk2346qezka5cpm8jjh3yl5j88pf4ly2ptu7s6uu55wcfqy0wq36rpev\nBot built by nostr:npub1hee433872q2gen90cqh2ypwcq9z7y5ugn23etrd2l2rrwpruss8qwmrsv6","picture":"https://m.primal.net/IyOX.png","banner":"https://m.primal.net/JAfV.jpg","lud16":"palekangaroo1@primal.net","displayName":"SwannDVM"}
    content = json.dumps(content)
    eventID = asyncio.run(nostrpost(private_key, kind=0, content=content))
    print(eventID)