# a360-myhub-download

Python scripts to recursively request to export model files under
a directory and parse emails received for download links.

## Getting Started

### Prerequisites

To install the dependencies, run:

```
pip3 install -r requirements.txt
```

### Configuration

To use the scripts, first write a config file within the same directory
as in this repository and name it as config.py

Write following content into the file config.py
```
ACCT = 'your a360 account'
PASS = 'your password for the account'

EMAIL_POP3_SERVER = 'your email provider's pop server address'
EMAIL_ACCT = ACCT
EMAIL_PASS = 'your email password'
```

An example of config.py file would be:
```
ACCT = 'example@hotmail.com'
PASS = 'password'

EMAIL_POP3_SERVER = 'pop-mail.outlook.com'
EMAIL_ACCT = ACCT
EMAIL_PASS = 'emailPassword'
```

### Running

To download all the model files under a directory, first login your
a360 myhub account on [https://myhub.autodesk360.com](https://myhub.autodesk360.com)

Then enter the project, optionally enter the directory you want to batch download.
From the url, retrieve the long sequence containing both upper case and lower case letters and digits part after .../data/ and before another slash if there is one.

Run the download.py script and enter the long sequence just retrieved.

After the script is finished, wait until the a360 server has converted 
all files, then run the emailParse.py script.

After the script is finished, download links for these exports would be
stored in download-list.txt in current directory.

You can then use the following command or other tools to download them:
```
cat download-list.txt | xargs -I {} -P 5 sh -c 'wget -o /dev/null "{}"'
```



## TODO list
- [ ] refactor code
- [ ] user-friendly prompt for login details
- [ ] add support for other export file type
- [ ] add download support
- [ ] add a responsive cui interface to browse the project and download


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details