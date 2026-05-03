import smtplib
from email.mime.text import MIMEText

msg = MIMEText('Test from SA Property Intel - it works!')
msg['Subject'] = 'SA Property Intel - Test Email'
msg['From'] = 'mboffa53@gmail.com'
msg['To'] = 'mboffa53@gmail.com'

try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login('mboffa53@gmail.com', 'uwbb cllk llox plsd')
        s.send_message(msg)
    print('SUCCESS - Email sent!')
except Exception as e:
    print(f'FAILED - Error: {e}')
