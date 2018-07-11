import re
import poplib
import sys
import os
import signal
import queue
import threading
import html
from email import parser
from config import EMAIL_ACCT, EMAIL_PASS, EMAIL_POP3_SERVER
"""
need following from config:
    EMAIL_POP3_SERVER
    EMAIL_ACCT - email account
    EMAIL_PASS - email password
"""

EMAIL_FROM_ADDR = 'notifications@autodesk360.com'
EMAIL_SUBJ = 'Download file'
LINK_RE = (r'<html>.*<a.*href='
           r'"(https:\/\/developer\.api\.autodesk\.com.*\.stp)"'
           r'.*>.*<\/a>.*<\/html>')

emailRe = re.compile('<{}>'.format(EMAIL_FROM_ADDR))
subjectRe = re.compile(EMAIL_SUBJ)
linkRe = re.compile(LINK_RE, flags=re.DOTALL)

# lock for printing progress bar
progress_lock = threading.Lock()


class POPInitialiser(threading.Thread):
    """
    Thread runner for init a POP connection
    """

    # static var: # of connections made
    connections = 0

    def __init__(self, pop_q):
        super().__init__()
        self._pop_q = pop_q

    def run(self):
        try:
            pop = poplib.POP3_SSL(EMAIL_POP3_SERVER)
        except Exception as err:
            print('Error on connecting POP3 server: {}'.format(err),
                  file=sys.stderr)
            return

        # print('Logging in email account')

        pop.user(EMAIL_ACCT)

        try:
            pop.pass_(EMAIL_PASS)
        except Exception as err:
            print('Error on login for email: {}'.format(err),
                  file=sys.stderr)
            return

        # print('Logged in')

        self._pop_q.put(pop)
        POPInitialiser.connections += 1


class EmailAnalyser(threading.Thread):
    """
    Thread runner
    Using an avaiable POP obj from pop_q
    Pop off a email from mail_nums and analyse, append to mail_q if qualify
    """
    parser = parser.BytesParser()
    progress = 0
    nMails = 0

    def __init__(self, pop_q, mail_q, matching_q):
        super().__init__()
        self._mail_q = mail_q
        self._matching_q = matching_q
        self._pop_q = pop_q

    def run(self):
        while True:
            try:
                num = self._mail_q.get_nowait()
            except queue.Empty:
                break

            p = EmailAnalyser.parser

            pop = self._pop_q.get()
            try:
                msg = p.parsebytes(combineLines(pop.top(num, 0)[1]),
                                   headersonly=True)
            except Exception as e:
                print('Exception occurred during communication '
                      'with POP server: ',
                      str(e),
                      file=sys.stderr)
                # exit all threads
                os.kill(os.getpid(), signal.SIGINT)
            finally:
                self._pop_q.put(pop)

            if(email_test(msg)):
                self._matching_q.put(num)

            EmailAnalyser.progress += 1
            printProgress(EmailAnalyser.progress, EmailAnalyser.nMails)

            self._mail_q.task_done()


class DownloadLinkParser(threading.Thread):
    """
    Thread runner for retrieving email body and parse download link
    """
    parser = parser.BytesParser()
    progress = 0
    nMatchings = 0
    nSuccess = 0

    def __init__(self, pop_q, matching_q, download_q):
        super().__init__()
        self._pop_q = pop_q
        self._matching_q = matching_q
        self._download_q = download_q

    def run(self):
        while True:
            try:
                num = self._matching_q.get_nowait()
            except queue.Empty:
                break

            p = DownloadLinkParser.parser

            pop = self._pop_q.get()
            try:
                msg = p.parsebytes(combineLines(pop.retr(num)[1]))
            except Exception as e:
                print('Exception occurred during communication '
                      'with POP server: ',
                      str(e),
                      file=sys.stderr)
                # exit all threads
                os.kill(os.getpid(), signal.SIGINT)

            downlink = parseDownloadLink(msg)
            if downlink:
                self._download_q.put(downlink)
                DownloadLinkParser.nSuccess += 1
                pop.dele(num) # mark delete msg after successfully parsed
                pop.rset() # delete

            self._pop_q.put(pop)

            DownloadLinkParser.progress += 1
            printProgress(DownloadLinkParser.progress,
                          DownloadLinkParser.nMatchings)

            self._matching_q.task_done()


# m should be email.message.Message obj
def email_test(m):
    try:
        return bool(emailRe.findall(m.values()[m.keys().index('From')])) and \
                bool(subjectRe.findall(m.values()[m.keys().index('Subject')]))
    except Exception:
        return False


# parse a list of bytes (lines) to a single string
# def parseStr(bs):
#     return '\n'.join([line.decode('utf-8') for line in bs])

def combineLines(lines):
    return b'\n'.join(lines)


def printProgress(finished, _all):
    ratio = finished/_all
    prefix = '{}/{} |'.format(finished, _all)
    term_width = os.get_terminal_size().columns

    # full len of progress bar
    full = term_width - len(prefix)

    with progress_lock:
        sys.stdout.write('\r')
        sys.stdout.write(prefix + ('#' * int(ratio * full)))
        sys.stdout.flush()


# pass in email.message.Message obj
def parseDownloadLink(msg):
    html_content = msg.get_payload(0).get_payload(1) \
        .get_payload(decode=True).decode('utf-8')
    result = linkRe.findall(html_content)
    return html.unescape(result[0]) if result else False
