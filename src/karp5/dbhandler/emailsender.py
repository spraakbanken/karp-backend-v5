import smtplib
import six
import logging

from email.mime.text import MIMEText
import karp5.server.helper.configmanager as configM
# Sends emails from the adress specified in dbconf.py

_logger = logging.getLogger('karp5')


def send_notification(email, subject, message):
    # From https://docs.python.org/2/library/email-examples.html
    sender_email = configM.config['DB']['SENDER_EMAIL']
    try:
        if isinstance(message, six.text_type):
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
        smtp_server = 'localhost'
        if 'SMTP_SERVER' in configM.config['DB']:
            smtp_server = configM.config['DB']['SMTP_SERVER']
        _logger.debug('Using smtp server: {}'.format(smtp_server))
        s = smtplib.SMTP(smtp_server)
        s.sendmail(sender_email, emaillist, msg.as_string())
        s.quit()
    except Exception as e:
        import datetime
        error = '%s: Could not send notification to email %s,  %s\n %s'\
                % (datetime.datetime.now(), str(email), str(e), message)
        _logger.exception(error)
