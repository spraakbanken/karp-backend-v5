from flask import jsonify
from src.server.helper.utils import route
import skbl.searching as searching


def init():
    urls = []

    @route(urls)
    def getplaces():
        ans = searching.get_places()
        return jsonify({"places": ans})


    @route(urls)
    def getplacenames():
        ans = searching.get_placenames()
        return jsonify({"places": ans})

    return urls
