from zuu.UTILS.smart_query import SmartQuery

class TestSmartQuery:
    def test_format(self):
        assert SmartQuery.format('a|b') == 'a or b'
        assert SmartQuery.format('a&b') == 'a and b'
        assert SmartQuery.format('a|b&c') == 'a or b and c'
        assert SmartQuery.format('a|b&c!d') == 'a or b and c not d'

        assert SmartQuery.format('a.b(c)', ('a', 'b')) == "a.b('c')"
        assert SmartQuery.format("a = b*", ('a',)) == "re.match(r'b*', a)"
        assert SmartQuery.format('a|b&c!d', ('a', 'b', 'c', 'd')) == 'a or b and c not d'
        assert SmartQuery.format('a.b(c)', ('a', 'b', 'c')) == "a.b(c)"
        assert SmartQuery.format("a = b*", ('a', 'b')) != "re.match(r'b*', a)"

        # even more complex
        assert SmartQuery.format("a = b* and c = d*", ('a', 'b', 'c', 'd')) != "re.match(r'b*', a) and re.match(r'd*', c)"
        assert SmartQuery.format("a = b* and c = d*", ('a', 'c')) == "re.match(r'b*', a) and re.match(r'd*', c)"

    def test_match(self):
        assert SmartQuery.match({'a': 1, 'b': 2}, 'a==1') is True
        assert SmartQuery.match({'a': 1, 'b': 2}, 'a==2') is False

    def test_all(self):
        items = [{'a': 1, 'b': 2}, {'a': 2, 'b': 3}]
        assert list(SmartQuery.all(items, 'a==1')) == [{'a': 1, 'b': 2}]
        assert list(SmartQuery.all(items, 'a==2')) == [{'a': 2, 'b': 3}]

    def test_first(self):
        items = [{'a': 1, 'b': 2}, {'a': 2, 'b': 3}]
        assert SmartQuery.first(items, 'a==1') == {'a': 1, 'b': 2}
        assert SmartQuery.first(items, 'a==2') == {'a': 2, 'b': 3}
        assert SmartQuery.first(items, 'a==3') is None

    def test_any(self):
        items = [{'a': 1, 'b': 2}, {'a': 2, 'b': 3}]
        assert SmartQuery.any(items, 'a=1') is True
        assert SmartQuery.any(items, 'a=2') is True
        assert SmartQuery.any(items, 'a=3') is False