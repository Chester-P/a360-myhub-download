#!/usr/bin/env python
import queue
from utils import POPInitialiser, EmailAnalyser, DownloadLinkParser
from config import EMAIL_POP3_SERVER

OUTPUT_FILE = 'download-list.txt'
MAX_CONNECTION = 15
MAX_THREADS = 20


assert(MAX_CONNECTION > 0)
print('Initiating {} connections to POP3 server: {}'
      .format(MAX_CONNECTION, EMAIL_POP3_SERVER))
pop_q = queue.Queue()
tasks = []
for i in range(MAX_CONNECTION):
    t = POPInitialiser(pop_q)
    tasks.append(t)
    t.start()

for t in tasks:
    t.join()

print('{}/{} connections established'.
      format(POPInitialiser.connections, MAX_CONNECTION))

assert(POPInitialiser.connections > 0)

print('Retriving all emails from *inbox*')
pop = pop_q.get()
pop_q.put(pop)
mail_nums = pop.list()[1]
nMails = len(mail_nums)
# convert bytes to num and parse only the mail number
mail_nums = map(lambda b: b.decode('utf-8').split(' ')[0], mail_nums)
mail_q = queue.Queue()
for num in mail_nums:
    mail_q.put(num)

matching_q = queue.Queue()
print('Analysing {} email headers matching for criteria...'
      .format(nMails))

threads = []
EmailAnalyser.nMails = nMails

for i in range(MAX_THREADS):
    t = EmailAnalyser(pop_q, mail_q, matching_q)
    threads.append(t)
    t.start()

# wait for mail_q to finish
mail_q.join()

print()
nMatchings = matching_q.qsize()
DownloadLinkParser.nMatchings = nMatchings
print('Found {} emails for download links'.format(nMatchings))

download_q = queue.Queue()
threads = []
nSuccess = 0
print('Retrieving download link from emails...')
for i in range(MAX_THREADS):
    t = DownloadLinkParser(pop_q, matching_q, download_q)
    threads.append(t)
    t.start()

matching_q.join()

print()
print('Successfully retrieved {}/{} download links'
      .format(DownloadLinkParser.nSuccess, nMatchings))

fp = open(OUTPUT_FILE, 'w')
while not download_q.empty():
    fp.write(download_q.get())
    fp.write('\n')
fp.flush()
fp.close()
print('Successfully write all download links into', OUTPUT_FILE)


while not pop_q.empty():
    pop = pop_q.get()
    pop.close()
