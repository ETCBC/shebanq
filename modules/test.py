class X:
    def __init__(self, offset):
        def inc(x):
            return offset + x

        setattr(self, "inc", inc)


xobj = X(5)

print(xobj.inc(6))
