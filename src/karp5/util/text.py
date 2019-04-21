if isinstance(b"", str):                                                        
    byte_types = (str, bytes, bytearray)                                        
    text_types = (unicode, )                                                    
    def uton(x): return x.encode('utf-8', 'surrogateescape')                    
    def ntob(x): return x                                                       
    def ntou(x): return x.decode('utf-8', 'surrogateescape')                    
    def bton(x): return x
else:                                                                           
    byte_types = (bytes, bytearray)                                             
    text_types = (str, )                                                        
    def uton(x): return x                                                       
    def ntob(x): return x.encode('utf-8', 'surrogateescape')                    
    def ntou(x): return x                                                       
    def bton(x): return x.decode('utf-8', 'surrogateescape')    

escape_tm = dict((k, ntou(repr(chr(k))[1:-1])) for k in range(32))              
escape_tm[0] = u'\0'                                                            
escape_tm[7] = u'\a'                                                            
escape_tm[8] = u'\b'                                                            
escape_tm[11] = u'\v'                                                           
escape_tm[12] = u'\f'                                                           
escape_tm[ord('\\')] = u'\\\\'

def escape_control(s):                                                          
    if isinstance(s, text_types):                                               
        return s.translate(escape_tm)
    else:
        return s.decode('utf-8', 'surrogateescape').translate(escape_tm).encode('utf-8', 'surrogateescape')

def unescape_control(s):                                                        
    if isinstance(s, text_types):                                               
        return s.encode('latin1', 'backslashreplace').decode('unicode_escape')
    else:                                                                       
        return s.decode('utf-8', 'surrogateescape').encode('latin1', 'backslashreplace').decode('unicode_escape').encode('utf-8', 'surrogateescape')



# Replace with a less hacky function? originally from:
# https://stackoverflow.com/questions/9778550/which-is-the-correct-way-to-encode-escape-characters-in-python-2-without-killing
#def control_escape(s):
    #""" Escapes control characters so that they can be parsed by a json parser.
    #Eg. '\u0001' => '\\u0001'
    #Note that u'\u0001'.encode('unicode_escape') will encode the string as
    #'\\x01', which do not work for json. Hence the .replace('\\x', '\u00').
    #"""
    # the set of characters migth need to be extended
    #if type(s) is not str and type(s) is not str:
    #    s = str(s)
    #control_chars = [chr(c) for c in range(0x20)]
    #return u''.join([c.encode('unicode_escape').replace('\\x', '\u00')
     #                if c in control_chars else c for c in s])

