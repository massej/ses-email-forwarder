# lambda_function.py
# Edited by Jonathan Massé.
# Date : 2021-06-26.
# Goal : Forward email based on a dictionary list inside this lambda function.
#
# Copyright 2010-2021 Jonathan Massé, Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# This file is licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License. A copy of the
# License is located at
#
# http://aws.amazon.com/apache2.0/
#
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
#
# Email structure
#
#   mixed
#       alternative
#           text
#           html or related
#               html
#               inline image
#               inline image
#       attachment
#       attachment


# Includes.
import os
import boto3
import email
import re
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import Message
from email.mime.message import MIMEMessage
from email.mime.application import MIMEApplication
from email.header import decode_header, make_header
from datetime import datetime, timezone
import html
import traceback
import quopri
import unicodedata
import json


"""
decode_email_list_to_string
decode email list to string. (If needed).
If the input value is already a string, it will do nothing.
Ex : Convert a list ["example1@domain", "example2@domain"] to "example1@domain, example2@domain"
:param value: The email list to decode.
:return: decoded email list in string.
"""
def decode_email_list_to_string(value) -> str:

    # Email default separator.
    separator = ", "

    # If value is a list.
    if type(value) is list:
        return separator.join(value)
    else:
        return value


"""
decode_email_header
decode email header string
Ex : It can have encoding parameter (i.e. : UTF-8)
i.e.        Subject: [ 201105161048 ] GewSt: =?utf-8?q?_Wegfall_der_Vorl=C3=A4ufigkeit?=
(decoded)   Subject: [ 201105161048 ] GewSt:  Wegfall der Vorläufigkeit
:param header_text_input: The header text input to decode.
:return: decoded string header.
"""
def decode_email_header(header_text_input: str) -> str:
    return str(make_header(decode_header(header_text_input)))


"""
encode_email_line
encode an email line (string).
i.e. Encode an email line (string) to HTML or plain/text.
:param text_input: The line string text input to encode.
:param format_html: If we need to format/encode under HTML format or plain/text.
:return: encoded string line.
"""
def encode_email_line(text_input: str, format_html: bool) -> str:
    return html.escape(text_input) if format_html else text_input


"""
get_part_content_transfer_encoding
Return the part content transfer encoding under string format.
i.e. base64, 8bit, 7bit.
:param current_part: The current email MIME part to get the content transfer encoding.
:return: The content transfer encoding (string)
"""
def get_part_content_transfer_encoding(current_part: object) -> str:
    # If do not exist, we return an empty string.
    return current_part["Content-Transfer-Encoding"].lower().strip() if "Content-Transfer-Encoding" in current_part else ""


"""
get_part_content_charset
Return the part content charset under string format.
i.e. utf-8, iso-8859-1.
:param current_part: The current email MIME part to get the content charset.
:return: The content charset (string)
"""
def get_part_content_charset(current_part: object) -> str:
    # If charset is not set (None) then, we set to UTF-8 by default.
    return 'utf-8' if current_part.get_content_charset() is None else current_part.get_content_charset()


"""
remove_accent_chars
Remove / replace accent characters in a text input.
i.e. replace "é" by "e" etc. ("testé" -> "teste")
:param text_input: The text input to remove accents.
:return: string without accent.
"""
def remove_accent_chars(text_input: str) -> str:
    return "".join([c for c in unicodedata.normalize('NFKD', text_input) if not unicodedata.combining(c)])


"""
extract_email_address
Extract an email address from a string input.
i.e. "test <test-@cddf.com>" will return "test-@cddf.com"
:param text_input: The text input that contains the email address.
:return: the email address string.
"""
def extract_email_address(text_input: str) -> str:
    # Search for an email address.
    result = re.search(r"\w+([-+.']\w*)*@\w+([-.]\w+)*\.\w+([-.]\w+)*", text_input)

    # If there no result, return an empty string.
    if result is None:
        return ""
    # If there is a result then return the match found.
    else:
        return result.group(0)


"""
get_body_text
Prepare email body text / message to be send.
:param mailobject_received: The mail object received to use to create the message.
:param error: The error string message.
:param format_html: If we need to format under HTML format.
:param format_quote_printed: If we need format output to quote printed format.
:param charset_quote_printed: Quote printed conversion charset.
:return: string (The email body text / message).
"""
def get_body_text(mailobject_received: email.message, error: str, format_html: bool, format_quote_printed: bool = False, charset_quote_printed: str = 'utf-8') -> str:
    # Prepare the separator (html or plain text one)
    # IMPORTANT : plain-text need to have 4 spaces before the \r\n to be sure that it will work.
    separator = ("<br>\r\n" if format_html else "    \r\n")

    mailobject_received_decoded_from = decode_email_header(mailobject_received['From'])
    mailobject_received_decoded_date = decode_email_header(mailobject_received['Date'])
    mailobject_received_decoded_to = decode_email_header(mailobject_received['To'])
    mailobject_received_decoded_subject = decode_email_header(mailobject_received['Subject'])

    # Prepare email message / body text.
    bodytext = ("________________________________" + separator
                + "From : " + encode_email_line(mailobject_received_decoded_from, format_html) + separator
                + "Date : " + encode_email_line(mailobject_received_decoded_date, format_html) + separator
                + "To : " + encode_email_line(mailobject_received_decoded_to, format_html) + separator
                + "Subject : " + encode_email_line(mailobject_received_decoded_subject, format_html) + separator + separator)

    # If there is an error message to display / to add.
    if error:
        bodytext = ("FORWARD EMAIL ERROR ! This email cannot be forwarded !" + separator +
                "ERROR : " + encode_email_line(error, format_html) + separator + bodytext)

    # Return the email body text / message.
    if format_quote_printed:
        return quopri.encodestring(bodytext.encode(charset_quote_printed)).decode(charset_quote_printed)
    else:
        return bodytext


"""
add_header_text
Add header text message to a new email.
i.e. : 
________________________________
From : Firstname Lastname <fromexample@example.com>
Date : Tue, 29 Jun 2021 18:53:26 -0400
To : example@example.com
Subject : test

:param mailobject_received: The mail object received to use to create the message.
:param mailobject_to_send: The mail object to be sent. (Must be the mime/alternative part.)
:param error: The error string to add.
:return: None
"""
def add_header_text(mailobject_received: email.message, mailobject_to_send: email.message, error: str = "") -> None:

    # Default charset to the new part.
    part_charset = email.charset.Charset('utf-8')
    part_charset.body_encoding = email.charset.QP

    # Create a MIME text part.
    text_part = MIMEText(get_body_text(mailobject_received, error, False), "plain", part_charset)
    # Attach the text part to the MIME message.
    mailobject_to_send.attach(text_part)

    # Create a MIME text part.
    text_part = MIMEText(get_body_text(mailobject_received, error, True), "html", part_charset)
    # Attach the text part to the MIME message.
    mailobject_to_send.attach(text_part)
    return None


"""
append_header_text_part
Append header text message (under plain/text or HTML format)
i.e. : 
________________________________
From : Firstname Lastname <fromexample@example.com>
Date : Tue, 29 Jun 2021 18:53:26 -0400
To : example@example.com
Subject : test

:param mailobject_received: The mail object received to use to create the message.
:param current_part: The current part to append the text message.
:param format_html: If we need to use HTML format. (If not it will be a plain/text format).
:return: None
"""
def append_header_text_part(mailobject_received: email.message, current_part: object, format_html: bool) -> None:
    part_content_transfer_encoding = get_part_content_transfer_encoding(current_part)
    part_content_charset = get_part_content_charset(current_part)

    # If this is not a quoted-printable format then we need to convert it.
    if part_content_transfer_encoding != "quoted-printable":
        current_part.set_payload(str(current_part.get_payload()).encode('utf-8')) # IMPORTANT : To fix encoding issue. Ex : "é" will become "Ã©".
        email.encoders.encode_quopri(current_part)
        del current_part["Content-Transfer-Encoding"]
        current_part.add_header("Content-Transfer-Encoding", "quoted-printable")

    # Prepare the new body part to add.
    current_part.set_payload(get_body_text(mailobject_received, "", format_html, True, part_content_charset) + current_part.get_payload())
    return None


"""
append_header_text
Append header text message to an existing email.
i.e. : 
________________________________
From : Firstname Lastname <fromexample@example.com>
Date : Tue, 29 Jun 2021 18:53:26 -0400
To : example@example.com
Subject : test

:param mailobject_received: The mail object received to use to create the message.
:param mailobject_to_send: The mail object to be sent.
:return: None
"""
def append_header_text(mailobject_received: email.message, mailobject_to_send: email.message) -> None:

    # If found in the email then we need don't need to add again this part.
    found_plaintext_part = False
    found_html_part = False

    # For each mail part. (Check if text/plain or html is there and add the header text)
    for current_part in mailobject_to_send.walk():
        # Get current part content type.
        part_content_type = current_part.get_content_type()

        # If this is a plaintext part, add header.
        if not found_plaintext_part and part_content_type == 'text/plain':
            found_plaintext_part = True
            append_header_text_part(mailobject_received, current_part, False)

        # If this is an HTML part, add header.
        if not found_html_part and part_content_type == 'text/html':
            found_html_part = True
            append_header_text_part(mailobject_received, current_part, True)

    return None


"""
get_forward_email_to
Get the forward email address from the dictionary based on the original email address where it was supposed to be sent.
:param email: Original email destination.
:return: List of new email destination.
"""
def get_forward_email_to(email: str) -> list:
    # Load email list from environment variable.
    email_list_dictionnary = json.loads(os.environ['EmailList'])

    # For each key / value inside the email dictionary.
    for key, value in email_list_dictionnary.items():

        # If this is a match, return new destination email address.
        if re.match(key, email):
            # If value is a list.
            if type(value) is list:
                return value
            else:
                return [value]

    # If there is no match then return the catch-all email address.
    # If value is a list.
    value = email_list_dictionnary['catch-all']
    if type(value) is list:
        return value
    else:
        return [value]


"""
get_reply_to_value
Get the "Reply-To" email header string to set in the new email message.
i.e. Return "Reply-To" header if exist in the received message otherwise it will return the "From" header.
:param mailobject_received: The mail object received to use to create the message.
:return: The "Reply-To" string to set in the new email message.
"""
def get_reply_to_value(mailobject_received: email.message) -> str:
    # If "Reply-To" do not exist, we return "From".
    return mailobject_received["Reply-To"] if "Reply-To" in mailobject_received else mailobject_received["From"]


"""
get_message_from_s3
Return the message from s3 bucket by using the message id.
:param message_id: Message id in the s3 bucket.
:return: The eml file content stored on s3 bucket.
"""
def get_message_from_s3(message_id: str) -> object:
    incoming_email_bucket = os.environ['S3Bucket']
    incoming_email_prefix = os.environ['S3Prefix']

    # If there is a prefix.
    if incoming_email_prefix:
        object_path = incoming_email_prefix + "/" + message_id
    else:
        object_path = message_id

    # Not used.
    # S3 url / path.
    # aws_region = os.environ['Region']
    # object_http_path = f"https://s3.console.aws.amazon.com/s3/object/{incoming_email_bucket}/{object_path}?region={aws_region}"

    # Create a new S3 client.
    client_s3 = boto3.client("s3")

    # Get the email object from the S3 bucket.
    object_s3 = client_s3.get_object(Bucket=incoming_email_bucket, Key=object_path)

    # Prepare the dictionary to return.
    file_dict = {
        "Data": object_s3['Body'].read().decode('utf-8'),
        "MessageID": message_id,
        "ContentLength": object_s3['ContentLength'],
        "LastModified": object_s3['LastModified'],
        # Not used.
        # "Path": object_http_path
    }

    return file_dict


"""
create_message
Create the email message to be sent based on the old email.
:param file_dict: The eml file dictionary.
:return: A message object to be sent.
"""
def create_message(file_dict: object) -> object:
    # Parse the email body.
    mailobject_received = email.message_from_string(file_dict['Data'])

    # Log the received email.
    mail_to_recipient = get_forward_email_to(extract_email_address(decode_email_header(mailobject_received['To'])))
    print("From : " + decode_email_header(mailobject_received['From']) + "\r\n"
          + " Date : " + decode_email_header(mailobject_received['Date']) + "\r\n"
          + " To : " + decode_email_header(mailobject_received['To']) + "\r\n"
          + " Subject : " + decode_email_header(mailobject_received['Subject']) + "\r\n"
          + " Resent-From : " + os.environ['MailFromEmailAddress'] + "\r\n"
          + " Resent-To : " + decode_email_list_to_string(mail_to_recipient))

    # If email is to the forwarder then we need to ignore. (Maybe it's a vacation email that is bouncing back.)
    if decode_email_header(mailobject_received['To']).lower() == os.environ['MailFromEmailAddress']:
        print(f"Destination email is the same as the forwarder! (Maybe it's a vacation email that is bouncing back.) The forwarder will ignore this email!")
        exit()

    # Create a mixed - MIME container.
    mailobject_to_send = MIMEMultipart("mixed")
    mailobject_to_send.set_charset("utf-8")
    del mailobject_to_send["Content-Transfer-Encoding"] # By default it's adding base64 which can cause issue when converting to quote-printed if there is no Content-Transfer-Encoding in the email.

    # Add header.
    mailobject_to_send['Subject'] = mailobject_received['Subject']
    # If we need to use resent header.
    if eval(os.environ['UseResentHeader']):
        mailobject_to_send['Resent-Date'] = datetime.now(tz=timezone.utc).strftime("%a, %d %b %Y %T %z")
        mailobject_to_send['Resent-Message-ID'] = mailobject_received['Message-ID']
        mailobject_to_send['Resent-From'] = os.environ['MailFromEmailAddress']
        mailobject_to_send['Resent-To'] = mail_to_recipient
        mailobject_to_send['From'] = mailobject_received['From']
        mailobject_to_send['Date'] = mailobject_received['Date']
        mailobject_to_send['To'] = decode_email_list_to_string(mailobject_received['To'])
    else:
        mailobject_to_send['Originally-From'] = mailobject_received['From']
        mailobject_to_send['From'] = os.environ['MailFromEmailAddress']
        mailobject_to_send['Date'] = datetime.now(tz=timezone.utc).strftime("%a, %d %b %Y %T %z")
        mailobject_to_send['To'] = decode_email_list_to_string(mail_to_recipient)

    # If you decode and re-encode an header using < > it will convert the < > which can cause issue.
    # i.e. WORKING : mailobject_to_send['Reply-To'] = "=?utf-8?Q?Alex=20de=20Pige=20Qu=C3=A9bec?= <service@pige.quebec>"
    # i.e. FAIL : mailobject_to_send['Reply-To'] = "=?utf-8?q?Alex_de_Pige_Qu=C3=A9bec_=3Cservice=40pige=2Equebec=3E?="
    mailobject_to_send['Reply-To'] = get_reply_to_value(mailobject_received)

    # If we need to attach an eml attachment as email forward.
    if eval(os.environ['UseEMLAttachment']):

        # If we need to add header to the email to be forwarded.
        if eval(os.environ['AddHeader']):
            # Create an alternative - MIME container.
            mailobject_alternative = MIMEMultipart("alternative")
            mailobject_alternative.set_charset("utf-8")
            add_header_text(mailobject_received, mailobject_alternative)

            # Attach the alternative (text/html) part to the MIME message.
            mailobject_to_send.attach(mailobject_alternative)

        # The file name to use for the attached message. Uses regex to remove all
        # non-alphanumeric characters, and appends a file extension.
        filename = re.sub('[^0-9a-zA-Z]+', '_', remove_accent_chars(decode_email_header(mailobject_received['Subject'])) if eval(os.environ['UseSubjectEMLFilename']) else file_dict["MessageID"]) + ".eml"

        # Create a new MIME object under base64 format.
        # iPhone cannot open the eml file when it's under base64.
        # The filesize and date is working on base64. (The file will never change)
        if eval(os.environ['UseEMLBase64Format']):
            part_attachment = MIMEApplication(file_dict["Data"], filename)
            part_attachment.add_header("Content-Type", 'application/octet-stream', name=filename)
            part_attachment.add_header("Content-Description", filename)
            part_attachment.add_header("Content-Disposition", 'attachment', filename=filename, size=str(file_dict["ContentLength"]),
                            creation_date=file_dict["LastModified"].strftime("%a, %d %b %Y %T %z"),
                            modification_date=file_dict["LastModified"].strftime("%a, %d %b %Y %T %z"))
            # Attach the file object to the message.
            mailobject_to_send.attach(part_attachment)
        else:
            # Create a new MIME object under rfc822 format.
            # The iPhone can read the rfc822 format to read the eml file, but we cannot have the filesize or filedate.
            part_attachment = MIMEMessage(Message(), 'rfc822')
            part_attachment.add_header("Content-Type", 'message/rfc822', name=filename)
            part_attachment.add_header("Content-Description", filename)
            part_attachment.add_header("Content-Disposition", 'attachment', filename=filename)
            # Sometime the email edit the content when it's not in base64 so we need to ignore the content length / date. (It can be different)
            # size=str(file_dict["ContentLength"]),
            # creation_date=file_dict["LastModified"].strftime("%a, %d %b %Y %T %z"),
            # modification_date=file_dict["LastModified"].strftime("%a, %d %b %Y %T %z"))
            part_attachment.set_payload(file_dict["Data"])
            # Attach the file object to the message.
            mailobject_to_send.attach(part_attachment)

    # We need to copy received email payload to the new email payload.
    else:
        # Copy payload from last email to the new email.
        mailobject_to_send.set_payload(mailobject_received.get_payload(), mailobject_received.get_charset())

        # Update content-type accordingly.
        mailobject_to_send.replace_header('Content-Type', mailobject_received.get_content_type())

        # If we need to add Content-Transfer-Encoding header.
        if "Content-Transfer-Encoding" in mailobject_received:
            mailobject_to_send.add_header('Content-Transfer-Encoding', mailobject_received['Content-Transfer-Encoding'])

        # If we need to append header to the email to be forwarded.
        if eval(os.environ['AddHeader']):
            append_header_text(mailobject_received, mailobject_to_send)

    # Prepare message object to be sent.
    message = {
        "MailToRecipient": mail_to_recipient,
        "MailObjectToSend": mailobject_to_send,
        "MailObjectReceived": mailobject_received
    }

    return message


"""
send_email
Send email using the message object.
:param message: The message object to be sent.
:return: Result / status string. (Error or success)
"""
def send_email(message: object) -> str:

    # Create a new SES client.
    client_ses = boto3.client('ses', os.environ['Region'])

    # Send the email.
    try:
        # Provide the contents of the email.
        response = client_ses.send_raw_email(
            Source=os.environ['MailFromEmailAddress'],
            Destinations=message['MailToRecipient'],
            RawMessage={
                'Data': message['MailObjectToSend'].as_string()
            }
        )

    # Display an error if something goes wrong.
    except ClientError as e:
        # Printing stack trace
        traceback.print_exc()

        # Try to send an email with the error message.
        send_error_email(message, e.response['Error']['Message'])
        output = e.response['Error']['Message']
    else:
        output = "Email sent! Message ID: " + response['MessageId']

    return output


"""
send_error_email
Send error email to the mailToRecipient. (Ex : Message too large to be sent)
:param message: The message object to be sent.
:param error: The error string.
:return: None
"""
def send_error_email(message: object, error: str) -> None:

    # Create a new SES client.
    client_ses = boto3.client('ses', os.environ['Region'])

    # Create a mixed - MIME container.
    mailobject_to_send = MIMEMultipart("mixed")
    mailobject_to_send.set_charset("utf-8")
    del mailobject_to_send["Content-Transfer-Encoding"] # By default it's adding base64 which can cause issue when converting to quote-printed if there is no Content-Transfer-Encoding in the email.

    # Add subject, from and to lines.
    mailobject_to_send['Subject'] = "ERROR " + message['MailObjectToSend']['Subject']
    mailobject_to_send['From'] = message['MailObjectToSend']['From']
    mailobject_to_send['Date'] = datetime.now(tz=timezone.utc).strftime("%a, %d %b %Y %T %z")
    mailobject_to_send['To'] = message['MailObjectToSend']['To']

    # Create an alternative - MIME container.
    mailobject_alternative = MIMEMultipart("alternative")
    mailobject_alternative.set_charset("utf-8")
    add_header_text(message['MailObjectReceived'], mailobject_alternative, error)

    # Attach the alternative (text/html) part to the MIME message.
    mailobject_to_send.attach(mailobject_alternative)

    # Send the email.
    try:
        # Provide the contents of the email.
        response = client_ses.send_raw_email(
            Source=os.environ['MailFromEmailAddress'],
            Destinations=message['MailToRecipient'],
            RawMessage={
                'Data': mailobject_to_send.as_string()
            }
        )
    # Ignore error and continue, since we already have an error
    except:
        # Printing stack trace
        traceback.print_exc()
    return None


"""
lambda_handler
Main function called by amazon ses / lambda.
:param event: Event that is calling this function.
:param context: Context to use to run this lambda. 
:return: None
"""
def lambda_handler(event, context) -> None:

    # Main try catch.
    try:
        # Get the unique ID of the message. This corresponds to the name of the file
        # in S3.
        message_id = event['Records'][0]['ses']['mail']['messageId']
        print(f"Received message ID {message_id}")

        # Retrieve the file from the S3 bucket.
        file_dict = get_message_from_s3(message_id)

        # Create the message.
        message = create_message(file_dict)

        # Send the email and print the result.
        result = send_email(message)

        # Print the result / status.
        print(result)

    except:
        # Printing stack trace
        traceback.print_exc()
    return None
