import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from crawler import utils

email_configuration = utils.get_config()['EMAIL']
port = 465  # For SSL
sender_email = email_configuration['Sender']
receiver_email = email_configuration['Receiver']
password = email_configuration['Password']


def generate_message(new_offers):
    """Format the content of the message, which will be send"""
    def format_row(offer):
        return f'<li><a href="{offer.url}">{offer.title} : {offer.price}</a>' \
               f'</li>'

    message = MIMEMultipart("alternative")
    message['Subject'] = "New offers found!"
    message["From"] = sender_email
    message["To"] = receiver_email

    formatted_offers = list(map(format_row, new_offers))
    formatted_offers = "\n".join(formatted_offers)

    content = f"""\
    <html>
      <body>
        <p>New offers detected:<br></p>
        <ul>
          {formatted_offers}
        </ul>
      </body>
    </html>
    """
    message.attach(MIMEText(content, "html"))
    return message


def send_message(message):
    """Send message to preconfigured email"""
    with smtplib.SMTP_SSL("smtp.gmail.com", port) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
