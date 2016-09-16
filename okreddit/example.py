subs = {
    'ALLOWED': ['one', 'two'],
    'DISALLOWED': ['three', 'four']
}

comments = {}
for sub in subs['ALLOWED']:
    # reverse and uppercase
    comments[sub] = sub[-1:-6:-1].upper()

print(comments)
