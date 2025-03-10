# Log setup
import logging
logging.basicConfig(level=logging.INFO)

# Internal programs
# from nostr.publish import nostrpost
from nostr.getevent import getevent
from lsbSteganography import decode_text_from_url, extract_image_url
from emojiDecoder import detect_and_decode_emoji_steganography

# Outside programs
import asyncio, os, json, ast, re
from nostr_sdk import Client, PublicKey, NostrSigner, Keys, Event, UnsignedEvent, Filter, \
    HandleNotification, Timestamp, nip04_decrypt, ClientMessage, EventBuilder, UnwrappedGift, \
    init_logger, LogLevel, Kind, Tag, nip04_encrypt

# Set Contact and Private Key
lemon = "npub1hee433872q2gen90cqh2ypwcq9z7y5ugn23etrd2l2rrwpruss8qwmrsv6"
# lemonhex = PublicKey.from_bech32(lemon).to_hex()
lemonhex = PublicKey.parse(lemon).to_hex()
botpubkey = "npub13p25qtngtldjyk5p7y457h3hxyq54lwennvkku42zg24h5gfjqvsgmpwxc"
# botpubhex = PublicKey.from_bech32(botpubkey).to_hex()
botpubhex = PublicKey.parse(botpubkey).to_hex()
private_key = os.environ["stegonostrkey"]

# Initialize lists
target_event = None

# Get relay list
relay_str = os.environ["relaylist"]
relaywss_list = ast.literal_eval(relay_str)

help_terms = ["help", "command", "commands"]
help_message = f'''
I'm Steg the image decoding stegosaurus
Tag me in the reply to the image you want decoded\n\n
                    
Send any feeedback you have to nostr:{lemon}
'''

async def main():
    init_logger(LogLevel.DEBUG)

    keys = Keys.parse(private_key)

    sk = keys.secret_key()
    pk = keys.public_key()

    signer = NostrSigner.keys(keys)
    client = Client(signer)

    for relay in relaywss_list:
        await client.add_relay(relay)
    await client.connect()

    now = Timestamp.now()

    # nip04_filter = Filter().pubkey(pk).kind(Kind.from_enum(KindEnum.ENCRYPTED_DIRECT_MESSAGE())).since(now)
    # mentions = Filter().pubkey(pk).kind(Kind.from_enum(KindEnum.TEXT_NOTE())).since(now)
    # nip59_filter = Filter().pubkey(pk).kind(Kind.from_enum(KindEnum.GIFT_WRAP())).limit(0)
    nip04_filter = Filter().pubkey(pk).kind(Kind(4)).since(now)
    mentions = Filter().pubkey(pk).kind(Kind(1)).since(now)
    nip59_filter = Filter().pubkey(pk).kind(Kind(14)).limit(0)
    # await client.subscribe([nip04_filter, nip59_filter, mentions], None)
    await client.subscribe(mentions, None)

    class NotificationHandler(HandleNotification):
        async def handle(self, relay_url, subscription_id, event: Event):
            logging.info(f"Received new event from {relay_url}: {event.as_json()}")
            # if event.kind().as_enum() == KindEnum.ENCRYPTED_DIRECT_MESSAGE():
            if event.kind().as_u16() == 4: #Encrypted direct message
                logging.info("Decrypting NIP04 event")
                try:
                    msg = nip04_decrypt(sk, event.author(), event.content())
                    # await client.send_private_msg(receiver=event.author(), message=help_message, reply_to=None)
                    # secret = await make_private_msg(keys, event.author(), help_message)
                    # await client.send_event(secret)
                    # await client.send_direct_msg(event.author(), help_message, None)
                    encrypted_content = nip04_encrypt(sk, event.author(), help_message)
                    builder = EventBuilder(Kind(4), encrypted_content).tag(Tag.public_key(event.author()))
                    await client.send_event_builder(builder)
                    logging.info(f"Received new msg: {msg}")
                except Exception as e:
                    logging.info(f"Error during content NIP04 decryption: {e}")
            # elif event.kind().as_enum() == KindEnum.GIFT_WRAP():
            elif event.kind().as_u16() == 1059: #Gift-wrapped event
                logging.info("Decrypting NIP59 event")
                try:
                    # Extract rumor
                    unwrapped_gift = UnwrappedGift.from_gift_wrap(keys, event)
                    sender = unwrapped_gift.sender()
                    rumor: UnsignedEvent = unwrapped_gift.rumor()

                    # Check timestamp of rumor
                    if rumor.created_at().as_secs() >= now.as_secs():
                        # if rumor.kind().as_enum() == KindEnum.PRIVATE_DIRECT_MESSAGE():
                        if rumor.kind().as_u16() == 14: #Private message
                            msg = rumor.content()
                            logging.info(f"Received new msg [sealed]: {msg}")
                            await client.send_private_msg(sender, help_message, None)
                        else:
                            logging.info(f"{rumor.as_json()}")
                except Exception as e:
                    logging.info(f"Error during content NIP59 decryption: {e}")
            # elif event.kind().as_enum() == KindEnum.TEXT_NOTE():
            elif event.kind().as_u16() == 1: #Text Note
                logging.info('Mention notification!')

                # Process each unique event
                receiver = event.author()
                reply = event.id()
                event = json.loads(event.as_json())
                logging.info("Event Initial:")
                logging.info(event)
                eventID = event['id']
                eventContent = event['content'] # NOTE: Should have image url
                author = event['pubkey']

                # Self reference loop
                if author == botpubhex:
                    logging.info('Self referenced event')
                    return "Self referenced event"
                
                # New Event!
                try:
                    logging.info('New event!')
                    # Extract target event ID                 
                    # target_eventID = next((tag[1] for tag in event['tags'] if tag[0] == 'e'), None)
                    # Initialize variables
                    target_eventID = None
                    relay_hint = None

                    # First try to find an 'e' tag with "reply"
                    for tag in event['tags']:
                        if tag[0] == 'e' and len(tag) >= 4 and tag[3] == 'reply':
                            target_eventID = tag[1]
                            relay_hint = tag[2] if len(tag) >= 3 else None
                            break

                    # If no reply tag was found, fall back to the first 'e' tag
                    if target_eventID is None:
                        for tag in event['tags']:
                            if tag[0] == 'e':
                                target_eventID = tag[1]
                                relay_hint = tag[2] if len(tag) >= 3 else None
                                break

                    # Get target event
                    try:
                        target_event = await getevent(id=target_eventID, relay=relay_hint)
                        target_event = target_event[0]
                        logging.info("Target Content:")
                        logging.info(str(target_event))
                        logging.info(type(target_event))
                    except:
                        logging.info(f"Event Detection Issue: {target_eventID}")
                        message = 'Uh-oh! Unable to find event in relay list'
                        # await nostrpost(private_key=private_key, content=message, reply_to=eventID)
                        # await client.send_private_msg(receiver=receiver, message=message, reply_to=None)
                        # secret = await make_private_msg(keys, event.author(), message)
                        # await client.send_event(secret)
                        # await client.send_direct_msg(receiver, message, reply)
                        encrypted_content = nip04_encrypt(sk, receiver, message)
                        builder = EventBuilder(Kind(4), encrypted_content).tags([Tag.public_key(receiver)])
                        await client.send_event_builder(builder)

                        return "Consider adding new relays"

                    # Search for target language and source language
                    logging.info("Event Content:")
                    logging.info(str(target_event['content']))
                    encoded_url = extract_image_url(str(target_event['content']))

                    if encoded_url:
                        logging.info("Extracted Encoded URL:")
                        logging.info(encoded_url)
                        decoded_text = decode_text_from_url(encoded_url)
                        logging.info("Decoded Text:")
                        logging.info(decoded_text)
                        if decoded_text:
                            # await nostrpost(private_key=private_key, content=decoded_text, reply_to=eventID)
                            # await client.send_private_msg(receiver=receiver, message=decoded_text, reply_to=None)
                            # secret = await make_private_msg(keys, event.author(), decoded_text)
                            # await client.send_event(secret)
                            # await client.send_direct_msg(receiver, decoded_text, reply)
                            encrypted_content = nip04_encrypt(sk, receiver, decoded_text)
                            builder = EventBuilder(Kind(4), encrypted_content).tags([Tag.public_key(receiver)])
                            await client.send_event_builder(builder)
                            return "Successful Decoding!"
                        else:
                            logging.info(f"No secret message detected: {target_eventID}")
                            message = 'No secret message detected'
                            # await nostrpost(private_key=message, content=message, reply_to=eventID)
                            # await client.send_private_msg(receiver=receiver, message=message, reply_to=None)
                            # secret = await make_private_msg(keys, event.author(), message)
                            # await client.send_event(secret)
                            # await client.send_direct_msg(receiver, message, reply)
                            encrypted_content = nip04_encrypt(sk, receiver, message)
                            builder = EventBuilder(Kind(4), encrypted_content).tags([Tag.public_key(receiver)])
                            await client.send_event_builder(builder)
                            return "Unsuccessful Decoding"
                    else:
                        has_hidden, decoded_text = detect_and_decode_emoji_steganography(str(target_event['content']))
                        if has_hidden:
                            logging.info(decoded_text)
                            encrypted_content = nip04_encrypt(sk, receiver, decoded_text)
                            builder = EventBuilder(Kind(4), encrypted_content).tags([Tag.public_key(receiver)])
                            await client.send_event_builder(builder)
                            return "Successful Decoding!"
                        else:
                            logging.info(f"No secret message detected: {target_eventID}")
                            message = 'No secret message detected'
                            # await nostrpost(private_key=message, content=message, reply_to=eventID)
                            # await client.send_private_msg(receiver=receiver, message=message, reply_to=None)
                            # secret = await make_private_msg(keys, event.author(), message)
                            # await client.send_event(secret)
                            # await client.send_direct_msg(receiver, message, reply)
                            encrypted_content = nip04_encrypt(sk, receiver, message)
                            builder = EventBuilder(Kind(4), encrypted_content).tags([Tag.public_key(receiver)])
                            await client.send_event_builder(builder)
                            return "Unsuccessful Decoding"
                except Exception as e:
                    logging.error(f"An error occurred: {str(e)}")
                    message = 'Uh-oh! Something broke while trying to decode image'
                    # await nostrpost(private_key=private_key, content=message, reply_to=eventID)
                    # await client.send_private_msg(receiver=receiver, message=message, reply_to=None)
                    # secret = await make_private_msg(keys, event.author(), message)
                    # await client.send_event(secret)
                    # await client.send_direct_msg(receiver, message, reply)
                    encrypted_content = nip04_encrypt(sk, receiver, message)
                    builder = EventBuilder(Kind(4), encrypted_content).tags([Tag.public_key(receiver)])
                    await client.send_event_builder(builder)
                    return f"Something broke when a New Event path was triggered."

        async def handle_msg(self, relay_url, msg):
            None

    await client.handle_notifications(NotificationHandler())

    # To handle notifications and continue with code execution, use:
    asyncio.create_task(client.handle_notifications(NotificationHandler()))

    # Keep up the script (if using the create_task)
    while True:
      await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())