from karp_backend.server.translator import parser


def test_simple_1(client):
    args = {
        'q': 'simple||stort hus',
        'resource': 'test',
        'mode': 'karp'
    }
    settings = {
        'allowed': ['test']
    }

    result = parser.parse(args, settings)

    print(repr(result))
    assert 'query' in result
    assert 'bool' in result['query']
