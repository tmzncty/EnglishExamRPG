path = '/opt/project-mia/frontend/index.html'
with open(path, 'r') as f:
    content = f.read()

# Fix viewport for tablet: viewport-fit=cover + interactive-widget=resizes-content
# This tells mobile/tablet browsers to account for their UI chrome in the viewport
content = content.replace(
    '<meta name="viewport" content="width=device-width, initial-scale=1.0" />',
    '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, interactive-widget=resizes-content" />'
)

# Fix title
content = content.replace(
    '<title>frontend</title>',
    '<title>Project Mia</title>'
)

with open(path, 'w') as f:
    f.write(content)
print('index.html FIXED')
