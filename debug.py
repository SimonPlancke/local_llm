content = '/tree/thisworks?'

if content.startswith(('/downloads', '/tree', '/uptodate')):
    pdf_url = 'https://sci-hub.se' + content
else:
    pdf_url = 'https:/' + content

print(pdf_url)