import sb.server.searching as searching
import src.server.errorhandler as eh
import src.server.helper.configmanager as configM
from src.server.helper.utils import route
from flask import request

# sb spec

def init():
    urls = []

    @route(urls)
    def saldopath():
        return searching.saldopath(configM.elastic('saldo'))


    # Just for test purposes:
    @route(urls, methods=["POST", "GET"], crossdomain=False)
    def error():
        raise Exception("Tralala")


    @route(urls, methods=["POST", "GET"], crossdomain=False)
    def errortut():
        raise eh.KarpException("Tut tut")


    @route(urls, methods=["POST", "GET"])
    def autherror():
        raise eh.KarpAuthenticationError("Testing the authentication error")


    @route(urls, methods=["POST", "GET"])
    def generalerror():
        """User gets some default message, the real error is logged."""
        user_message = "A karponaut has intentionally caused this error for testing purposes."
        query = request.path
        try:
            "string".add(1)
        except Exception as e:
            raise eh.KarpGeneralError("Testing KarpGeneralError",
                                      user_msg=user_message, debug_msg=e.message,
                                      query=query)

    return urls
