# Source - https://stackoverflow.com/a/16801605
# Posted by Jon Clements, modified by community. See post 'Timeline' for change history
# Retrieved 2026-04-24, License - CC BY-SA 4.0

def count_not_none(iterable):
    """
    Check how many elements are not None
    :param iterable: The iterable to check
    :return bool: True or False
    """
    return iterable.count(None) - len(iterable)
