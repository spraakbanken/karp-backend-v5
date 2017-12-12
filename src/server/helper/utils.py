
''' Decorator function @route
    Adds the function to a list of urls, which should later be processed
    by Flask (see flaskhelper.py)
    If 'name' is not given, the url will be the name of the function.
    If 'url', it will appended to the function name, and may contain variable
    parts of the path
    'methods' is a list of allowed methods, defaults to 'GET'
    Example:
    urls = []
    @route(urls)
    def mypage():
       return render_page("hello")
    ==> /mypage

    @route(urls, '<pagename>')
    def mypage(pagename=''):
       return render_page("welcome to"+pagename)
    ==> /mypage/any_page_name
'''


def route(urls, url='', methods=None, crossdomain=True, name=None):
    def f(func):
        if name is not None:
            urlname = name
        elif url:
            urlname = '/%s/%s' % (func.__name__, url)
        else:
            urlname = '/%s' % func.__name__
        urls.append((urlname, func, methods, crossdomain))
        return func
    return f
