# ses-email-forwarder
 Amazon Simple Email Service Forwarder - ses-email-forwarder
 
Configuration

Name	Description
AddHeader	If we need to add the received header into the email message.

Value must be "True" or "False"

Example : 
________________________________
From : Tester <testemail@domain.com >
Date : Tue, 20 Jul 2021 18:10:39 +0000
To : Firstname Lastname <email@domain.com>
Subject : email subject

Type : boolean.
EmailList	JSON email rules list.

The first column is the rules and the second column is where to forward the email.

If there are no rules that matched with the received email then it will use the catch-all address.

Example (JSON string) :

{
    "test@": "test@domain.com "
    "catch-all": "jonathanmasse@domain.com"
}


Type : string.
MailFromEmailAddress	Email to use when forwarding email.

This parameter is used only when "UseResentHeader" is set to "False"

Type : string.


Name	Description
Region	Current lambda function Amazon Region to use.

Type : string.
S3Bucket	S3 Bucket where to store the received email.

Type : string.
S3Prefix	S3 Prefix (folder) where to store the received email.

Type : string.
UseEMLAttachment	If we need to put the forwarded email as an attachment (EML file).

Value must be "True" or "False"

Type : boolean.
UseEMLBase64Format	If the email attachment (EML file) needs to be under base64 format.

This parameter is used only when "UseEMLAttachment" is set to "True"

Value must be "True" or "False"

* Take note that the iPhone cannot open EML file is the attachment is under base64 format.

Type : boolean.
UseResentHeader	If we need to use Resent headers / parameters in the email.

* Take note that some email software will block email when using this option. (The From field will be a copy of the received email and can cause SPF or DKIM to fail.)

Value must be "True" or "False"

* Recommended value is "False"

Type : boolean.

 
Name	Description
UseSubjectEMLFilename	If we need to use the email subject as the EML file attachment filename.

If false the EML file attachment will be the message id / filename on the S3 bucket.

Value must be "True" or "False"

Type : boolean.

