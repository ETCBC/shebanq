from mql import mql

test_queries = (
'',
'''
''',
'''select all  objects where
[word focus lex='x']
''',
'''
    select all objects where
    [book book=Genesis
        [chapter chapter=1
            [word focus lex="H"]
            ..
            [word focus lex="H"]
        ]
    ]
''',
'''
    select all objects where
    [book book=Genesis
        [chapter chapter=1
            [word focus lex="H"]
            ..
            [word focus lex="H"]
        ]
    ] 
//''',
'''
    select all objects where
    [book book=Genesis
        [chapter chapter=1
            [word focus lex="H"]
            ..
            [word focus lex="H"]
        ]
    ] 
/*''',
'''
    select all objects where
    [book book=Genesis
        [chapter chapter=1
            [word focus lex="H"]
            ..
            [word focus lex="H"]
        ]
    ] 
/* aaa /* */''',
'''
    select all objects where
    [book book=Genesis
        [chapter chapter=1
            [word focus lex="H"]
            ..
            [word focus lex="H"]
        ]
    ] 
/* aaa /* bbb /* ccc */''',
'''
    select all objects where
    [book book=Genesis
        [chapter chapter=1
            [word focus lex="H"]
            ..
            [word focus lex="H"]
        ]
    ] 
/* aaa /* */ /* bbb */''',
'''select all  objects where
[phrase focus function = Pred]
''',
'''select all  objects where
[book book=Genesis [word focus lex='JC/']]
''',
'''select all  objects where
[book [chapter chapter=1 [word focus]]]
''',
)

print mql(test_queries[-2])

'''
for query in test_queries:
    (good, result) = mql(query)
    if good:
        monads = eval(result)
        print "QUERY{}\n=====>\n{}\n===SUCCESS={}==\n".format(query, monads, len(monads))
    else:
        print "QUERY{}\n=====>\n{}\n===FAILED===\n".format(query, result)
'''
