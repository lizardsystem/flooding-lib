from django import template

register = template.Library()


def readable(s):
    try:
        f = float(s)

        units = 0
        while f > 1000 and units <= 3:
            units += 1
            f /= 1000

        return "{0:.1f}{1}".format(f, {
                0: "",
                1: " duizend",
                2: " miljoen",
                3: " miljard"
                }[units])
    except:
        return s


register.filter('readable', readable)
