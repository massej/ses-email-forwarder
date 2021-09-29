# ses-email-forwarder
 ### Amazon Simple Email Service Forwarder
 ### Serverless Lambda Python Function
 
# Lambda environment variables configuration

| Name        | Description           |
| ------------- |:-------------:|
| AddHeader      | If we need to add the received header into the email message.<br></br><br></br>Value must be "True" or "False"<br></br><br></br>Example :<br></br>--------------------------------<br></br>From : Tester <testemail@domain.com><br></br>Date : Tue, 20 Jul 2021 18:10:39 +0000<br></br>To : Firstname Lastname <email@domain.com><br></br>Subject : email subject<br></br><br></br>Type : boolean.|
| EmailList      | JSON email rules list.<br></br><br></br>The first column is the rules and the second column is where to forward the email.<br></br><br></br>If there are no rules that matched with the received email then it will use the catch-all address.<br></br><br></br>Example (JSON string) :<br></br><br></br>{<br></br>    "test@": "test@domain.com "<br></br>    "catch-all": "jonathanmasse@domain.com"<br></br>}<br></br><br></br>Type : string.|
| MailFromEmailAddress | Email to use when forwarding email.<br></br><br></br>This parameter is used only when "UseResentHeader" is set to "False"<br></br><br></br>Type : string.|
| Region | Current lambda function Amazon Region to use.<br></br><br></br>Type : string.|
| S3Bucket | S3 Bucket where to store the received email.<br></br><br></br>Type : string.|
| S3Prefix | S3 Prefix (folder) where to store the received email.<br></br><br></br>Type : string.|
| UseEMLAttachment | If we need to put the forwarded email as an attachment (EML file).<br></br>Value must be "True" or "False"<br></br>Type : boolean.|
| UseEMLBase64Format | If the email attachment (EML file) needs to be under base64 format.<br></br><br></br>This parameter is used only when "UseEMLAttachment" is set to "True"<br></br><br></br>Value must be "True" or "False"<br></br><br></br>* Take note that the iPhone cannot open EML file is the attachment is under base64 format.<br></br><br></br>Type : boolean.|
| UseResentHeader | If we need to use Resent headers / parameters in the email.<br></br><br></br>* Take note that some email software will block email when using this option. (The From field will be a copy of the received email and can cause SPF or DKIM to fail.)<br></br><br></br>Value must be "True" or "False"<br></br><br></br>* Recommended value is "False"<br></br><br></br>Type : boolean.|
| UseSubjectEMLFilename | If we need to use the email subject as the EML file attachment filename.<br></br><br></br>If false the EML file attachment will be the message id / filename on the S3 bucket.<br></br><br></br>Value must be "True" or "False"<br></br><br></br>Type : boolean.|
