"""
Internationalization handler.
Deal with making the program aware of multiple languages.

Language codes are in ISO 639-1 standard.
"""
import gettext


LANGUAGES = ("en", "hr")
_ = gettext.gettext

if __name__ == "__main__":
    en = gettext.translation("base", localedir="bot.locales", languages=["en"])
    print(_('Hello!'))
