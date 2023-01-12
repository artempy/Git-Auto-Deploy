# -*- coding: utf-8 -*-
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP_SSL
import os


def send_notify_mail(repo_config, message, status_return, errors_text,
                     errors_info_text, repo_url):
    date_now = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
    filepath_info = "logs/info_" + date_now + '.txt'
    filepath_errors = "logs/errors_" + date_now + '.txt'
    if not os.path.exists("logs"):
        os.makedirs("logs")

    if errors_info_text:
        with open(filepath_info, 'w') as f:
            f.write(errors_info_text)
    if errors_text:
        with open(filepath_errors, 'w') as f:
            f.write(errors_text)


    address = repo_config['smtp_from']

    part_info, part_error = None, None

    if errors_info_text:
        # Compose attachment
        basename = os.path.basename(filepath_info)
        part_info = MIMEBase('application', "octet-stream")
        part_info.set_payload(open(filepath_info,"rb").read() )
        part_info.add_header('Content-Disposition', 'attachment; filename="%s"' % basename)
        encoders.encode_base64(part_info)

    if errors_text:
        # Compose attachment
        basename = os.path.basename(filepath_errors)
        part_error = MIMEBase('application', "octet-stream")
        part_error.set_payload(open(filepath_errors, "rb").read())
        part_error.add_header('Content-Disposition', 'attachment; filename="%s"' % basename)
        encoders.encode_base64(part_error)

    # Compose message
    msg = MIMEMultipart()
    msg['From'] = address
    msg['To'] = ",".join(repo_config['smtp_to'])
    subject = u'Завершен процесс деплоя ' + repo_url + u' со статусом ' + status_return
    msg['Subject'] = subject.encode('utf-8')
    msg.attach(MIMEText(message.encode('utf-8'), 'plain', 'utf-8'))

    if errors_info_text and part_info:
        msg.attach(part_info)
    if errors_text and part_error:
        msg.attach(part_error)

    # Send mail
    smtp = SMTP_SSL()
    smtp.connect(host=repo_config['smtp_server'], port=repo_config['smtp_port'])
    smtp.login(repo_config['smtp_login'], repo_config['smtp_password'])
    smtp.sendmail(address, repo_config['smtp_to'], msg.as_string())
    smtp.quit()
