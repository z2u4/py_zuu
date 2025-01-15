from functools import cache
import re

class SmartQuery:
    @classmethod
    @cache
    def format(cls, query: str, gck: tuple | None = None):
        # Replace | with or and & with and, but only if they are not within quotes
        query = re.sub(r'(?<!["\'])\|(?!"|\')', ' or ', query)
        query = re.sub(r'(?<!["\'])&(?!"|\')', ' and ', query)
        
        query = query.replace('!', ' not ')

        if gck is None:
            query = re.sub(r'\s+', ' ', query).strip()
            return query

        components = re.split(r'(?m)(?<=\s)(?:and|or|\(|\)|\!|not)(?=\s)', query, flags=re.IGNORECASE)

        for comp in components:
            ocomp = comp
            if comp in ['and', 'or', '(', ')', '!', 'not']:
                continue
            
            # Check for method calls
            if "(" in comp and (match := re.match(r'(\w+)\.\w+\((\w+)\)', comp)):
                field_name, value = match.groups()
                if value not in gck and not value.isdigit():
                    comp = comp.replace(value, f"'{value}'")  # Convert to string if not in gck

            elif "=" in comp:
                if "==" in comp:
                    comp = comp.replace("==", "=")

                key, value = comp.split("=")
                key = key.strip()
                value = value.strip()
                valueAlpha = re.sub(r'[^a-zA-Z]', '', value)

                if valueAlpha in gck or value.isdigit():
                    comp = f"{key} == {value}"  # Keep as is if in gck
                elif ("?" in value or "*" in value):
                    comp = f" re.match(r'{value}', {key}) "  # Convert to regex if not in gck
                else:
                    comp = f" {key} == '{value}' "  # Convert to string

            query = query.replace(ocomp, comp)

        query = re.sub(r'\s+', ' ', query).strip()
        return query
    

    @classmethod
    def gck(cls, items : list, trust : bool = True):
        if trust:
            if isinstance(items, dict):
                return tuple(items.keys())
            else:
                return tuple(item.__dict__.keys() for item in items if not item.startswith('_'))
        
        common_keys = set(items[0].keys())
        for item in items[1:]:
            common_keys &= set(item.keys())
        return tuple(common_keys)

    @classmethod
    def match(cls, item, query : str, ctx = {}, gck : bool = True, gck_trust : bool = True):
        gck_ = cls.gck(item, gck_trust) if gck else None
        query = cls.format(query, gck_)
        if isinstance(item, dict):
            ctx.update(item)
        else:
            ctx.update(item.__dict__)
        
        return eval(query, ctx)
    
    @classmethod
    def all(cls, items, query : str, passList : bool = False):
        

        for item in items:
            ctx = {"re" : re}
            if passList:
                ctx['items'] = items
            if cls.match(item, query, ctx):
                yield item

    @classmethod
    def first(cls, items, query : str, ctx = {}):
        for item in cls.all(items, query, ctx):
            return item
        return None
    
    @classmethod
    def any(cls, items, query : str, ctx = {}):
        return cls.first(items, query, ctx) is not None
