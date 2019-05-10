import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import os
from email import encoders
from datetime import datetime

# atexit allows for a method to be set to handle an object when the script             exits
import atexit

class MailLogger():

    def __init__(self, filePath, smtpDict):
        self.filePath = filePath
        self.smtpDict = smtpDict
        # Generate dated logfile
        filename = '%s.log' % (datetime.now().strftime("%Y_%m_%d"))
        # Create full filename and filepath
        filename = '%s/%s' % (filePath,filename)
        self.filename = filename
        self.fileLogger = logging.getLogger('mailedLog')
        self.fileLogger.setLevel(logging.INFO)
        self.fileHandler = logging.FileHandler(filename)
        self.fileHandler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.fileHandler.setFormatter(formatter)
        self.fileLogger.addHandler(self.fileHandler)
        atexit.register(self.mailOut)

    def mailOut(self):
        '''
        Script is exiting so time to mail out the log file

        "smtpDict":    {
                            "smtpServer"    :     "smtp.dom.com",
                            "smtpPort"        :    25,
                            "sender"        :    "sender@dom.com>",
                            "recipients"    :    [
                                                    "recipient@dom.com"
                                                ],
                            "subject"        :    "Email Subject"
    },
        '''
        # Close the file handler
        smtpDict = self.smtpDict
        self.fileHandler.close()
        msg = MIMEMultipart('alternative')
        s = smtplib.SMTP(smtpDict["smtpServer"], smtpDict["smtpPort"] )
        s.starttls()
        s.login(smtpDict["username"], smtpDict["password"])
        msg['Subject'] = smtpDict["subject"]
        msg['From'] = smtpDict["sender"]
        msg['To'] = ','.join(smtpDict["recipients"])
        body = 'See attached report file'
        content = MIMEText(body, 'plain')
        msg.attach(content)
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(open(self.filename, 'rb').read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(self.filename))
        msg.attach(attachment)
        s.sendmail(smtpDict["sender"],smtpDict["recipients"],msg.as_string())
        s.quit()
