import getpass
import os
import paramiko
import scp
import sys
import time


CURRENT_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))
GENERATED_HTML_PATH = os.path.join(CURRENT_PATH, 'html', 'generated')
GENERATED_RULEBOOK_PATH = os.path.join(GENERATED_HTML_PATH, 'PaintedLands.html')
GENERATED_STYLE_PATH = os.path.join(GENERATED_HTML_PATH, 'style.css')

LOCAL_STYLE_SHEET = 'style.css'
REMOTE_STYLE_SHEET = "{{ url_for('static', filename='painted_lands/style.css') }}"

INSTANCE_HOSTNAME = '3.222.117.14'
INSTANCE_USER = 'ubuntu'
KEY_FILE = 'server.pem'
TIMEOUT_SEC = 60
LAST_TIME = time.time()


def _find_ssh_key_path():
    paths_to_try = [
        os.path.join('C:', 'Users', getpass.getuser(), '.ssh', KEY_FILE),
        os.path.join(CURRENT_PATH, KEY_FILE),
    ]

    for path in paths_to_try:
        if os.path.exists(path):
            return path

    raise FileNotFoundError('Could not find SSH key. Place the "%s" file in the same directory as this file or '
                            'in a ".ssh" folder under your username' % KEY_FILE)


def _swap(file_path, text_to_replace, replacement_text):
    with open(file_path, 'r', encoding='utf8') as f:
        html = f.read()

    html = html.replace(text_to_replace, replacement_text)

    with open(file_path, 'w+', encoding='utf8') as f:
        f.write(html)


def _upload(scp_client, local_path, remote_path, file_name, log):
    global LAST_TIME
    LAST_TIME = time.time()

    log('Uploading %s' % file_name)
    scp_client.put(local_path, remote_path=remote_path)


def deploy(log):
    global LAST_TIME

    def progress(filename, size, sent):
        global LAST_TIME
        if time.time() > LAST_TIME + 1:
            log('%s progress: %.2f%%' % (filename.decode('utf-8'), 100 * float(sent) / float(size)))
            LAST_TIME = time.time()

    ssh_key_path = _find_ssh_key_path()

    # Swap out the style sheet inclusion with one that flask will understand
    _swap(GENERATED_RULEBOOK_PATH, LOCAL_STYLE_SHEET, REMOTE_STYLE_SHEET)

    ssh_client = None
    scp_client = None
    try:
        log('Establishing connection')
        ssh_key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=INSTANCE_HOSTNAME, username=INSTANCE_USER, pkey=ssh_key, timeout=TIMEOUT_SEC)

        scp_client = scp.SCPClient(ssh_client.get_transport(), socket_timeout=TIMEOUT_SEC, progress=progress)
        _upload(scp_client, GENERATED_RULEBOOK_PATH, '/home/ubuntu/kouhai/templates/painted_lands/PaintedLands.html',
                'PaintedLands rulebook', log)
        _upload(scp_client, GENERATED_STYLE_PATH, '/home/ubuntu/kouhai/static/painted_lands/style.css',
                'PaintedLands style sheets', log)

        log('Restarting server')
        ssh_client.exec_command('pm2 restart kouhai')

    except Exception:
        raise Exception('Failed uploading files, likely a network error. Regenerate files before re-uploading.')
    else:
        log('Updated website')
    finally:
        # Revert style file
        _swap(GENERATED_RULEBOOK_PATH, REMOTE_STYLE_SHEET, LOCAL_STYLE_SHEET)

        if scp_client:
            scp_client.close()
        if ssh_client:
            ssh_client.close()
