"""Shared scope policy: senior men; Europe + FIFA World Cup; matches since 2001."""
EUROPE = frozenset('Albania|Andorra|Armenia|Austria|Azerbaijan|Belarus|Belgium|Bosnia and Herzegovina|Bulgaria|Croatia|Cyprus|Czech Republic|Czechia|Denmark|England|Estonia|Faroe Islands|Finland|France|Georgia|Germany|Gibraltar|Greece|Hungary|Iceland|Ireland|Republic of Ireland|Israel|Italy|Kazakhstan|Kosovo|Latvia|Liechtenstein|Lithuania|Luxembourg|Malta|Moldova|Montenegro|Netherlands|North Macedonia|Northern Ireland|Norway|Poland|Portugal|Romania|Russia|San Marino|Scotland|Serbia|Slovakia|Slovenia|Spain|Sweden|Switzerland|Turkey|Ukraine|Wales|Europe'.split('|'))


def in_competition_scope(comp):
    # Country is the provider's competition region, not the host or team country.
    return (comp.get('country_name') in EUROPE or
            comp.get('competition_name') == 'FIFA World Cup')


def eligible_catalogue_entry(comp):
    return (comp.get('competition_gender') == 'male' and
            comp.get('competition_youth') is False and in_competition_scope(comp))


def eligible_match(match):
    return (match['match_date'] >= '2001-01-01' and in_competition_scope(match['competition']) and
            all(match[t].get(f'{t}_gender') == 'male' for t in ['home_team', 'away_team']))
