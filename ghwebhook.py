import BaseHTTPServer
import cgi
import json
import Queue
import threading
import logging
import subprocess

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

FORMAT = '[%(asctime)-15s %(levelname)s %(filename)s %(funcName)s] %(message)s'
handler = logging.FileHandler('log')
handler.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(handler)

def run(handler_class, queue):
    server_address = ('', 8000)
    httpd = BaseHTTPServer.HTTPServer(server_address, handler_class)
    httpd.queue = queue
    httpd.serve_forever()

class Config(object):
    def __init__(self, line):
        elems = line.split(' ', 3)
        self.user = elems[0]
        self.repo = elems[1]
        self.ref = elems[2]
        self.command = elems[3]

class Runner(object):
    def __init__(self, queue):
        self.queue = queue

    def run(self):
        logger.info('start Runner')
        while (True):
            try:
                self._run()
            except Exception, e:
                logger.error('ERROR: {}, {}'.format(e.__class__, e))
            finally:
                self.queue.task_done()

    def _run(self):
        logger.info('start waiting, remain: {}'.format(self.queue.qsize()))
        payload = self.queue.get()
        logger.info('get payload: {}'.format(payload))

        user = payload['repository']['owner']['name']
        repo = payload['repository']['name']
        ref = payload['ref']
        logger.info('user:{}, repo:{}, ref:{}'.format(user, repo, ref))

        logger.info('load config')
        lines = open('config').readlines()
        configs = [Config(line) for line in lines]

        logger.info('find matched line')
        for config in configs:
            if (config.user == user and
                config.repo == repo and
                config.ref == ref):
                logger.info('found config')
                logger.info('run command: {}'.format(config.command))
                try:
                    output = subprocess.check_output(config.command, shell=True, stderr=subprocess.STDOUT)
                    logger.info('run command is success: {}'.format(output))
                except subprocess.CalledProcessError, e:
                    logger.error('run command is failed: {}, {}'.format(e.returncode, e.output))

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200, '')
        self.end_headers()

        length = int(self.headers.getheader('content-length'))
        postvars = cgi.parse_qs(self.rfile.read(length))
        logging.info('%s'.format(postvars))

        payload = json.loads(postvars['payload'][0])

        self.server.queue.put(payload)

if __name__ == '__main__':
    queue = Queue.Queue()
    runner = Runner(queue)
    th = threading.Thread(target=runner.run)
    th.daemon = True
    th.start()
    run(Handler, queue)