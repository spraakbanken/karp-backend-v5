import smtplib
from email.mime.text import MIMEText
import karp_backend.server.helper.configmanager as configM
# Sends emails from the adress specified in dbconf.py


def send_notification(email, subject, message):
    # From https://docs.python.org/2/library/email-examples.html
    sender_email = configM.config['DB']['SENDER_EMAIL']
    try:
        if type(message) is unicode:
            message = message.encode('utf-8')
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = sender_email
        if type(email) is list:
            emailstring = ', '.join(email)
            emaillist = email
        else:
            emailstring = email
            emaillist = [email]
        msg['To'] = emailstring
        s = smtplib.SMTP('localhost')
        s.sendmail(sender_email, emaillist, msg.as_string())
        s.quit()
    except Exception as e:
        import datetime
        import logging
        error = '%s: Could not send notification to email %s,  %s\n %s'\
                % (datetime.datetime.now(), str(email), str(e), message)
        logging.exception(error)
