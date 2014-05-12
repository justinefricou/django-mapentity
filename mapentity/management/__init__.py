from django.db import DEFAULT_DB_ALIAS
from django.contrib.contenttypes.models import ContentType
from django.contrib import auth
from django.contrib.auth.models import Permission
from django.utils.translation import ugettext as _

from mapentity import models as mapentity_models
from mapentity.middleware import get_internal_user, clear_internal_user_cache
from mapentity import logger
from mapentity.signals import post_register

from paperclip import models as paperclip_models


def create_mapentity_models_permissions(sender, **kwargs):
    """ Create `Permission` objects for each model registered
    in MapEntity.

    Could have been implemented a metaclass on `MapEntityMixin`. We chose
    this approach to avoid problems with inheritance of permissions on
    abstract models.

    See:
        * https://code.djangoproject.com/ticket/10686
        * http://stackoverflow.com/a/727956/141895
    """
    db = DEFAULT_DB_ALIAS

    model = kwargs.get('model')

    logger.info("Synchronize migrations of MapEntity models")

    # During tests, the database is flushed so we need to flush caches in order
    # to correctly recreate all permissions
    clear_internal_user_cache()
    ContentType.objects.clear_cache()

    internal_user = get_internal_user()
    perms_manager = Permission.objects.using(db)

    permissions = set()
    for view_kind in mapentity_models.ENTITY_KINDS:
        perm = model.get_entity_kind_permission(view_kind)
        codename = auth.get_permission_codename(perm, model._meta)
        name = "Can %s %s" % (perm, model._meta.verbose_name_raw)
        permissions.add((codename, _(name)))

    ctype = ContentType.objects.db_manager(db).get_for_model(model)
    for (codename, name) in permissions:
        p, created = perms_manager.get_or_create(codename=codename,
                                                 name=name[:50],
                                                 content_type=ctype)
        if created:
            logger.info("Permission '%s' created." % codename)

    for view_kind in (mapentity_models.ENTITY_LIST,
                      mapentity_models.ENTITY_DOCUMENT):
        perm = model.get_entity_kind_permission(view_kind)
        codename = auth.get_permission_codename(perm, model._meta)

        internal_user_permission = internal_user.user_permissions.filter(codename=codename, content_type=ctype)

        if not internal_user_permission.exists():
            permission = perms_manager.get(codename=codename, content_type=ctype)
            internal_user.user_permissions.add(permission)
            logger.info("Added permission %s to internal user %s" % (codename, internal_user))

    attachmenttype = ContentType.objects.db_manager(db).get_for_model(paperclip_models.Attachment)
    read_perm = dict(codename='read_attachment', content_type=attachmenttype)
    if not internal_user.user_permissions.filter(**read_perm).exists():
        permission = perms_manager.get(**read_perm)
        internal_user.user_permissions.add(permission)
        logger.info("Added permission %s to internal user %s" % (permission.codename, internal_user))


post_register.connect(create_mapentity_models_permissions,
                      dispatch_uid="create_mapentity_models_permissions")
