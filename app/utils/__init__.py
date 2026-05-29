import logging

from django.conf import settings

if not settings.DEBUG:
    dbg_logger = logging.getLogger("django")
else:
    try:
        dbg_logger = logging.getLogger("lumieres.debug")
    except:
        dbg_logger = logging.getLogger("django")
