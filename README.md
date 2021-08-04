# dynamic_dns
Google Public DNS client

## Configuration

The script requires a configuration/data file `dynamic_dns.yml` that will be read/rewritten by the script. The script uses Gmail to send an email alert when the API returns certain errors that may need to be handled before continuing. The program supports multiple sites in case multiple entries are needed. The format is as follows:

    ---
    config:
      email_from: username@gmail.com
      email_to: username@gmail.com
      username: username@gmail.com
      password: password
    sites:
      host.domain.com:
        username: JfQaStOWZgKMPknR
        password: fBVuQpTLwylOmGWb
        use_local_ip: eth0

* `config` section contains the email configuration
  * `email_from` is the from email address. This needs to be an email address that the Gmail account has previously authorized to send mail. 
  * `email_to` is the destination email address.
  * `username` and `password` are the credentials to the Gmail account.
* `sites` is a list of hostnames. Each hostname has a `username` and `password` from the Google Domains Dynamic DNS configuration. 
  * `use_local_ip` flag can be used if the local IP is needed rather than the internet-accessible IP. This should be set to the name of the interface to be used. To disable this feature, remove this configuration line.
  * If an error occurred such as nohost, badauth, notfqdn, badagent, abuse, 911 or conflict, a flag `last_result: error` will be set in the configuration file. This will need to be removed before the program will attempt to call the API for that domain.

Logging currently goes to dynamic_dns.log, but this can be changed by modifying line 11. I'll add this to the config file for greater flexibility in a future version..
