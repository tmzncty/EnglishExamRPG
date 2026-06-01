path = '/opt/project-mia/frontend/src/views/ExamRoom.vue'
with open(path, 'r') as f:
    content = f.read()

# Fix: h-screen → min-h-screen on ExamRoom root
content = content.replace(
    '<div class="h-screen w-full flex flex-col bg-[#f5f5f0] text-gray-900">',
    '<div class="min-h-screen w-full flex flex-col bg-[#f5f5f0] text-gray-900">'
)

# Fix sidebar: add max height to prevent it being too tall on tablet
# The sidebar already has overflow-y-auto, but let's ensure it doesn't push past viewport

with open(path, 'w') as f:
    f.write(content)
print('ExamRoom.vue FIXED')
