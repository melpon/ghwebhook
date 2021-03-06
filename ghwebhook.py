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
    server_address = ('', 20267)
    httpd = BaseHTTPServer.HTTPServer(server_address, handler_class)
    httpd.queue = queue
    httpd.serve_forever()

class Config(object):
    def __init__(self, line):
        elems = line.split(' ', 3)
        self.gituser = elems[0]
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

        gituser = payload['repository']['owner']['login']
        repo = payload['repository']['name']
        ref = payload['ref']
        logger.info('gituser:{}, repo:{}, ref:{}'.format(gituser, repo, ref))

        logger.info('load config')
        lines = open('config').readlines()
        configs = [Config(line) for line in lines]

        logger.info('find matched line')
        for config in configs:
            if (config.gituser == gituser and
                config.repo == repo and
                config.ref == ref):
                logger.info('found config')

                command = 'sudo {command}'.format(command=config.command)
                logger.info('run command: {}'.format(command))
                try:
                    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
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

    def do_GET(self):
        logger.info('GET: {}'.format(self.path))

        try:
            lines = int(self.path.rstrip('/').split('/')[-1])
        except:
            lines = 400

        logger.info('lines: {}'.format(lines))
        if lines > 10000:
            lines = 10000
            logger.info('shrink lines to: {}'.format(lines))

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()

        logger.info('start subprocess tail -n {} log'.format(lines))

        text = subprocess.check_output(['tail', '-n', str(lines), 'log'])

        logger.info('end subprocess')

        self.wfile.write(text)

if __name__ == '__main__':
    queue = Queue.Queue()
    runner = Runner(queue)
    th = threading.Thread(target=runner.run)
    th.daemon = True
    th.start()
    run(Handler, queue)
