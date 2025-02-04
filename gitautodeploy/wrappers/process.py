class ProcessWrapper():
    """Wraps the subprocess popen method and provides logging."""

    def __init__(self):
        pass

    @staticmethod
    def call(*popenargs, **kwargs):
        """Run command with arguments. Wait for command to complete. Sends
        output to logging module. The arguments are the same as for the Popen
        constructor."""

        from subprocess import Popen, PIPE
        import logging
        logger = logging.getLogger()

        kwargs['stdout'] = PIPE
        kwargs['stderr'] = PIPE

        supressStderr = None
        if 'supressStderr' in kwargs:
            supressStderr = kwargs['supressStderr']
            del kwargs['supressStderr']

        p = Popen(*popenargs, **kwargs)
        stdout, stderr = p.communicate()

        # Decode bytes to string (assume utf-8 encoding)
        stdout = stdout.decode("utf-8")
        stderr = stderr.decode("utf-8")

        errors = []
        errors_info = []

        if stdout:
            for line in stdout.strip().split("\n"):
                logger.info(line)
                errors_info.append(line)

        if stderr:
            for line in stderr.strip().split("\n"):
                if supressStderr:
                    logger.info(line)
                    errors_info.append(line)
                else:
                    logger.error(line)
                    errors.append(line)

        return p.returncode, errors, errors_info
