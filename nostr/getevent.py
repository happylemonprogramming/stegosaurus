import os, json, re, ast
from datetime import timedelta
from nostr_sdk import Client, EventId, PublicKey, Kind, Filter, EventSource, init_logger, LogLevel, Timestamp
init_logger(LogLevel.WARN)

# Get relay list
relay_str = os.environ["relaylist"]
relaywss_list = ast.literal_eval(relay_str)

# Get event list
async def getevent(id=None, kind=1, pubkey=None, event=None, since=None, author=None, relay=None):
    # Initialize client without signer
    client = Client()

    # Add relays and connect
    if relay:
        await client.add_relay(relay)
    else:
        for relay in relaywss_list:
            await client.add_relay(relay)
            
    await client.connect()

    # Get events from relays
    if id: # Direct search
        f = Filter().id(EventId.parse(id))
    elif pubkey and kind and since: # Mentions
        f = Filter().pubkey(PublicKey.from_hex(pubkey)).kind(Kind(kind)).since(since)
    elif event and kind and not pubkey: # Zaps
        f = Filter().event(EventId.parse(event)).kind(Kind(kind))
    elif kind==0 and author: # Metadata
        f = Filter().kind(Kind(kind)).author(PublicKey.from_hex(author))
    elif kind and not pubkey and not event and not since:
        f = Filter().kind(Kind(kind))

    else:
        raise Exception("Unrecognized request for event retreival")

    source = EventSource.relays(timeout=timedelta(seconds=30))
    events = await client.get_events_of([f], source)
    
    # Convert objects into list of dictionaries
    event_list = []
    for event in events:
        event = event.as_json()
        event = json.loads(event)
        event_list.append(event)

    return event_list

if __name__ == "__main__":
    pass