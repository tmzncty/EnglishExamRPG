path = '/opt/project-mia/frontend/src/components/Layout.vue'
with open(path, 'r') as f:
    content = f.read()

# Fix 1: Root div - h-screen overflow-hidden → min-h-screen (allow scroll + grow)
content = content.replace(
    '<div class="relative w-full h-screen bg-[#f5f5f0] overflow-hidden">',
    '<div class="relative w-full min-h-screen bg-[#f5f5f0]">'
)

# Fix 2: Inner content area - h-full → min-h-full (allow child to grow)
content = content.replace(
    '<div class="relative z-10 w-full h-full">',
    '<div class="relative z-10 w-full min-h-full">'
)

# Fix 3: Bottom nav - add safe area padding for tablet browsers
content = content.replace(
    '<div id="global-nav" class="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50 flex gap-2 bg-white/90 backdrop-blur shadow-lg border border-gray-200 p-1.5 rounded-full tablet:bottom-auto tablet:top-1/2 tablet:left-6 tablet:-translate-y-1/2 tablet:-translate-x-0 tablet:flex-col tablet:gap-1 tablet:p-2 tablet:rounded-2xl">',
    '<div id="global-nav" class="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50 flex gap-2 bg-white/90 backdrop-blur shadow-lg border border-gray-200 p-1.5 rounded-full tablet:bottom-auto tablet:top-1/2 tablet:left-6 tablet:-translate-y-1/2 tablet:-translate-x-0 tablet:flex-col tablet:gap-1 tablet:p-2 tablet:rounded-2xl" style="margin-bottom: env(safe-area-inset-bottom, 0px);">'
)

with open(path, 'w') as f:
    f.write(content)
print('Layout.vue FIXED')
