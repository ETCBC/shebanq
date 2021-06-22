from mql import mql

q = '''
Select all objects where
[sentence
  [word focus lex='JHWH/']
  [word focus lex='>LHJM/']
]
GO
'''

msgs = []

print(mql('4b', q))
