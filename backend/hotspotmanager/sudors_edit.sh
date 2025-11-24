# Execute ap_manager without asking password
echo 'ALL ALL=NOPASSWD: /usr/bin/ap_manager' | sudo EDITOR='tee -a' visudo -f ap_manager
