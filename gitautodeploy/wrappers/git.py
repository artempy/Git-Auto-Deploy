# -*- coding: utf-8 -*-
import os

from gitautodeploy.wrappers.notify_smtp import send_notify_mail


class GitWrapper():
    """Wraps the git client. Currently uses git through shell command
    invocations."""

    def __init__(self):
        pass

    @staticmethod
    def init(repo_config):
        """Init remote url of the repo from the git server"""
        import logging
        from .process import ProcessWrapper
        import os
        import platform

        logger = logging.getLogger()
        logger.info("Initializing repository %s" % repo_config['path'])

        commands = []

        # On Windows, bash command needs to be run using bash.exe. This assumes bash.exe
        # (typically installed under C:\Program Files\Git\bin) is in the system PATH.
        if platform.system().lower() == "windows":
            commands.append('bash -c "cd \\"' + repo_config['path'] + '\\" && unset GIT_DIR"')
        else:
            commands.append('unset GIT_DIR')

        commands.append('git remote set-url ' + repo_config['remote'] + " " + repo_config['url'])
        commands.append('git fetch ' + repo_config['remote'])
        commands.append('git checkout -f -B ' + repo_config['branch'] + ' -t ' + repo_config['remote'] + '/' + repo_config['branch'])
        commands.append('git submodule update --init --recursive')

        # All commands need to success
        res = []

        for command in commands:
            return_command = ProcessWrapper().call(command, cwd=repo_config['path'], shell=True, supressStderr=True)
            res.append(return_command[0])
            if return_command[0] != 0:
                logger.error("Command '%s' failed with exit code %s" % (command, res))
                break

        if res[0] == 0 and os.path.isdir(repo_config['path']):
            logger.info("Repository %s successfully initialized" % repo_config['path'])
        else:
            logger.error("Unable to init repository %s" % repo_config['path'])

        return int(res[0])

    @staticmethod
    def pull(repo_config):
        """Pulls the latest version of the repo from the git server"""
        import logging
        from .process import ProcessWrapper
        import os
        import platform

        logger = logging.getLogger()
        logger.info("Updating repository %s" % repo_config['path'])

        # Only pull if there is actually a local copy of the repository
        if 'path' not in repo_config:
            logger.info('No local repository path configured, no pull will occure')
            return 0

        commands = []

        # On Windows, bash command needs to be run using bash.exe. This assumes bash.exe
        # (typically installed under C:\Program Files\Git\bin) is in the system PATH.
        if platform.system().lower() == "windows":
            commands.append('bash -c "cd \\"' + repo_config['path'] + '\\" && unset GIT_DIR"')
        else:
            commands.append('unset GIT_DIR')

        if "prepull" in repo_config:
            commands.append(repo_config['prepull'])

        commands.append('git fetch ' + repo_config['remote'])
        commands.append('git reset --hard ' + repo_config['remote'] + "/" + repo_config['branch'])
        commands.append('git submodule update --init --recursive')

        if "postpull" in repo_config:
            commands.append(repo_config['postpull'])

        # All commands need to success
        res = []
        for command in commands:
            return_command = ProcessWrapper().call(command, cwd=repo_config['path'], shell=True, supressStderr=True)
            res.append(return_command[0])

            if return_command[0] != 0:
                logger.error("Command '%s' failed with exit code %s" % (command, res))
                break

        if res[0] == 0 and os.path.isdir(repo_config['path']):
            logger.info("Repository %s successfully updated" % repo_config['path'])
        else:
            logger.error("Unable to update repository %s" % repo_config['path'])

        return int(res[0])

    @staticmethod
    def clone(repo_config):
        """Clones the latest version of the repo from the git server"""
        import logging
        from .process import ProcessWrapper
        import os
        import platform

        logger = logging.getLogger()
        logger.info("Cloning repository %s" % repo_config['path'])

        # Only pull if there is actually a local copy of the repository
        if 'path' not in repo_config:
            logger.info('No local repository path configured, no clone will occure')
            return 0

        commands = []
        commands.append('unset GIT_DIR')
        commands.append('git clone --recursive ' + repo_config['url'] + ' -b ' + repo_config['branch'] + ' ' + repo_config['path'])

        # All commands need to success
        res = []
        for command in commands:
            return_command = ProcessWrapper().call(command, shell=True)
            res.append(return_command[0])

            if return_command[0] != 0:
                logger.error("Command '%s' failed with exit code %s" % (command, res))
                break

        if res[0] == 0 and os.path.isdir(repo_config['path']):
            logger.info("Repository %s successfully cloned" % repo_config['url'])
        else:
            logger.error("Unable to clone repository %s" % repo_config['url'])

        return int(res[0])

    @staticmethod
    def deploy(repo_config):
        """Executes any supplied post-pull deploy command"""
        from .process import ProcessWrapper
        import logging
        logger = logging.getLogger()

        if 'path' in repo_config:
            path = repo_config['path']

        if not 'deploy_commands' in repo_config or len(repo_config['deploy_commands']) == 0:
            logger.info('No deploy commands configured')
            return []

        logger.info('Executing %s deploy commands' % str(len(repo_config['deploy_commands'])))

        # Use repository path as default cwd when executing deploy commands
        cwd = (repo_config['path'] if 'path' in repo_config else None)

        res = []
        errors = []
        for cmd in repo_config['deploy_commands']:
            return_command = ProcessWrapper().call([cmd], cwd=cwd, shell=True)
            res.append(return_command[0])
            errors.append({
                'command': cmd,
                'repo_url': repo_config.get('url'),
                'return_code': return_command[0],
                'errors': return_command[1],
                'errors_info': return_command[2],
            })

        logger.info('%s commands executed with status; %s' % (str(len(res)), str(res)))

        repo_url  = os.path.basename(repo_config.get('url')).replace('.git', '')

        message = u"Репозиторий: " + repo_url + "\n"

        message_log = ''
        message_log_error = ''

        status_return = u'Успех'

        for error in errors:
            if error['return_code'] == 0:
                status_return = u'Успех'
            else:
                status_return = u'Ошибка'

            message += u'Статус выполнения команды "' + error['command'] + '" деплоя: ' + status_return + "\n"

            if error['errors']:
                message_log_error = "\n".join(error['errors'])
            if error['errors_info']:
                message_log = "\n".join(error['errors_info'])

        # if repo_config['smtp_server'] and repo_config['smtp_port'] and repo_config['smtp_login'] and repo_config['smtp_password'] and repo_config['smtp_to'] and repo_config['smtp_from']:
        send_notify_mail(
            repo_config, message, status_return, message_log_error, message_log, repo_url
        )

        logger.info(u"\n\n\n=====================" + message + "=====================\n\n\n")
        logger.info("An email has been sent to " + ", ".join(repo_config['smtp_to']))

        return res, errors
