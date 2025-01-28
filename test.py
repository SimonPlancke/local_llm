import os

filepath = 'C:\\Users\\simon.plancke\\OneDrive - Keyrus\\Documents\\repositories\\dap_appl_dala_code'

print(os.walk(filepath))

for dirpath, dirnames, filenames in os.walk(filepath):
    for file in filenames:
        print(file)