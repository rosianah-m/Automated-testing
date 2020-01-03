import logging, json, os, Levenshtein, difflib, re, traceback
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

from telethon.sync import TelegramClient, events 
import time
from tkinter import Button, filedialog,Label,Frame, StringVar, Tk, IntVar, Radiobutton
import asyncio

#Bot test window(front end)
class BotTest(Frame):
    def __init__(self,tk): #tk is tkinter its a GUI package
        Frame.__init__(self,tk)
        tk.geometry('650x600') #window size

        tk.title("Welcome to Caawiye Tests App")#Intrface/window title

        self.conversations = {}
        self.test_counter, self.question_counter = 0,0
        self.conversationReset = True

        self.statusupdate = StringVar() #stringVar has been imported from tkinter
        self.statusupdate.set('Awaiting test  file to be loaded') #current status of the test app (at the bottom)

        #labels 
        lbl = Label(tk, text="Please select Bot instance to test", font=("Arial Bold", 15))

        #pack geometry manager
        lbl.pack(side="top", fill='both', expand=True, padx=1, pady=1)

        #select file button has a selectfile() function call
        self.fileSelector = Button(self,text='Select test file',command=lambda : self.selectfile(), font=("Arial Bold", 12))
        self.fileSelector.pack(side="top", fill='both', expand=True, padx=4, pady=4)

        #value holdr for integer values values and set the variable to a value 1 
        self.v = IntVar()
        self.v.set(1)

        #pack() anchors define where text is positioned
        Label(self, text="Do you want to validate bot responses?").pack(anchor='w',side="top", fill='both', expand=True, padx=4, pady=4)
        
        Radiobutton(self, text="Yes", variable=self.v, value=1).pack(anchor='w')
        Radiobutton(self, text="No", variable=self.v, value=0).pack(anchor='w')

        #function call to load the bots file
        self.loadBots("bots.json")

        #position of teh status update and text
        self.status = Label(tk,textvariable=self.statusupdate, bd=1, relief='sunken', anchor='w')

        self.status.pack(side='bottom', fill='x')

    #quit button
    def quit(self):
        global root
        root.quit()

    def cancel(self,client):
        client.disconnect

    #sending a reset message function
    #converstation reset becomes false after a reset message has been send
    def reset_conversation(self,client,bot):
        text = 'Reset'
        client.send_message(bot, text) #bot id then message
        self.conversationReset = False

    #selecting a file using explorer 
    def selectfile(self):
        #tkinter module to ask a file to open. Filedialog class and askopenfilename function
        file = filedialog.askopenfilename(title='Choose a test file')
        try:
            if file != None: 
                self.conversations = self.load_json(file) #call load_json()
                 #count the number of converstations, size of the array tests
                self.conversationLabel = Label(self, text=str(len(self.conversations['tests'])) + " test found in file " + os.path.basename(file), font=("Arial", 12))
                self.conversationLabel.pack(side="top", fill='both', expand=True, padx=4, pady=4) #the geometry
        #if out of the norm occurs
        except Exception as e:
            print(e)
            self.conversationLabel = Label(self, text="You have chosen an invalid json file")
            self.conversationLabel.pack(side="top", fill='both', expand=True, padx=4, pady=4)

    #show the output at teh bottom while the bot test is running
    def show_output(self,text_output):
        self.statusupdate.set(text_output)
        # print(text_output)
        self.update_idletasks()

    #send message to the bot
    async def send_to_bot(self,client,bot,text,type):
        if type == 'message':#***
            # Send message to bot
            client.send_message(bot, text)

    def reset_tests(self):
        self.question_counter = 0
        self.test_counter = 0
        self.conversationReset = True

    #loading bots and having a button for each bot
    def loadBots(self,file):
        bots = self.load_json(file)

        #Display the bots
        for bot in bots:
            button = Button(self, text=bot, width=20, font=("Lucinda Sans", 12),command= lambda name = bot, id = bots[bot]: self.run_test(name,id))
            button.pack(side="top", expand=False, padx=(10, 10), pady=(10, 10))

    #saving the file
    def save_result(self,results,result,status,message):
        result['status'] = status
        result['message'] = message
        results['results'].append(result)
        resultlog = 'results ' + time.strftime("%d-%m-%Y %H - %M", time.localtime(self.start))+'.json'
        if os.path.exists(resultlog):
            res = open(resultlog,'w')#open file for writing
        else:
            res = open(resultlog,'w+')#open file for writing and reading

        json.dump(results, res, indent=4)
        res.close
#?????????
    def string_compare(self,first,second):
        ratio = difflib.SequenceMatcher(None,first, second).ratio()
        isFirstInSecond = second.find(first)
        result = ratio < 0.75 and isFirstInSecond < 0
        # print("First: " + first + " Second: "+ second)
        # print("ratio: " + "{0:0.2f}".format(ratio) + " isFirstInSecond: "+ str(second.find(first)))
        # print(result)
        return result

    #load the json files in the explorer
    def load_json(self,file):
        json_file = open(file, "rb")
        return json.load(json_file)

    #Reading conversations and matching the ids with the expected output, validate responses
    def load_expected_text(self,expectedResponses):
        response = ""
        filtered = {}

        json = self.load_json(expectedResponses['file']) #load the file in the conversations eg intents.json
        match = [i for i in json if i["id"] == expectedResponses['id']][-1] #if id in json matches with the id in the expected conversation
        
        #where there are filters
        if "filters" in expectedResponses:
            key = expectedResponses["filters"]["property"]
            match = match[key] #match with the key using the id
            
            for item in match: #for item in match, 
                for i in list(expectedResponses["filters"])[1:]:
                    if item[i] == expectedResponses["filters"][i]: #if items in the filters match with the expected response
                        filtered = item 
        else:
            filtered = match
        
        keys = expectedResponses["property"].split(".") #split where there's . eg prompts.promptWithHints

    #    Will find a better way to filter this part and make it dynamic ?????????????????????????????
        if len(keys) > 1:
            filtered = filtered[keys[0]]
            if isinstance(filtered,dict):
                filtered = filtered[keys[1]]

        key_results = self.findkeys(filtered, keys[-1]) #call the findkeys func
        return self.remove_placeholders(list(key_results))

    def remove_placeholders(self, items):
        formated_string = []
        for i in items:
            if isinstance(i,list):
                [formated_string.append(re.sub("\$\w+", '', j)) for j in i] 
            else:
                formated_string.append(re.sub("\$\w+", '', i))
        return formated_string
    
    def findkeys(self,node, kv):
        if isinstance(node, list):
            for i in node:
                for x in self.findkeys(i, kv):
                    yield x
        elif isinstance(node, dict):
            if kv in node:
                yield node[kv]
            for j in node.values():
                for x in self.findkeys(j, kv):
                    yield x

    #running test, provide api id and hash
    def run_test(self,name,bot_id):
        self.start = time.time()
        api_id = 1051818
        api_hash = 'c12711744c64b21019251856f1bd4acd'

        #using the telegram api to send message to the bot
        with TelegramClient('me', api_id, api_hash) as client:

            results = {'results':[], 'start': time.asctime(time.localtime(self.start)), 'conversations': len(self.conversations['tests'])}

            self.cancel_button = Button(self, text='Cancel', width=20, font=("Lucinda Sans", 12),command=self.cancel(client)) #cancel function called

            statusintro = 'Bot Instance ' + name +': '
            testtitle = ""
            
            #call the show-output function
            self.show_output(statusintro + testtitle)

            #if conversation has ben reset, send message. Else, send a reset message
            if self.conversationReset is False:
                client.send_message(bot_id, self.conversations['tests'][self.test_counter]['questions'][self.question_counter])
            else:
                client.send_message(bot_id, 'Reset')
                self.conversationReset = False

            #different events
            @client.on(events.NewMessage)
            async def my_event_handler(event):
                try:
                    done = False
                    testPassed = True
                    expectedResponses = []
                    
                    #if conversationReset is true, wait as you send  message then set conversationReset to False
                    if self.conversationReset:
                        await client.send_message(bot_id, 'Reset')
                        self.conversationReset = False
                    else:
                        result = {}
                        testtitle = 'Test '+ self.conversations['tests'][self.test_counter]['title'] + ': '
                        #name of each test. Title from the conversations file
                        title = str(self.test_counter+1) + '. ' + self.conversations['tests'][self.test_counter]['title']
                        #questions from te converstaion file
                        question = self.conversations['tests'][self.test_counter]['questions'][self.question_counter]
                        #if below text is > 0, load expected response and start the counter
                        if event.raw_text.find('you can now start afresh') < 0:
                            expectedResponses = self.conversations['tests'][self.test_counter]['expectedResponses'][self.question_counter]

                        #will show the current bot's response at the bottom
                        self.show_output(statusintro + testtitle + ' Post from bot: ' + event.raw_text)
                        result['name'] = title
                        test_message = ''
                        test_status = ''
                        if event.sender_id == bot_id:
                            #if the bot has crashed
                            if event.raw_text.find('experiencing difficulty') >= 0:                                
                                test_message = 'Bot crashed at ' + question + '('+ str(self.question_counter) +')' 
                                test_status = 'Failed'
                                done = True
                                #show the status at the bottom of the interface
                                self.show_output(statusintro + testtitle)
                            elif event.raw_text.find('404') >= 0:
                                #bot has crashed
                                test_message  = 'Bot unreacheable, crashed at ' + question + '('+ str(self.question_counter) +')' 
                                test_status = 'Failed'
                                done = True
                                self.show_output(statusintro + testtitle)
                            elif event.raw_text.find('403') >= 0:
                                #bot has crashed
                                test_message = 'Bot\'s endpoint failed with HTTP status 403, crashed at ' + question + '('+ str(self.question_counter) +')' 
                                test_status = 'Failed'
                                done = True
                                self.show_output(statusintro + testtitle)
                            elif event.raw_text.find('502') >= 0:
                                #bot has crashed
                                test_message = 'Bot connection strings wrong, Bot crashed at ' + question + '('+ str(self.question_counter) +')' 
                                test_status = 'Failed'
                                done = True
                                self.show_output(statusintro + testtitle)
                            elif event.raw_text.find('500') >= 0:
                                #bot has crashed
                                test_message = 'Bot code has a problem, Bot crashed at ' + question + '('+ str(self.question_counter) +')'
                                test_status = 'Failed' 
                                done = True
                                self.show_output(statusintro + testtitle)
                            else:
                                if event.raw_text.find('timed out') < 0 and event.raw_text.find('endpoint failed') and event.raw_text.find('.jpg') < 0 and event.raw_text.find('.png') < 0:
                                    # print("To bot: " + question)
                                    # print("From bot: " + event.raw_text)
                                    # print("Expected: " + ', '.join(expectedResponses))
                                    # print("Ratio: " + str(difflib.SequenceMatcher(None,event.raw_text, expectedResponses).ratio()))
                                    # print("Contains: " + str(event.raw_text.find(expectedResponses)))
                                    # print("Question Counter: " + str(self.question_counter))
                                    # print("Test Counter: " + str(self.test_counter))
                                    

                                    #v represents the integer values asigned to the radio buttons 
                                    if self.v.get() == 1 and event.raw_text.find('you can now start afresh') < 0: 
                                        responses = self.load_expected_text(expectedResponses)
                                        if isinstance(responses, list): #return true if the responses is a list
                                            hasTrue = False
                                            for expectedResponse in  responses:
                                                comparisson =  self.string_compare(expectedResponse,re.sub('<.*>', '', event.raw_text))
                                                if comparisson == False:
                                                    hasTrue = True
                                            if hasTrue == False:
                                                testPassed = False
                                    
                                   #tests status                                    
                                    if testPassed:
                                        #increase the question counter
                                        if self.question_counter < len(self.conversations['tests'][self.test_counter]['questions'] ) - 1:
                                            if event.raw_text.find('you can now start afresh') < 0:
                                                self.question_counter += 1
                                        #increase test counter and print status & message if test is passed
                                        else:
                                            self.question_counter = 0
                                            test_status = 'Test Passed'
                                            test_message = 'Test Result: ' + 'Passed'
                                            result['input'] = question
                                            result['status'] = test_status
                                            if self.test_counter < len(self.conversations['tests']) - 1:
                                                self.test_counter += 1
                                                self.conversationReset = True
                                                self.save_result(results,result,test_status,test_message)
                                            #if tests are are over (ie test counter > len(self.conversations['tests])), show the final test result
                                            else:
                                                results['Final Test Result']  = 'Test Passed'
                                                self.test_counter = 0
                                                done = True
                                    #if a test fails, show 
                                    else:
                                        test_message = 'Test Failed at : ' + str(self.question_counter)
                                        self.question_counter = 0
                                        test_status = 'Failed'
                                        result['input'] = question
                                        result['status'] = test_status
                                       
                                        result['expected response'] = responses
                                        result['bot response'] = event.raw_text
                                        
                                        result['message'] = test_message
                                        #if tests are not done, increase the test counter and save the results
                                        if self.test_counter < len(self.conversations['tests']) - 1:
                                            self.test_counter += 1
                                            self.conversationReset = True
                                            self.save_result(results,result,test_status,test_message)
                                        else: #doesn't make sense
                                            results['Final Test Result']  = 'Test Failed'
                                            self.test_counter = 0
                                            done = True

                            #to display after running tests
                            #if done is true, ie tests are done
                            if done:
                                results["results"].append(result)
                                end = time.time()
                                results["end"] = time.asctime(time.localtime(end))
                                results["duration"] = (end-self.start)/100
                                successful = 0
                                unsuccessful = 0

                                #check the unsuccessful tests and increase them in the counter
                                for item in results["results"]:
                                    if item['status'] == 'Failed':
                                        unsuccessful += 1
                                    #count the successful tests and increase them in the counter
                                    else:
                                        successful += 1

                                results["successful"] = successful
                                results["unsuccessful"] = unsuccessful
                                #the final result is a fail if there was any unsuccessful test
                                final_status = "Failed" if unsuccessful > 0 else "Passed"
                                self.save_result(results,{},final_status,test_message)
                                # self.cancel_button.destroy()
                                await client.disconnect()
                            else:
                                #if there's a timeout, endpoint fail etc...wait for reply and show output
                                if self.conversationReset is False:
                                    if event.raw_text.find('is likely') < 0 and event.raw_text.find('timed out') < 0 and event.raw_text.find('endpoint failed') and event.raw_text.find('.jpg') < 0 and event.raw_text.find('.png') < 0:
                                        question = self.conversations['tests'][self.test_counter]['questions'][self.question_counter]
                                        if question: 
                                            await event.reply(question)
                                            self.show_output(statusintro + testtitle + ' Post to bot: ' + question)
                                else:
                                    if event.raw_text.find('is likely') < 0:
                                        await client.send_message(bot_id, 'Reset')
                                        self.conversationReset = False
                except Exception as e:
                    tb = traceback.format_exc()
                    print(e)
                    self.reset_tests()
                    
                    await client.disconnect()
                else:
                    tb = "No error"
                finally:
                    print(tb)
                    
            client.start()
            client.run_until_disconnected()
            
root = Tk()
frame = BotTest(root).pack()
Button(root, text="Quit", command=quit).pack()
root.mainloop()

