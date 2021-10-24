import os
import re
from datetime import datetime
from pathlib import Path
import warnings

import dotenv
import inquirer
import paramiko

from slpp import slpp as lua


def get_ssh(host, user, passphrase=None):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()

    ssh.connect(
        hostname=host,
        username=user,
        password='',
        passphrase=passphrase
    )

    return ssh


def exec_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)

    stdout_read = stdout.read()
    stderr_read = stderr.read()

    if len(stderr_read) > 0:
        raise Exception(stderr_read)

    return stdout_read


def get_sidecar_paths(ssh, start_from):
    sidecar_paths = []

    if type(start_from) == str:
        start_from = [start_from]

    for start in start_from:
        sidecar_stdout = exec_command(
            ssh, 'find "{}" -type d -name "*.sdr"'.format(start)
        )

        sidecar_paths = sidecar_paths + sidecar_stdout.decode().split('\n')
    return sidecar_paths


def get_sidecar_lua_path(ssh, sidecar_path):
    sidecar_lua_stdout = exec_command(
        ssh, 'find "{}" -type f -name "metadata.*.lua"'.format(sidecar_path))
    sidecar_lua_paths = sidecar_lua_stdout.decode().split('\n')
    return sidecar_lua_paths[0]


def get_sidecar_contents(ssh, sidecar_path):
    sidecar_lua_path = get_sidecar_lua_path(ssh, sidecar_path)
    sidecar_contents = get_file_contents(ssh, sidecar_lua_path)
    return sidecar_contents


def get_file_contents(ssh, file_path):
    sftp = ssh.open_sftp()
    with sftp.open(file_path) as file_open:
        file_contents = file_open.read()

    return file_contents


def parse_bookmark(bookmark):
    """Different file formats have different bookmark information. Here I try to
    standardize it into something I would want to have in Obsidian

    :param bookmark:
    :return:
    """
    output = ''

    if 'text' in bookmark:
        text = re.sub(r'^Page \d+ ', '', bookmark.pop('text'), count=1)
        text = text.rsplit(' @ ', 1)[0]
        text = '- {}'.format(text)
    elif 'notes' in bookmark:
        text = '- {}'.format(bookmark.pop('notes'))
    else:
        return None

    output += '\n  - '.join(text.split('\\\n'))
    output += ' <!-- datetime: {} -->\n'.format(bookmark['datetime'])
    return output


def write_markdown(output_path, authors, title, bookmarks):
    output_path.mkdir(parents=True, exist_ok=True)

    # Get start and end dates from the bookmarks
    bookmark_dates = [b['datetime'] for b in bookmarks]
    start = datetime.strptime(
        min(bookmark_dates), '%Y-%m-%d %H:%M:%S'
    ) if len(bookmark_dates) > 0 else None
    end = datetime.strptime(
        max(bookmark_dates), '%Y-%m-%d %H:%M:%S'
    ) if len(bookmark_dates) > 1 else None

    prefix = ''
    if end is not None:
        prefix = end.strftime('%Y%m%d - ')
    elif start is not None:
        prefix = start.strftime('%Y%m%d - ')

    # Get current datetime
    modified = datetime.now().isoformat()

    # Construct the output file path and empty it
    md_file = output_path / '{}{}.md'.format(prefix, title)
    md_file.write_text('')

    # Add frontmatter and headers
    with md_file.open(mode='a') as md:
        md.write('---\n')
        if start is not None:
            md.write('created: {}\n'.format(start.isoformat()))
        md.write(
            'modified: {2}\n'
            'tags:\n'
            '  - boek\n'
            '  - {0}\n\n'
            '---\n\n'
            '# {0}\n\n'
            '- Van [[{1}]]\n'.format(
                title,
                authors,
                modified
            ))

        if start is not None:
            md.write('- Eerste highlight gezet op {}\n'
                     ''.format(start.strftime('[[DAGBOEK/%Y/%Y-%m/%Y-%m-%d]]')))
        if end is not None:
            md.write('- Laatste highlight gezet op {}'
                     '\n'.format(end.strftime('[[DAGBOEK/%Y/%Y-%m/%Y-%m-%d]]')))

        md.write('\n## Highlights\n')

        # Write the actual bookmarks, per chapter
        current_chapter = None
        for bookmark in bookmarks:
            bookmark_chapter = bookmark.pop('chapter')

            if bookmark_chapter != current_chapter:
                current_chapter = bookmark_chapter
                md.write('\n### {}\n\n'.format(current_chapter))

            md.write(parse_bookmark(bookmark))


def sort_bookmarks(bookmarks_dict):
    def sort_key(item):
        if type(item['page']) == int:
            return [item['page']]

        return [int(i) for i in re.findall(r'\[(\d+)\]', item['page'])]

    bookmarks_list = [b for b in bookmarks_dict.values()]
    bookmarks_list = sorted(bookmarks_list, key=sort_key)
    return bookmarks_list


def ask_passphrase():
    passphrase = inquirer.password(
            'name',
            message="What's your name?"
            ),


def main():
    try:
        ssh = get_ssh(
            os.environ['SSH_HOST'],
            os.environ['SSH_USER']
        )
    except paramiko.ssh_exception.PasswordRequiredException as e:
        warnings.warn(e.args[0])
        passphrase = inquirer.password("Enter your private key's passphrase:")
        ssh = get_ssh(
            os.environ['SSH_HOST'],
            os.environ['SSH_USER'],
            passphrase
        )

    sidecar_paths = get_sidecar_paths(ssh, [
        '/mnt/onboard/.adds/koreader/articles/',
        '/mnt/onboard/.adds/koreader/books/',
        '/mnt/onboard/.adds/koreader/comics/'
    ])

    for sidecar_path in sidecar_paths:
        if len(sidecar_path) == 0:
            continue

        print(sidecar_path)

        sidecar_contents = get_sidecar_contents(ssh, sidecar_path).decode()

        # Clean that sidecar str, then decode into a dict
        sidecar_contents = re.sub('^[^{]*', '', sidecar_contents).strip()
        sidecar_lua = lua.decode(sidecar_contents)

        # Get book authors, title and dates
        authors = sidecar_lua['doc_props']['authors']
        title = sidecar_lua['doc_props']['title']

        # Sort bookmarks based on `page`
        sorted_bookmarks = sort_bookmarks(sidecar_lua['bookmarks'])

        # Write the bookmarks to the `output` folder
        write_markdown(
            Path('output').resolve(),
            authors,
            title,
            sorted_bookmarks
        )


if __name__ == '__main__':
    dotenv.load_dotenv()
    main()
