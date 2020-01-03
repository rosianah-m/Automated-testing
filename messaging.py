import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

from telethon.sync import TelegramClient, events
import json

# Remember to use your own values from my.telegram.org!
api_id = 947831
api_hash = '014e2a6be41b14ad66dfb357b160cb9e'
test_counter, question_counter = 0,0

with TelegramClient('anon', api_id, api_hash) as client:
    
    f = open("conversations.json", "r")
    conversations = json.load(f)

    #print(conversations["tests"])
    
    # for conversation in conversations["tests"]:
    #     print('Running test ' + conversation["title"])
    
    print('Running test ' + conversations['tests'][test_counter]['title'])

    # You can send messages to yourself...
    client.send_message(828984156, conversations['tests'][test_counter]['questions'][question_counter])

    @client.on(events.NewMessage)
    async def my_event_handler(event):
        try:
            global question_counter, test_counter, client
            done = False

            print('Post to bot: ', conversations['tests'][test_counter]['questions'][question_counter])
            print('Response from Bot: ',event.raw_text)
            if question_counter < len(conversations['tests'][test_counter]['questions'] ) - 1:
                question_counter += 1
            else:
                question_counter = 0
                if test_counter < len(conversations['tests']) - 1:
                    test_counter += 1
                else:
                    print('Tests complete')
                    test_counter = 0
                    done = True
           
            if done:
                await client.disconnect()
            else:
                await event.reply(conversations['tests'][test_counter]['questions'][question_counter])

        except:
            print("An error has occured")

    client.start()
    client.run_until_disconnected()

